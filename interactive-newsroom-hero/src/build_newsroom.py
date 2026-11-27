import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
except ImportError:
    bpy = None

from scene_config import DESKS, NEWSROOM_OUTPUT_NAMES, RenderSpec


SPEC = RenderSpec()
ENTRY_WINDOWS = {
    "a2": (2, 8),
    "a5": (2, 8),
    "a1": (7, 13),
    "a4": (7, 13),
    "a3": (12, 18),
    "a6": (12, 18),
}


def entry_window(desk_id):
    return ENTRY_WINDOWS[desk_id]


def parse_frame_selection(value):
    frames = []
    try:
        for token in value.split(","):
            bounds = token.split("-")
            if len(bounds) == 1:
                selected = [int(bounds[0])]
            elif len(bounds) == 2:
                start, end = map(int, bounds)
                if end < start:
                    raise ValueError
                selected = range(start, end + 1)
            else:
                raise ValueError
            frames.extend(selected)
    except (TypeError, ValueError):
        raise ValueError("invalid frame selection") from None
    if (
        not frames
        or len(set(frames)) != len(frames)
        or any(frame < SPEC.frame_start or frame > SPEC.frame_end for frame in frames)
    ):
        raise ValueError("invalid frame selection")
    return tuple(frames)


def role_render_color(desk):
    if desk.id == "a2":
        return (
            1.0,
            0.32,
            0.0,
            desk.color[3],
        )
    return desk.color


def role_emission(desk):
    return (1.0, 0.08, 0.0, 1.0) if desk.id == "a2" else None


def project_quad(projector, corners) -> list[list[int]]:
    points = []
    for corner in corners:
        normalized_x, normalized_y = projector(corner)
        x = round(normalized_x * SPEC.width)
        y = round((1.0 - normalized_y) * SPEC.height)
        if not 0 <= x <= SPEC.width or not 0 <= y <= SPEC.height:
            raise ValueError("projected hit region is outside the 1280x720 canvas")
        points.append([x, y])
    if len(points) != 4:
        raise ValueError("desk hit region must contain exactly four points")
    return points


def material(
    name, color, metallic=0.0, roughness=0.62, emission=None,
    emission_strength=1.6,
):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def cube(name, location, scale, mat, bevel=0.08, collection=None):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel_mod = obj.modifiers.new("Soft edges", "BEVEL")
    bevel_mod.width = bevel
    bevel_mod.segments = 3
    obj.data.materials.append(mat)
    if collection:
        for owner in list(obj.users_collection):
            owner.objects.unlink(obj)
        collection.objects.link(obj)
    return obj


def uv_sphere(name, location, scale, mat, collection):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=32, ring_count=16, location=location
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def cylinder(name, location, radius, depth, mat, collection, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24, radius=radius, depth=depth, location=location,
        rotation=rotation or (0, 0, 0),
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def look_at(obj, target):
    obj.rotation_euler = (
        Vector(target) - obj.location
    ).to_track_quat("-Z", "Y").to_euler()


def keyframe(obj, frame, location=None, rotation=None, scale=None):
    if location is not None:
        obj.location = location
        obj.keyframe_insert("location", frame=frame)
    if rotation is not None:
        obj.rotation_euler = rotation
        obj.keyframe_insert("rotation_euler", frame=frame)
    if scale is not None:
        obj.scale = scale
        obj.keyframe_insert("scale", frame=frame)


def parent_to(obj, parent):
    obj.parent = parent


def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)
    for block in list(bpy.data.materials):
        bpy.data.materials.remove(block)


