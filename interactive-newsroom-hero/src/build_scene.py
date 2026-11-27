import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scene_config import A1_ROLE, RenderSpec

SPEC = RenderSpec()
ARGS = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
OUTPUT = Path(ARGS[0]).resolve() if ARGS else ROOT / "output"
FRAMES = OUTPUT / "frames"


def material(name, color, metallic=0.0, roughness=0.62, emission=None):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = 1.6
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


def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.materials:
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
    return scene


def build_scene():
    reset_scene()
    scene = configure_scene()
    base = bpy.data.collections.new("base")
    interactive = bpy.data.collections.new("interactive")
    scene.collection.children.link(base)
    scene.collection.children.link(interactive)

    white = material("porcelain white", (0.92, 0.93, 0.94, 1))
    pale = material("warm white", (0.78, 0.80, 0.82, 1))
    dark = material(
        "screen body", (0.035, 0.045, 0.055, 1), roughness=0.35
    )
    red = material("A1 red", A1_ROLE["color"], roughness=0.48)
    screen = material(
        "topic screen",
        (0.15, 0.52, 0.90, 1),
        emission=(0.12, 0.42, 1.0, 1),
    )

    cube(
        "base.floor",
        (0, 0, -0.18),
        (10.0, 8.0, 0.15),
        white,
        0.22,
        base,
    )
    cube(
        "interactive.desk.top",
        (0, 0.25, 1.45),
        (2.55, 0.95, 0.12),
        white,
        0.10,
        interactive,
    )
    for x in (-2.15, 2.15):
        cube(
            f"interactive.desk.leg.{x}",
            (x, 0.25, 0.68),
            (0.13, 0.70, 0.70),
            pale,
            0.05,
            interactive,
        )
    cube(
        "interactive.drawer",
        (1.82, 0.22, 0.73),
        (0.48, 0.68, 0.63),
        pale,
        0.08,
        interactive,
    )
    cube(
        "interactive.monitor",
        (0, 0.28, 2.55),
        (1.18, 0.12, 0.72),
        dark,
        0.10,
        interactive,
    )
    cube(
        "interactive.screen",
        (0, 0.13, 2.56),
        (1.02, 0.035, 0.56),
        screen,
        0.04,
        interactive,
    )
    cube(
        "interactive.monitor.stand",
        (0, 0.33, 1.83),
        (0.10, 0.10, 0.30),
        dark,
        0.04,
        interactive,
    )
    cube(
        "interactive.keyboard",
        (0, -0.42, 1.63),
        (0.76, 0.25, 0.05),
        pale,
        0.05,
        interactive,
    )

    cube(
        "interactive.chair.back",
        (0, -1.62, 1.13),
        (0.80, 0.14, 0.72),
        pale,
        0.18,
        interactive,
    )
    cube(
        "interactive.chair.seat",
        (0, -1.35, 0.63),
        (0.72, 0.62, 0.12),
        pale,
        0.14,
        interactive,
    )
    cube(
        "interactive.chair.post",
        (0, -1.35, 0.18),
        (0.10, 0.10, 0.42),
        dark,
        0.04,
        interactive,
    )

    torso = uv_sphere(
        "interactive.role.torso",
        (0, -1.16, 1.33),
        (0.64, 0.46, 0.72),
        red,
        interactive,
    )
    head = uv_sphere(
        "interactive.role.head",
        (0, -1.03, 2.20),
        (0.47, 0.43, 0.48),
        white,
        interactive,
    )
    left_arm = cube(
        "interactive.role.arm.left",
        (-0.50, -0.76, 1.38),
        (0.13, 0.48, 0.13),
        red,
        0.12,
        interactive,
    )
    right_arm = cube(
        "interactive.role.arm.right",
        (0.50, -0.76, 1.38),
        (0.13, 0.48, 0.13),
        red,
        0.12,
        interactive,
    )
    left_arm.rotation_euler.x = math.radians(-24)
    right_arm.rotation_euler.x = math.radians(-24)

    camera_data = bpy.data.cameras.new("Camera")
    camera = bpy.data.objects.new("Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.lens = 52
    keyframe(camera, 1, (8.8, -11.8, 9.3))
    look_at(camera, (0, 0, 1.0))
    camera.keyframe_insert("rotation_euler", frame=1)
    keyframe(camera, 20, (7.7, -10.5, 8.2))
    look_at(camera, (0, 0, 1.05))
    camera.keyframe_insert("rotation_euler", frame=20)
    keyframe(camera, 120, (7.7, -10.5, 8.2))
    look_at(camera, (0, 0, 1.05))
    camera.keyframe_insert("rotation_euler", frame=120)

    keyframe(torso, 21, scale=(1.0, 1.0, 1.0))
    keyframe(torso, 70, scale=(1.015, 1.015, 1.035))
    keyframe(torso, 120, scale=(1.0, 1.0, 1.0))
    keyframe(head, 21, rotation=(math.radians(8), 0, 0))
    keyframe(
        head,
        70,
        rotation=(math.radians(2), 0, math.radians(-3)),
    )
    keyframe(head, 120, rotation=(math.radians(8), 0, 0))
    for arm, sign in ((left_arm, -1), (right_arm, 1)):
        keyframe(
            arm,
            21,
            rotation=(math.radians(-24), 0, math.radians(sign * 4)),
        )
        keyframe(
            arm,
            48,
            rotation=(math.radians(-19), 0, math.radians(sign * 2)),
        )
        keyframe(
            arm,
            74,
            rotation=(math.radians(-25), 0, math.radians(sign * 5)),
        )
        keyframe(
            arm,
            98,
            rotation=(math.radians(-20), 0, math.radians(sign * 3)),
        )
        keyframe(
            arm,
            120,
            rotation=(math.radians(-24), 0, math.radians(sign * 4)),
        )

    bpy.ops.object.light_add(type="AREA", location=(-4.8, -4.2, 9.5))
    key = bpy.context.object
    key.name = "Key light"
    key.data.energy = 1150
    key.data.shape = "DISK"
    key.data.size = 5.5
    look_at(key, (0, 0, 1))
    bpy.ops.object.light_add(type="AREA", location=(5.5, 1.0, 6.0))
    fill = bpy.context.object
    fill.name = "Fill light"
    fill.data.energy = 700
    fill.data.size = 4
    look_at(fill, (0, 0, 1.2))

    return scene, base, interactive


def render_outputs(scene, base, interactive):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(FRAMES / "frame_")
    scene.render.film_transparent = False
    bpy.ops.render.render(animation=True)

    scene.frame_set(SPEC.idle_start)
    scene.render.filepath = str(OUTPUT / "sample-cover.png")
    bpy.ops.render.render(write_still=True)

    for obj in base.objects:
        obj.hide_render = True
    scene.render.film_transparent = True
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.frame_set(70)
    scene.render.filepath = str(OUTPUT / "sample-highlight.png")
    bpy.ops.render.render(write_still=True)

    scene.render.film_transparent = False
    for obj in base.objects:
        obj.hide_render = False
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / "sample.blend"))


if __name__ == "__main__":
    render_outputs(*build_scene())