def configure_scene():
    scene = bpy.context.scene
    scene.frame_start = SPEC.frame_start
    scene.frame_end = SPEC.frame_end
    scene.render.fps = SPEC.fps
    engines = {
        item.identifier
        for item in scene.render.bl_rna.properties["engine"].enum_items
    }
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        if engine in engines:
            scene.render.engine = engine
            break
    else:
        raise RuntimeError("A compatible Eevee render engine is unavailable")
    scene.render.resolution_x = SPEC.width
    scene.render.resolution_y = SPEC.height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.world.use_nodes = True
    world_nodes = scene.world.node_tree.nodes
    world_nodes.clear()
    world_output = world_nodes.new("ShaderNodeOutputWorld")
    scene_background = world_nodes.new("ShaderNodeBackground")
    scene_background.inputs["Color"].default_value = (0.05, 0.05, 0.05, 1.0)
    scene_background.inputs["Strength"].default_value = 1.0
    camera_background = world_nodes.new("ShaderNodeBackground")
    camera_background.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    camera_background.inputs["Strength"].default_value = 3.0
    light_path = world_nodes.new("ShaderNodeLightPath")
    background_mix = world_nodes.new("ShaderNodeMixShader")
    world_links = scene.world.node_tree.links
    world_links.new(light_path.outputs["Is Camera Ray"], background_mix.inputs[0])
    world_links.new(scene_background.outputs["Background"], background_mix.inputs[1])
    world_links.new(camera_background.outputs["Background"], background_mix.inputs[2])
    world_links.new(background_mix.outputs["Shader"], world_output.inputs["Surface"])
    scene.view_settings.look = "AgX - Medium High Contrast"
    compositor = bpy.data.node_groups.new(
        "Newsroom Compositor", "CompositorNodeTree"
    )
    scene.compositing_node_group = compositor
    compositor.interface.new_socket(
        name="Image", in_out="OUTPUT", socket_type="NodeSocketColor"
    )
    render_layers = compositor.nodes.new("CompositorNodeRLayers")
    white = compositor.nodes.new("CompositorNodeRGB")
    white.outputs["Color"].default_value = (16.0, 16.0, 16.0, 1.0)
    fade = compositor.nodes.new("CompositorNodeAlphaOver")
    composite = compositor.nodes.new("NodeGroupOutput")
    compositor.links.new(white.outputs["Color"], fade.inputs["Background"])
    compositor.links.new(render_layers.outputs["Image"], fade.inputs["Foreground"])
    compositor.links.new(fade.outputs["Image"], composite.inputs["Image"])
    fade.inputs["Factor"].default_value = 0.0
    fade.inputs["Factor"].keyframe_insert("default_value", frame=1)
    fade.inputs["Factor"].default_value = 1.0
    fade.inputs["Factor"].keyframe_insert("default_value", frame=6)
    fade.inputs["Factor"].keyframe_insert("default_value", frame=20)
    fade.inputs["Factor"].keyframe_insert("default_value", frame=120)
    return scene


def make_materials():
    return {
        "white": material("porcelain white", (0.92, 0.93, 0.94, 1)),
        "pale": material("warm white", (0.78, 0.80, 0.82, 1)),
        "dark": material(
            "screen body", (0.035, 0.045, 0.055, 1), roughness=0.35
        ),
        "skin": material("role head", (0.94, 0.81, 0.68, 1), roughness=0.58),
        "blue": material(
            "screen blue", (0.15, 0.52, 0.90, 1),
            emission=(0.12, 0.42, 1.0, 1),
        ),
        "paper": material("paper", (0.94, 0.91, 0.82, 1)),
        "magenta": material("marking magenta", (0.86, 0.08, 0.46, 1)),
        "yellow": material("publish yellow", (0.96, 0.72, 0.08, 1)),
        "cyan": material(
            "chart cyan", (0.05, 0.72, 0.78, 1),
            emission=(0.04, 0.62, 0.68, 1),
        ),
    }


def build_role(desk, parent, materials) -> dict[str, object]:
    collection = parent.users_collection[0]
    role_mat = material(
        f"{desk.id} clothing",
        role_render_color(desk),
        roughness=0.48,
        emission=role_emission(desk),
        emission_strength=0.15,
    )
    role_x = 0.55 if desk.id == "a2" else 0
    torso = uv_sphere(
        f"{desk.id}.role.torso", (role_x, -0.78, 1.28),
        (0.64, 0.46, 0.72), role_mat, collection,
    )
    head = uv_sphere(
        f"{desk.id}.role.head", (role_x, -0.68, 2.15),
        (0.47, 0.43, 0.48), materials["skin"], collection,
    )
    left_arm = cube(
        f"{desk.id}.role.arm.left", (role_x - 0.50, -0.38, 1.35),
        (0.13, 0.48, 0.13), role_mat, 0.12, collection,
    )
    right_arm = cube(
        f"{desk.id}.role.arm.right", (role_x + 0.50, -0.38, 1.35),
        (0.13, 0.48, 0.13), role_mat, 0.12, collection,
    )
    left_arm.rotation_euler.x = math.radians(-24)
    right_arm.rotation_euler.x = math.radians(-24)
    for obj in (torso, head, left_arm, right_arm):
        parent_to(obj, parent)
    return {
        "torso": torso,
        "head": head,
        "left_arm": left_arm,
        "right_arm": right_arm,
    }


def build_workstation(desk, parent, materials) -> dict[str, object]:
    collection = parent.users_collection[0]
    objects = []
    monitor_x = -0.38 if desk.id == "a2" else 0
    chair_x = 0.55 if desk.id == "a2" else 0

    def add(obj):
        parent_to(obj, parent)
        objects.append(obj)
        return obj

    desk_top = add(cube(
        f"{desk.id}.desk.top", (0, 0.40, 1.25), (1.45, 0.65, 0.10),
        materials["white"], 0.10, collection,
    ))
    for x in (-1.18, 1.18):
        add(cube(
            f"{desk.id}.desk.leg.{x}", (x, 0.40, 0.64),
            (0.11, 0.48, 0.55), materials["pale"], 0.05, collection,
        ))
    add(cube(
        f"{desk.id}.drawer", (1.02, 0.40, 0.68), (0.32, 0.46, 0.46),
        materials["pale"], 0.07, collection,
    ))
    add(cube(
        f"{desk.id}.monitor", (monitor_x, 0.48, 2.05), (0.68, 0.08, 0.43),
        materials["dark"], 0.08, collection,
    ))
    screen_mat = material(
        f"{desk.id} screen", (0.15, 0.52, 0.90, 1),
        emission=(0.12, 0.42, 1.0, 1),
    )
    screen = add(cube(
        f"{desk.id}.screen", (monitor_x, 0.385, 2.06), (0.57, 0.018, 0.33),
        screen_mat, 0.025, collection,
    ))
    add(cube(
        f"{desk.id}.monitor.stand", (monitor_x, 0.50, 1.58),
        (0.07, 0.07, 0.24),
        materials["dark"], 0.03, collection,
    ))
    keyboard = add(cube(
        f"{desk.id}.keyboard", (0, -0.02, 1.39), (0.48, 0.20, 0.04),
        materials["pale"], 0.04, collection,
    ))
    add(cube(
        f"{desk.id}.chair.back", (chair_x, -1.07, 1.08),
        (0.52, 0.11, 0.55),
        materials["pale"], 0.16, collection,
    ))
    add(cube(
        f"{desk.id}.chair.seat", (chair_x, -0.91, 0.60),
        (0.48, 0.42, 0.10),
        materials["pale"], 0.12, collection,
    ))
    add(cube(
        f"{desk.id}.chair.post", (chair_x, -0.91, 0.26),
        (0.08, 0.08, 0.30),
        materials["dark"], 0.03, collection,
    ))
    return {
        "desk_top": desk_top,
        "screen": screen,
        "screen_material": screen_mat,
        "keyboard": keyboard,
        "objects": objects,
    }


def build_props(desk, parent, materials, workstation) -> dict[str, object]:
    collection = parent.users_collection[0]
    props = {}
    role_color = material(
        f"{desk.id} prop accent", desk.color, emission=tuple(desk.color)
    )

    def add(key, obj):
        parent_to(obj, parent)
        props[key] = obj
        return obj

    if desk.id == "a1":
        add("card", cube(
            "a1.prop.movable_card", (-0.98, 0.55, 1.48),
            (0.40, 0.28, 0.045), materials["yellow"], 0.04, collection,
        ))
        add("trend_screen", cube(
            "a1.prop.trend_screen", (0.55, 0.10, 1.47),
            (0.42, 0.26, 0.035), materials["dark"], 0.04, collection,
        ))
        for index, height in enumerate((0.08, 0.15, 0.23)):
            add(f"trend_bar_{index}", cube(
                f"a1.prop.trend_bar.{index}",
                (0.32 + index * 0.22, 0.05, 1.515),
                (0.065, height, 0.018), materials["blue"], 0.015, collection,
            ))
    elif desk.id == "a2":
        add("headband", cylinder(
            "a2.prop.headband", (0.55, -0.68, 2.39), 0.32, 0.07,
            materials["dark"], collection, rotation=(math.pi / 2, 0, 0),
        ))
        for x in (-0.43, 0.43):
            add(f"ear_cup_{x}", cylinder(
                f"a2.prop.ear_cup.{x}", (0.55 + x, -0.68, 2.15), 0.16, 0.10,
                materials["dark"], collection, rotation=(0, math.pi / 2, 0),
            ))
        add("folder", cube(
            "a2.prop.material_folder", (0.80, 0.18, 1.48),
            (0.40, 0.27, 0.045), role_color, 0.035, collection,
        ))
        add("folder_sheet", cube(
            "a2.prop.folder_sheet", (0.84, 0.22, 1.535),
            (0.30, 0.19, 0.018), materials["paper"], 0.015, collection,
        ))
    elif desk.id == "a3":
        for row in range(2):
            for column in range(5):
                add(f"key_{row}_{column}", cube(
                    f"a3.prop.key.{row}.{column}",
                    (-0.32 + column * 0.16, -0.10 + row * 0.14, 1.45),
                    (0.055, 0.045, 0.018), materials["dark"], 0.01, collection,
                ))
        add("manuscript", cube(
            "a3.prop.manuscript", (-0.88, 0.55, 1.48),
            (0.39, 0.27, 0.035), materials["dark"], 0.025, collection,
        ))
        add("manuscript_sheet", cube(
            "a3.prop.manuscript_sheet", (-0.88, 0.55, 1.525),
            (0.34, 0.22, 0.015), materials["paper"], 0.01, collection,
        ))
        for index, width in enumerate((0.24, 0.28, 0.20)):
            add(f"manuscript_line_{index}", cube(
                f"a3.prop.manuscript_line.{index}",
                (-0.92, 0.43 + index * 0.11, 1.548),
                (width, 0.022, 0.008), role_color, 0.006, collection,
            ))
    elif desk.id == "a4":
        add("pen", cylinder(
            "a4.prop.marking_pen", (-0.48, -0.05, 1.48), 0.045, 0.48,
            materials["magenta"], collection,
            rotation=(0, math.radians(68), math.radians(8)),
        ))
        add("badge", cylinder(
            "a4.prop.issue_badge", (-0.82, 0.12, 1.50), 0.26, 0.07,
            materials["magenta"], collection,
        ))
        check_left = add("badge_check_left", cube(
            "a4.prop.badge_check.left", (-0.88, 0.10, 1.545),
            (0.035, 0.10, 0.015), materials["paper"], 0.01, collection,
        ))
        check_left.rotation_euler.z = math.radians(-35)
        check_right = add("badge_check_right", cube(
            "a4.prop.badge_check.right", (-0.76, 0.16, 1.545),
            (0.035, 0.16, 0.015), materials["paper"], 0.01, collection,
        ))
        check_right.rotation_euler.z = math.radians(48)
    elif desk.id == "a5":
        for x in (-0.93, 0.93):
            add(f"side_screen_{x}", cube(
                f"a5.prop.side_monitor.{x}", (x, 0.28, 1.82),
                (0.31, 0.055, 0.36), materials["dark"], 0.04, collection,
            ))
            add(f"channel_tile_{x}", cube(
                f"a5.prop.channel_tile.{x}", (x, 0.215, 1.82),
                (0.24, 0.018, 0.27),
                materials["yellow"] if x < 0 else materials["blue"],
                0.025, collection,
            ))
        add("publish_key", cube(
            "a5.prop.publish_key", (0.62, -0.04, 1.44),
            (0.15, 0.15, 0.055), materials["yellow"], 0.05, collection,
        ))
    elif desk.id == "a6":
        for index, height in enumerate((0.18, 0.31, 0.45)):
            add(f"chart_{index}", cube(
                f"a6.prop.chart_bar.{index}",
                (-0.62 + index * 0.27, 0.03, 1.50 + height),
                (0.09, 0.09, height), materials["cyan"], 0.025, collection,
            ))
        for index, x in enumerate((0.45, 0.72, 0.99)):
            add(f"signal_{index}", cylinder(
                f"a6.prop.signal_post.{index}",
                (x, 0.03, 1.54 + index * 0.04),
                0.085, 0.30 + index * 0.08, role_color, collection,
            ))
    return props


def add_response_motif(desk, parent, materials):
    collection = parent.users_collection[0]
    motif = []
    color = material(
        f"{desk.id} motif", desk.color, emission=tuple(desk.color)
    )
    center = Vector((0, 0.38, 2.74))
    parent_rotation = parent.rotation_euler.to_quaternion()
    world_center = Vector(parent.location) + parent_rotation @ center
    world_rotation = (
        Vector((13.6, -17.6, 13.9)) - world_center
    ).to_track_quat("Z", "Y")
    local_rotation = parent_rotation.inverted() @ world_rotation
    right = local_rotation @ Vector((1, 0, 0))
    up = local_rotation @ Vector((0, 1, 0))
    normal = local_rotation @ Vector((0, 0, 1))

    def display_cube(name, offset, scale, mat, bevel=0.015):
        location = (
            center + right * offset[0] + up * offset[1] + normal * offset[2]
        )
        obj = cube(name, location, scale, mat, bevel, collection)
        parent_to(obj, parent)
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = local_rotation
        motif.append(obj)
        return obj

    display_cube(
        f"{desk.id}.motif.response_panel", (0, 0, 0),
        (0.62, 0.38, 0.04), materials["dark"], 0.05,
    )
    if desk.id in {"a1", "a6"}:
        heights = (0.10, 0.18, 0.29, 0.23)
        for index, height in enumerate(heights):
            display_cube(
                f"{desk.id}.motif.bar.{index}",
                (-0.36 + index * 0.24, -0.27 + height, 0.055),
                (0.075, height, 0.018), color,
            )
    elif desk.id == "a2":
        for index, height in enumerate((0.10, 0.22, 0.32, 0.22, 0.10)):
            display_cube(
                f"a2.motif.wave.{index}",
                (-0.38 + index * 0.19, 0, 0.055),
                (0.055, height, 0.018), color,
            )
    elif desk.id == "a3":
        for index, width in enumerate((0.45, 0.36, 0.42, 0.29)):
            display_cube(
                f"a3.motif.line.{index}",
                (-0.05, 0.24 - index * 0.16, 0.055),
                (width, 0.035, 0.018), color,
            )
    elif desk.id == "a4":
        display_cube(
            "a4.motif.marked_issue", (0, 0, 0.055),
            (0.38, 0.25, 0.018), materials["magenta"], 0.03,
        )
        display_cube(
            "a4.motif.issue_mark", (0, 0.06, 0.08),
            (0.055, 0.15, 0.018), materials["paper"],
        )
        display_cube(
            "a4.motif.issue_dot", (0, -0.22, 0.08),
            (0.055, 0.055, 0.018), materials["paper"],
        )
    elif desk.id == "a5":
        for row in range(2):
            for column in range(2):
                display_cube(
                    f"a5.motif.tile.{row}.{column}",
                    (-0.27 + column * 0.54, -0.17 + row * 0.34, 0.055),
                    (0.20, 0.11, 0.018),
                    materials["yellow"] if (row + column) % 2 else color,
                    0.02,
                )
    for obj in motif:
        parent_to(obj, parent)
        keyframe(obj, 21, scale=(0.001, 0.001, 0.001))
        keyframe(obj, 69, scale=(0.001, 0.001, 0.001))
        keyframe(obj, 70, scale=(1.0, 1.0, 1.0))
        keyframe(obj, 71, scale=(0.001, 0.001, 0.001))
        keyframe(obj, 120, scale=(0.001, 0.001, 0.001))
    return motif


def animate_desk(desk, root, role, workstation, props):
    start, end = entry_window(desk.id)
    root.scale = (0.001, 0.001, 0.001)
    keyframe(root, 1, scale=(0.001, 0.001, 0.001))
    keyframe(root, start, scale=(0.001, 0.001, 0.001))
    keyframe(root, end, scale=(1.0, 1.0, 1.0))
    keyframe(root, 20, scale=(1.0, 1.0, 1.0))
    keyframe(root, 120, scale=(1.0, 1.0, 1.0))

    torso = role["torso"]
    keyframe(torso, 21, scale=(1.0, 1.0, 1.0))
    keyframe(torso, 45, scale=(1.01, 1.01, 1.025))
    keyframe(torso, 70, scale=(1.015, 1.015, 1.035))
    keyframe(torso, 95, scale=(1.01, 1.01, 1.025))
    keyframe(torso, 120, scale=(1.0, 1.0, 1.0))

    head = role["head"]
    left_arm = role["left_arm"]
    right_arm = role["right_arm"]
    neutral_head = (math.radians(8), 0, 0)
    keyframe(head, 21, rotation=neutral_head)
    keyframe(head, 120, rotation=neutral_head)
    for arm, sign in ((left_arm, -1), (right_arm, 1)):
        neutral = (math.radians(-24), 0, math.radians(sign * 4))
        keyframe(arm, 21, rotation=neutral)
        keyframe(arm, 120, rotation=neutral)

    if desk.id == "a1":
        card = props["card"]
        keyframe(card, 21, location=(-0.98, 0.55, 1.48))
        keyframe(card, 70, location=(-0.86, 0.55, 1.48))
        keyframe(card, 120, location=(-0.98, 0.55, 1.48))
        keyframe(head, 70, rotation=(math.radians(5), 0, math.radians(-3)))
    elif desk.id == "a2":
        folder = props["folder"]
        folder_sheet = props["folder_sheet"]
        keyframe(folder, 21, location=(0.80, 0.18, 1.48))
        keyframe(folder, 70, location=(0.92, 0.12, 1.51))
        keyframe(folder, 120, location=(0.80, 0.18, 1.48))
        keyframe(folder_sheet, 21, location=(0.84, 0.22, 1.535))
        keyframe(folder_sheet, 70, location=(0.96, 0.16, 1.565))
        keyframe(folder_sheet, 120, location=(0.84, 0.22, 1.535))
        keyframe(head, 70, rotation=(math.radians(8), 0, math.radians(4)))
    elif desk.id == "a3":
        keyframe(left_arm, 48, rotation=(math.radians(-18), 0, math.radians(-2)))
        keyframe(right_arm, 48, rotation=(math.radians(-27), 0, math.radians(6)))
        keyframe(left_arm, 70, rotation=(math.radians(-27), 0, math.radians(-6)))
        keyframe(right_arm, 70, rotation=(math.radians(-18), 0, math.radians(2)))
        keyframe(left_arm, 96, rotation=(math.radians(-18), 0, math.radians(-2)))
        keyframe(right_arm, 96, rotation=(math.radians(-27), 0, math.radians(6)))
    elif desk.id == "a4":
        pen = props["pen"]
        keyframe(pen, 21, location=(-0.48, -0.05, 1.48))
        keyframe(pen, 70, location=(-0.36, -0.11, 1.52))
        keyframe(pen, 120, location=(-0.48, -0.05, 1.48))
        keyframe(head, 70, rotation=(math.radians(12), 0, 0))
    elif desk.id == "a5":
        keyframe(head, 21, rotation=(math.radians(8), 0, math.radians(-5)))
        keyframe(head, 70, rotation=(math.radians(8), 0, math.radians(5)))
        keyframe(head, 120, rotation=(math.radians(8), 0, math.radians(-5)))
    elif desk.id == "a6":
        keyframe(head, 70, rotation=(math.radians(12), 0, math.radians(-3)))

    bsdf = workstation["screen_material"].node_tree.nodes.get("Principled BSDF")
    emission = bsdf.inputs["Emission Strength"]
    emission.default_value = 1.6
    emission.keyframe_insert("default_value", frame=21)
    emission.default_value = 1.8
    emission.keyframe_insert("default_value", frame=70)
    emission.default_value = 1.6
    emission.keyframe_insert("default_value", frame=120)


def build_scene():
    reset_scene()
    scene = configure_scene()
    materials = make_materials()
    base = bpy.data.collections.new("base")
    scene.collection.children.link(base)
    cube(
        "base.floor", (0, 0, -0.18), (13.0, 10.0, 0.15),
        materials["white"], 0.22, base,
    )

    desks = {}
    for desk in DESKS:
        collection = bpy.data.collections.new(f"desk_{desk.id}")
        scene.collection.children.link(collection)
        root = bpy.data.objects.new(f"{desk.id}.root", None)
        collection.objects.link(root)
        root.location = desk.location
        root.rotation_euler.z = math.radians(desk.rotation_degrees)
        workstation = build_workstation(desk, root, materials)
        role = build_role(desk, root, materials)
        props = build_props(desk, root, materials, workstation)
        motif = add_response_motif(desk, root, materials)
        animate_desk(desk, root, role, workstation, props)
        desks[desk.id] = {
            "spec": desk,
            "collection": collection,
            "root": root,
            "workstation": workstation,
            "role": role,
            "props": props,
            "motif": motif,
        }

    camera_data = bpy.data.cameras.new("Camera")
    camera = bpy.data.objects.new("Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.lens = 52
    keyframe(camera, 1, (15.0, -19.4, 15.3))
    look_at(camera, (0, 0, 1.0))
    camera.keyframe_insert("rotation_euler", frame=1)
    keyframe(camera, 20, (13.6, -17.6, 13.9))
    look_at(camera, (0, 0, 1.0))
    camera.keyframe_insert("rotation_euler", frame=20)
    keyframe(camera, 120, (13.6, -17.6, 13.9))
    look_at(camera, (0, 0, 1.0))
    camera.keyframe_insert("rotation_euler", frame=120)

    bpy.ops.object.light_add(type="AREA", location=(-4.8, -4.2, 9.5))
    key = bpy.context.object
    key.name = "Key light"
    key.data.energy = 1800
    key.data.shape = "DISK"
    key.data.size = 8.0
    look_at(key, (0, 0, 1))
    bpy.ops.object.light_add(type="AREA", location=(5.5, 1.0, 6.0))
    fill = bpy.context.object
    fill.name = "Fill light"
    fill.data.energy = 1050
    fill.data.size = 6.0
    look_at(fill, (0, 0, 1.2))
    return scene, base, desks, camera, materials


def render_still(scene, path, frame):
    path.parent.mkdir(parents=True, exist_ok=True)
    scene.frame_set(frame)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def desktop_corners(desk_top):
    bounds = [Vector(corner) for corner in desk_top.bound_box]
    minimum_x = min(corner.x for corner in bounds)
    maximum_x = max(corner.x for corner in bounds)
    minimum_y = min(corner.y for corner in bounds)
    maximum_y = max(corner.y for corner in bounds)
    top_z = max(corner.z for corner in bounds)
    local = (
        (minimum_x, minimum_y, top_z),
        (maximum_x, minimum_y, top_z),
        (maximum_x, maximum_y, top_z),
        (minimum_x, maximum_y, top_z),
    )
    return [desk_top.matrix_world @ Vector(corner) for corner in local]


def write_hit_regions(scene, camera, desks, output):
    scene.frame_set(SPEC.idle_start)
    bpy.context.view_layer.update()
    regions = {}
    for desk_id, built in desks.items():
        corners = desktop_corners(built["workstation"]["desk_top"])
        regions[desk_id] = project_quad(
            lambda corner: world_to_camera_view(scene, camera, corner)[:2],
            corners,
        )
    payload = {"viewBox": [0, 0, SPEC.width, SPEC.height], "regions": regions}
    path = output / NEWSROOM_OUTPUT_NAMES["hit_regions"]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def add_highlight_ring(desk, built, materials):
    collection = built["collection"]
    bpy.ops.mesh.primitive_torus_add(
        major_radius=1.45, minor_radius=0.055,
        major_segments=64, minor_segments=12,
        location=(0, 0.15, 0.03),
    )
    ring = bpy.context.object
    ring.name = f"{desk.id}.highlight.ring"
    ring.scale.y = 0.62
    ring.data.materials.append(material(
        f"{desk.id} ring", desk.color, emission=tuple(desk.color)
    ))
    for owner in list(ring.users_collection):
        owner.objects.unlink(ring)
    collection.objects.link(ring)
    parent_to(ring, built["root"])
    ring.hide_render = True
    return ring


def set_response_motif_visibility(desks, selected_id=None):
    for desk_id, built in desks.items():
        visible = desk_id == selected_id
        for motif_object in built["motif"]:
            motif_object.hide_render = not visible


def render_highlights(scene, base, desks, materials, output):
    rings = {
        desk.id: add_highlight_ring(desk, desks[desk.id], materials)
        for desk in DESKS
    }
    scene.frame_set(70)
    scene.render.film_transparent = True
    compositor = scene.compositing_node_group
    scene.compositing_node_group = None
    base.hide_render = True
    for selected in DESKS:
        for desk_id, built in desks.items():
            built["collection"].hide_render = desk_id != selected.id
        set_response_motif_visibility(desks, selected.id)
        rings[selected.id].hide_render = False
        render_still(
            scene,
            output / NEWSROOM_OUTPUT_NAMES["highlights"][selected.id],
            70,
        )
        rings[selected.id].hide_render = True
    base.hide_render = False
    for built in desks.values():
        built["collection"].hide_render = False
    set_response_motif_visibility(desks)
    scene.render.film_transparent = False
    scene.compositing_node_group = compositor


def render_outputs(
    scene, base, desks, camera, materials, output, mode, repair_frames=(),
    regenerate_artifacts=False,
):
    output.mkdir(parents=True, exist_ok=True)
    scene.render.film_transparent = False
    set_response_motif_visibility(desks)
    if mode == "artifacts":
        render_still(
            scene, output / NEWSROOM_OUTPUT_NAMES["cover"], SPEC.idle_start
        )
        render_highlights(scene, base, desks, materials, output)
        write_hit_regions(scene, camera, desks, output)
        bpy.ops.wm.save_as_mainfile(
            filepath=str(output / NEWSROOM_OUTPUT_NAMES["blend"])
        )
        print("NEWSROOM_ARTIFACT_REPAIR_COMPLETE")
        return
    if mode == "repair":
        frame_dir = output / "newsroom-frames"
        for frame in repair_frames:
            render_still(scene, frame_dir / f"frame_{frame:04d}.png", frame)
        if regenerate_artifacts:
            render_still(
                scene, output / NEWSROOM_OUTPUT_NAMES["cover"], SPEC.idle_start
            )
            render_highlights(scene, base, desks, materials, output)
            write_hit_regions(scene, camera, desks, output)
        bpy.ops.wm.save_as_mainfile(
            filepath=str(output / NEWSROOM_OUTPUT_NAMES["blend"])
        )
        print(
            "NEWSROOM_REPAIR_COMPLETE "
            + ",".join(str(frame) for frame in repair_frames)
        )
        return
    if mode == "preview":
        frame_dir = output / "newsroom-preview"
        frames = (1, 21, 70, 120)
    else:
        frame_dir = output / "newsroom-frames"
        frames = range(SPEC.frame_start, SPEC.frame_end + 1)
    for frame in frames:
        render_still(scene, frame_dir / f"frame_{frame:04d}.png", frame)

    render_still(
        scene, output / NEWSROOM_OUTPUT_NAMES["cover"], SPEC.idle_start
    )
    render_highlights(scene, base, desks, materials, output)
    write_hit_regions(scene, camera, desks, output)
    bpy.ops.wm.save_as_mainfile(
        filepath=str(output / NEWSROOM_OUTPUT_NAMES["blend"])
    )


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "output_dir", nargs="?", type=Path, default=ROOT / "output"
    )
    parser.add_argument(
        "--mode",
        choices=("preview", "full", "repair", "artifacts"),
        default="preview",
    )
    parser.add_argument("--frames")
    parser.add_argument("--regenerate-artifacts", action="store_true")
    return parser.parse_args(argv)


def main():
    if bpy is None:
        raise RuntimeError("This scene builder must run inside Blender")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parse_args(argv)
    if args.mode == "repair" and not args.frames:
        raise ValueError("repair mode requires --frames")
    if args.mode != "repair" and args.frames:
        raise ValueError("--frames is only valid in repair mode")
    if args.mode != "repair" and args.regenerate_artifacts:
        raise ValueError("--regenerate-artifacts is only valid in repair mode")
    repair_frames = parse_frame_selection(args.frames) if args.frames else ()
    render_outputs(
        *build_scene(),
        args.output_dir.resolve(),
        args.mode,
        repair_frames,
        args.regenerate_artifacts,
    )


if __name__ == "__main__":
    main()
