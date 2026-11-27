# Six-Desk Interactive Newsroom Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the approved A1 one-desk proof into a complete A1–A6 interactive newsroom with an original six-desk render, six perspective-aligned hit regions, six independent transparent highlights, accessible interaction, and navigation to the six existing demo pages.

**Architecture:** Keep the approved sample pipeline and its generated assets unchanged. Add a parallel, data-driven full-scene pipeline: Python owns the render contract and desk metadata, Blender 5.2 builds the irregular-ring miniature scene and exports camera-projected hit polygons, a generator emits the matching JavaScript configuration, and the browser renders links, highlights, and cards from that configuration. Automated Python media/config tests and an Edge DevTools smoke test verify the full artifact while preserving the one-desk regression suite.

**Tech Stack:** Blender 5.2.0 LTS Python API and Eevee, Python 3.11 standard library, Pillow, FFmpeg/FFprobe 8.1.1, PowerShell, HTML5 video, SVG, CSS, vanilla JavaScript, Node.js 24, Microsoft Edge DevTools Protocol.

## Global Constraints

- Preserve the approved unified rounded role shape, white miniature lighting, visible contact shadows, 52 mm perspective camera language, restrained motion, and interaction quality.
- Keep `output/sample.*`, `output/frames/`, `web/assets/sample.*`, `src/build_scene.py`, and `scripts/render-sample.ps1` available as the approved one-desk baseline; the six-desk pipeline uses new `newsroom-*` names and `output/newsroom-frames/`.
- Build an original scene from Blender primitives. Do not copy Marvis or any third-party character outline, layout, camera, color treatment, model, animation, video, or page source.
- Use six instances of one role shape; distinguish roles only through clothing color, action, screen content, and desk props.
- Use the exact A1–A6 names, roles, actions, and destination files listed in the approved design and in Task 1.
- Render the complete scene at 1280×720, 24 fps, frames 1–120, for exactly 5.0 seconds.
- Keep camera entry motion in frames 1–20 and a loop-compatible idle section in frames 21–120; frame 21 and frame 120 must use matching camera, role, and screen states.
- Start hover feedback in 100 ms or less. Keep all six roles visible while dimming non-selected desks.
- Keep click confirmation and navigation at or below 500 ms; reduced-motion users navigate without animated delay.
- Desktop uses hover/focus plus click; touch uses first tap to select and second tap to navigate; keyboard uses Tab, Enter, and Escape.
- Reduced-motion mode pauses and hides the main video, suppresses role/camera transitions, and retains immediate selection and navigation.
- Low-performance mode uses the static cover and CSS/SVG selection ring without requesting transparent highlight images.
- A failed main video falls back to the static cover. A failed individual highlight falls back to the SVG/CSS selection ring. Either failure must leave all six native links usable.
- Check target existence before scripted navigation; a missing page leaves the user in the scene and announces `目标页面暂不可用，请稍后重试。`.
- Do not initialize Git and do not add commit steps. Verification commands are the task gates.
- Blender 5.2 emits `World.use_nodes` and `Material.use_nodes` deprecation warnings for Blender 6; these warnings are accepted for this tested 5.2 implementation and are not a reason to change the approved lighting path.

---

## File Map

- `src/scene_config.py` — retains the sample contract and adds immutable A1–A6 metadata, placement, output names, and validation.
- `src/build_scene.py` — remains the approved one-desk renderer.
- `src/build_newsroom.py` — builds, animates, and renders the complete scene; exports camera-projected desk polygons.
- `src/export_web_config.py` — combines Python desk metadata with projected polygons and writes `web/scene-data.js`.
- `src/verify_outputs.py` — retains sample verification and adds complete-scene video, color, highlight, polygon, and asset-sync verification.
- `scripts/render-sample.ps1` — remains the approved sample command.
- `scripts/render-newsroom.ps1` — provides preview, full render, encode, config generation, verification, and asset synchronization.
- `tests/test_scene_config.py` — adds exact six-role/config contract tests without removing sample tests.
- `tests/test_newsroom_geometry.py` — tests desk layout separation and projected polygon rules without launching Blender.
- `tests/test_verify_outputs.py` — adds full-scene verifier unit tests.
- `tests/test_web_contract.py` — checks six-link/config/asset references and destination existence.
- `web/index.html` — becomes the complete scene shell with native A1–A6 SVG links and one reusable accessible card.
- `web/scene-data.js` — generated, checked-in browser configuration with role copy, colors, projected hit polygons, highlight paths, and destinations.
- `web/styles.css` — complete-scene sizing, dim/highlight/card states, focus, touch, reduced-motion, low-performance, and fallback styling.
- `web/app.js` — data-driven pointer, touch, keyboard, media, asset-failure, and guarded navigation controller.
- `.superpowers/sdd/six-desk-browser-smoke.mjs` — end-to-end Edge test across all desks and degradation modes.
- `output/newsroom-frames/` — disposable 120-frame full-scene PNG sequence.
- `output/newsroom-preview/` — inexpensive representative frames used before the full render.
- `output/newsroom.mp4`, `output/newsroom-cover.png`, `output/newsroom-a1-highlight.png` through `output/newsroom-a6-highlight.png`, `output/newsroom-hit-regions.json`, and `output/newsroom.blend` — full-scene outputs.
- `web/assets/newsroom.*` and `web/assets/newsroom-a1-highlight.png` through `newsroom-a6-highlight.png` — synchronized browser assets; existing `sample.*` files remain untouched.
- `README.md` — documents both pipelines, render cost controls, checks, preview URL, and manual acceptance.

### Task 1: Lock the Six-Desk Data Contract

**Files:**
- Modify: `src/scene_config.py`
- Modify: `tests/test_scene_config.py`

**Interfaces:**
- Preserves: `RenderSpec`, `A1_ROLE`, `OUTPUT_NAMES`, and `rgba_hex(color) -> str`.
- Produces: `DeskSpec`, `DESKS`, `NEWSROOM_OUTPUT_NAMES`, `HIT_REGION_NAME`, and `validate_desks(desks) -> list[str]`.
- `DeskSpec` fields are `id`, `module`, `title`, `english`, `role`, `responsibility`, `color`, `action`, `props`, `destination`, `location`, `rotation_degrees`, and `card_side`.
- Desk IDs are lowercase `a1` through `a6`; generated Blender collections use `desk_a1` through `desk_a6`; DOM IDs use `desk-link-a1` through `desk-link-a6`.

- [ ] **Step 1: Add failing tests for the exact six-desk contract**

Append these tests to `RenderSpecTests`:

```python
from scene_config import DESKS, NEWSROOM_OUTPUT_NAMES, validate_desks

EXPECTED = [
    ("a1", "A1 智能选题", "策划编辑", "#c8102eff",
     "../../demo/pages/m1-topics.html"),
    ("a2", "A2 智能采集", "记者", "#e87524ff",
     "../../demo/pages/m2-collection.html"),
    ("a3", "A3 智能写作", "文字编辑", "#2d8c5aff",
     "../../demo/pages/m3-writing.html"),
    ("a4", "A4 智能审校", "审校编辑", "#a83274ff",
     "../../demo/pages/m4-review.html"),
    ("a5", "A5 全渠道分发", "运营编辑", "#d4a514ff",
     "../../demo/pages/m5-channels.html"),
    ("a6", "A6 效果洞察", "数据分析师", "#1596a5ff",
     "../../demo/pages/m6-insights.html"),
]

def test_six_desk_contract(self):
    actual = [
        (desk.id, desk.module, desk.role, rgba_hex(desk.color), desk.destination)
        for desk in DESKS
    ]
    self.assertEqual(actual, EXPECTED)
    self.assertEqual(validate_desks(DESKS), [])

def test_each_desk_has_role_specific_action_and_props(self):
    self.assertEqual(
        [desk.action for desk in DESKS],
        [
            "查看热点屏、移动选题卡",
            "戴耳机、整理采访素材",
            "敲键盘、查看稿件",
            "标记文本、确认问题",
            "切换多块平台屏幕",
            "查看图表和传播信号",
        ],
    )
    self.assertTrue(all(len(desk.props) >= 2 for desk in DESKS))

def test_newsroom_outputs_do_not_replace_sample_outputs(self):
    self.assertEqual(OUTPUT_NAMES["video"], "sample.mp4")
    self.assertEqual(NEWSROOM_OUTPUT_NAMES["video"], "newsroom.mp4")
    self.assertEqual(
        NEWSROOM_OUTPUT_NAMES["highlights"],
        {desk.id: f"newsroom-{desk.id}-highlight.png" for desk in DESKS},
    )
```

- [ ] **Step 2: Run the focused contract tests and observe the expected failure**

Run:

```powershell
python -m unittest tests.test_scene_config -v
```

Expected: the existing four tests pass and the new tests fail with `ImportError` for `DESKS`.

- [ ] **Step 3: Add the immutable role, placement, and output definitions**

Add this public contract to `src/scene_config.py` while retaining the existing sample constants:

```python
from dataclasses import dataclass

Color = tuple[float, float, float, float]
Point3D = tuple[float, float, float]

@dataclass(frozen=True)
class DeskSpec:
    id: str
    module: str
    title: str
    english: str
    role: str
    responsibility: str
    color: Color
    action: str
    props: tuple[str, ...]
    destination: str
    location: Point3D
    rotation_degrees: float
    card_side: str

DESKS = (
    DeskSpec(
        "a1", "A1 智能选题", "智能选题", "TOPIC PLANNING", "策划编辑",
        "聚合热点信号，形成可执行的报道方向。",
        (0.784, 0.063, 0.180, 1.0), "查看热点屏、移动选题卡",
        ("热点趋势屏", "选题卡"), "../../demo/pages/m1-topics.html",
        (-4.7, -0.6, 0.0), -72.0, "right",
    ),
    DeskSpec(
        "a2", "A2 智能采集", "智能采集", "SMART COLLECTION", "记者",
        "汇集现场采访、音视频与公开信源，整理可用素材。",
        (0.910, 0.459, 0.141, 1.0), "戴耳机、整理采访素材",
        ("耳机", "采访素材夹"), "../../demo/pages/m2-collection.html",
        (-2.8, 3.7, 0.0), -144.0, "right",
    ),
    DeskSpec(
        "a3", "A3 智能写作", "智能写作", "ASSISTED WRITING", "文字编辑",
        "组织事实与结构，协同生成并打磨新闻稿件。",
        (0.176, 0.549, 0.353, 1.0), "敲键盘、查看稿件",
        ("键盘", "稿件屏"), "../../demo/pages/m3-writing.html",
        (1.6, 4.2, 0.0), 156.0, "left",
    ),
    DeskSpec(
        "a4", "A4 智能审校", "智能审校", "SMART REVIEW", "审校编辑",
        "检查事实、语言与规范问题，确认修订结果。",
        (0.659, 0.196, 0.455, 1.0), "标记文本、确认问题",
        ("批注笔", "问题确认屏"), "../../demo/pages/m4-review.html",
        (5.0, 1.2, 0.0), 96.0, "left",
    ),
    DeskSpec(
        "a5", "A5 全渠道分发", "全渠道分发", "OMNICHANNEL DELIVERY", "运营编辑",
        "适配不同平台形态，编排并发布全渠道内容。",
        (0.831, 0.647, 0.078, 1.0), "切换多块平台屏幕",
        ("平台副屏", "发布控制键"), "../../demo/pages/m5-channels.html",
        (3.4, -3.4, 0.0), 30.0, "left",
    ),
    DeskSpec(
        "a6", "A6 效果洞察", "效果洞察", "IMPACT INSIGHTS", "数据分析师",
        "观察传播表现与受众反馈，提炼下一轮优化信号。",
        (0.082, 0.588, 0.647, 1.0), "查看图表和传播信号",
        ("图表屏", "传播信号柱"), "../../demo/pages/m6-insights.html",
        (-1.3, -4.2, 0.0), -12.0, "right",
    ),
)

HIT_REGION_NAME = "newsroom-hit-regions.json"
NEWSROOM_OUTPUT_NAMES = {
    "video": "newsroom.mp4",
    "cover": "newsroom-cover.png",
    "blend": "newsroom.blend",
    "hit_regions": HIT_REGION_NAME,
    "highlights": {
        desk.id: f"newsroom-{desk.id}-highlight.png" for desk in DESKS
    },
}

def validate_desks(desks: tuple[DeskSpec, ...]) -> list[str]:
    errors: list[str] = []
    if [desk.id for desk in desks] != [f"a{index}" for index in range(1, 7)]:
        errors.append("desk ids must be ordered a1 through a6")
    if len({desk.color for desk in desks}) != 6:
        errors.append("desk clothing colors must be unique")
    if len({desk.destination for desk in desks}) != 6:
        errors.append("desk destinations must be unique")
    if any(desk.card_side not in {"left", "right"} for desk in desks):
        errors.append("card_side must be left or right")
    if any(len(desk.props) < 2 for desk in desks):
        errors.append("each desk must define at least two role props")
    return errors
```

- [ ] **Step 4: Run the contract suite**

Run:

```powershell
python -m unittest tests.test_scene_config -v
```

Expected: seven tests pass, including the original sample assertions.

### Task 2: Build the Original Six-Desk Scene and Camera Projection

**Files:**
- Create: `src/build_newsroom.py`
- Create: `tests/test_newsroom_geometry.py`

**Interfaces:**
- Consumes: `DESKS`, `RenderSpec`, and `NEWSROOM_OUTPUT_NAMES`.
- CLI: `blender.exe --background --python src/build_newsroom.py -- <output-dir> --mode preview|full`.
- Preview produces `output/newsroom-preview/frame_0001.png`, `frame_0021.png`, `frame_0070.png`, `frame_0120.png`, the cover, six highlights, hit-region JSON, and Blend source without rendering all animation frames.
- Full produces `output/newsroom-frames/frame_0001.png` through `frame_0120.png`, cover, six highlights, hit-region JSON, and Blend source.
- `project_quad(projector, corners) -> list[list[int]]` is renderer-independent and rounds four projected pixel coordinates.
- Hit-region JSON shape is `{"viewBox":[0,0,1280,720],"regions":{"a1":[[x,y],...],...}}`.

- [ ] **Step 1: Write failing pure-Python geometry tests**

Create `tests/test_newsroom_geometry.py`:

```python
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from build_newsroom import project_quad

class NewsroomGeometryTests(unittest.TestCase):
    def test_project_quad_rounds_four_camera_points(self):
        projected = iter(((0.25, 0.75), (0.50, 0.75), (0.55, 0.40), (0.20, 0.40)))
        self.assertEqual(
            project_quad(lambda _corner: next(projected), range(4)),
            [[320, 180], [640, 180], [704, 432], [256, 432]],
        )

    def test_project_quad_rejects_off_canvas_points(self):
        with self.assertRaisesRegex(ValueError, "outside the 1280x720 canvas"):
            project_quad(lambda _corner: (-0.01, 0.5), range(4))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the geometry test and confirm the module is absent**

Run:

```powershell
python -m unittest tests.test_newsroom_geometry -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'build_newsroom'`.

- [ ] **Step 3: Implement projection as an import-safe unit**

Place Blender imports inside `if bpy is not None` paths so tests can import the projection function:

```python
try:
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
except ImportError:
    bpy = None

from scene_config import DESKS, NEWSROOM_OUTPUT_NAMES, RenderSpec

SPEC = RenderSpec()

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
```

- [ ] **Step 4: Implement the full-scene builder using the approved visual language**

Implement these concrete scene rules in `src/build_newsroom.py`:

1. Reuse the approved `material`, `cube`, `uv_sphere`, `look_at`, `keyframe`, Eevee detection, camera-ray white World nodes, AgX look, and area-light values from `src/build_scene.py`; copy the code into the new renderer so importing or changing it cannot alter the approved sample script.
2. Create a `base` collection with a rounded white floor scaled to `(13.0, 10.0, 0.15)`.
3. Create one collection per desk named `desk_a1` through `desk_a6`.
4. Implement `build_role(desk, parent, materials) -> dict[str, object]` with the exact approved torso `(0.64,0.46,0.72)`, head `(0.47,0.43,0.48)`, and arm `(0.13,0.48,0.13)` dimensions. Use `desk.color` on every torso and arm; do not vary silhouette dimensions between roles.
5. Implement `build_workstation(desk, parent, materials) -> dict[str, object]` using a compact version of the approved desk, monitor, keyboard, chair, and drawer. Give every desk the same structural dimensions.
6. Add only the role-specific primitives named in `desk.props`: flat movable cards and a blue trend screen for A1; a headband plus two ear cups and material folders for A2; keyboard keys plus a pale manuscript sheet for A3; a magenta marking pen and issue-confirmation badge for A4; two small side monitors and a yellow publish key for A5; cyan chart bars and three signal posts for A6.
7. Parent each workstation collection to an empty at `desk.location`, rotate it by `desk.rotation_degrees`, and keep the irregular center clear within world coordinates `x=-1.0..1.0`, `y=-1.0..1.2`.
8. Keep the approved 52 mm lens. Animate camera `(15.0,-19.4,15.3)` at frame 1 to `(13.6,-17.6,13.9)` at frame 20, looking at `(0,0,1.0)`; hold the frame-20 transform through frame 120.
9. Use the approved key light direction and soft fill, scaling only area-light sizes to `8.0` and `6.0` and energy to `1800` and `1050` for the larger floor. Keep the camera-ray background white and non-camera environment dark gray so contact shadows remain visible.
10. Stagger desk visibility with scale keys: A2/A5 frames 1–8, A1/A4 frames 5–13, A3/A6 frames 10–18, all reaching scale `(1,1,1)`. Do not hide roles at any rendered frame; start at scale `0.92` and opacity 1.
11. Animate frames 21–120 with matching endpoints. Give every torso the approved breathing scale cycle. A1 slides a card 0.12 units and glances at the screen; A2 tilts the head 4 degrees and moves a folder; A3 alternates arms over the keyboard; A4 moves the pen and nods; A5 turns 5 degrees between side screens; A6 tilts toward chart bars. Screen emission changes no more than 15%.
12. At frame 70, put each role in its response pose and switch its screen to a role-specific motif: A1 trend bars, A2 audio waveform, A3 text lines, A4 marked issue, A5 platform tiles, and A6 chart bars. Render each independent highlight by hiding `base` and the five unselected collections, enabling film transparency, and rendering the selected collection plus a color-matched flattened ring. Restore every collection after each still.
13. Obtain each desktop hit quad from the four top-surface corners transformed by `desk_top.matrix_world`; project with `world_to_camera_view(scene, camera, world_corner)` at frame 21; write integer points to `newsroom-hit-regions.json`.
14. In preview mode render only frames 1, 21, 70, and 120. In full mode render all frames. Both modes render cover at frame 21, all six highlights at frame 70, projected regions, and `newsroom.blend`.

- [ ] **Step 5: Run the pure geometry tests**

Run:

```powershell
python -m unittest tests.test_newsroom_geometry -v
```

Expected: two tests pass without requiring Blender on Python's import path.

- [ ] **Step 6: Run the low-cost Blender preview**

Run:

```powershell
$blender = Get-ChildItem "$env:ProgramFiles\Blender Foundation\Blender *\blender.exe" |
  Sort-Object FullName |
  Select-Object -Last 1 -ExpandProperty FullName
& $blender --background --python src/build_newsroom.py -- "$PWD\output" --mode preview
```

Expected: Blender reports `5.2.0 LTS`, exits 0, and writes four representative PNGs, one cover, six non-empty transparent highlights, one hit-region JSON file, and `newsroom.blend`. No `newsroom-frames/frame_*.png` sequence is produced in preview mode.

- [ ] **Step 7: Review the preview before paying full render cost**

Open the cover and four representative frames and confirm:

- six same-shape roles remain visible and use red, orange, green, purple-red, yellow, and cyan clothing in A1–A6 order;
- six desks form an irregular ring with an uncluttered center;
- all required props are recognizable without changing the unified role silhouette;
- the camera feels like the approved elevated 52 mm sample rather than a wide-angle replacement;
- the upper background remains near-white and every desk has a readable contact shadow;
- frame 21 and frame 120 have matching camera framing and no visible endpoint brightness change.

If any item fails, change only the new full-scene script and repeat preview mode. Do not run the 120-frame render until all seven checks pass.

### Task 3: Generate and Verify Perspective-Accurate Web Configuration

**Files:**
- Create: `src/export_web_config.py`
- Modify: `src/verify_outputs.py`
- Modify: `tests/test_verify_outputs.py`
- Create: `web/scene-data.js`

**Interfaces:**
- `load_hit_regions(path: Path) -> dict[str, list[list[int]]]`.
- `build_web_config(regions) -> list[dict]` returns serializable desk records with `id`, `module`, `title`, `english`, `role`, `responsibility`, `color`, `action`, `destination`, `highlight`, `points`, and `cardSide`.
- `write_web_config(output_path: Path, desks: list[dict])` writes `window.NEWSROOM_DESKS = Object.freeze([...]);`.
- `validate_hit_regions(payload: dict) -> list[str]`.
- `validate_newsroom(root: Path) -> list[str]` validates complete-scene outputs without changing `verify(root)` sample behavior.

- [ ] **Step 1: Add failing verifier tests for six highlights and polygons**

Append tests using these exact fixtures:

```python
from verify_outputs import validate_hit_regions, validate_newsroom_highlights

def test_hit_regions_require_six_distinct_in_bounds_quads(self):
    valid = {
        "viewBox": [0, 0, 1280, 720],
        "regions": {
            f"a{index}": [[100 * index, 100], [100 * index + 80, 105],
                         [100 * index + 70, 180], [100 * index - 5, 175]]
            for index in range(1, 7)
        },
    }
    self.assertEqual(validate_hit_regions(valid), [])
    valid["regions"]["a6"] = valid["regions"]["a5"]
    self.assertIn("hit-region polygons must be distinct", validate_hit_regions(valid))

def test_newsroom_highlights_require_all_six_rgba_assets(self):
    images = {
        f"a{index}": Image.new("RGBA", (1280, 720), (255, 255, 255, 0))
        for index in range(1, 7)
    }
    images["a1"].putpixel((10, 10), (200, 20, 40, 255))
    errors = validate_newsroom_highlights(images)
    self.assertIn("a2 highlight must contain visible pixels", errors)
    self.assertNotIn("a1 highlight must contain visible pixels", errors)
```

- [ ] **Step 2: Run the verifier tests and observe missing exports**

Run:

```powershell
python -m unittest tests.test_verify_outputs -v
```

Expected: existing tests pass and new tests fail with `ImportError` for `validate_hit_regions`.

- [ ] **Step 3: Implement polygon and six-highlight validation**

Add the following rules to `src/verify_outputs.py`:

```python
def validate_hit_regions(payload: dict) -> list[str]:
    errors = []
    if payload.get("viewBox") != [0, 0, 1280, 720]:
        errors.append("hit-region viewBox must be 1280x720")
    regions = payload.get("regions", {})
    if list(regions) != [f"a{index}" for index in range(1, 7)]:
        errors.append("hit regions must be ordered a1 through a6")
        return errors
    polygons = []
    for desk_id, points in regions.items():
        if len(points) != 4:
            errors.append(f"{desk_id} hit region must contain four points")
            continue
        if any(len(point) != 2 or not 0 <= point[0] <= 1280
               or not 0 <= point[1] <= 720 for point in points):
            errors.append(f"{desk_id} hit region must stay inside 1280x720")
        twice_area = abs(sum(
            points[index][0] * points[(index + 1) % 4][1]
            - points[(index + 1) % 4][0] * points[index][1]
            for index in range(4)
        ))
        if twice_area < 4000:
            errors.append(f"{desk_id} hit region is too small")
        polygons.append(tuple(tuple(point) for point in points))
    if len(set(polygons)) != len(polygons):
        errors.append("hit-region polygons must be distinct")
    return errors

def validate_newsroom_highlights(images: dict[str, Image.Image]) -> list[str]:
    errors = []
    for desk_id in (f"a{index}" for index in range(1, 7)):
        image = images.get(desk_id)
        if image is None:
            errors.append(f"missing highlight: {desk_id}")
            continue
        if image.size != (1280, 720) or image.mode != "RGBA":
            errors.append(f"{desk_id} highlight must be 1280x720 RGBA")
            continue
        alpha_min, alpha_max = image.getchannel("A").getextrema()
        if alpha_min != 0:
            errors.append(f"{desk_id} highlight must contain transparent pixels")
        if alpha_max == 0:
            errors.append(f"{desk_id} highlight must contain visible pixels")
    return errors
```

Implement `validate_newsroom(root)` to require H.264, `yuv420p`, 1280×720, 24 fps, 120 decoded frames, 5.0 seconds, a near-white cover, visible contact-shadow pixels, visible clothing-color evidence for all six configured colors, six valid highlights, valid hit-region JSON, and representative frames 1, 21, 70, and 120. Prefix errors with the artifact or desk ID. Leave `verify(root)` and its sample messages unchanged.

- [ ] **Step 4: Implement deterministic JavaScript config generation**

Create `src/export_web_config.py`. Read the JSON in UTF-8, call `validate_hit_regions`, convert Python RGBA to six-digit CSS hex with `rgba_hex(desk.color)[:7]`, and construct every emitted record with:

```python
records = [
    {
        "id": desk.id,
        "module": desk.module,
        "title": desk.title,
        "english": desk.english,
        "role": desk.role,
        "responsibility": desk.responsibility,
        "color": rgba_hex(desk.color)[:7],
        "action": desk.action,
        "destination": desk.destination,
        "highlight": f"assets/newsroom-{desk.id}-highlight.png",
        "points": " ".join(f"{x},{y}" for x, y in regions[desk.id]),
        "cardSide": desk.card_side,
    }
    for desk in DESKS
]
```

Serialize `records` with `json.dumps(..., ensure_ascii=False, indent=2)`, prepend `window.NEWSROOM_DESKS = Object.freeze(`, and append `);\n`. This emits all six records in `DESKS` order and derives each SVG point string from its own projected JSON quad. Do not hard-code hand-tuned polygons or silently clamp invalid projections.

- [ ] **Step 5: Generate the config from the preview projection**

Run:

```powershell
python src/export_web_config.py output/newsroom-hit-regions.json web/scene-data.js
node --check web/scene-data.js
```

Expected: both commands exit 0; `web/scene-data.js` contains six records and six distinct four-point SVG strings.

- [ ] **Step 6: Run verifier unit tests**

Run:

```powershell
python -m unittest tests.test_verify_outputs -v
```

Expected: seven verifier tests pass.

### Task 4: Add a Render-Cost-Aware Full Pipeline

**Files:**
- Create: `scripts/render-newsroom.ps1`
- Modify: `.gitignore`
- Modify: `README.md`

**Interfaces:**
- `render-newsroom.ps1 -PreviewOnly` renders four representative frames, cover, highlights, projection JSON, JavaScript config, and Blend source; it does not encode MP4.
- `render-newsroom.ps1` performs one full 120-frame render, H.264 encoding, complete verification, and web synchronization.
- `render-newsroom.ps1 -SkipRender` re-encodes and re-verifies an existing complete `output/newsroom-frames/` sequence.
- Success sentinels are `NEWSROOM_PREVIEW_COMPLETE` and `NEWSROOM_PIPELINE_COMPLETE`.

- [ ] **Step 1: Implement strict mode selection and dependency checks**

The script uses:

```powershell
param(
  [switch]$PreviewOnly,
  [switch]$SkipRender
)
$ErrorActionPreference = "Stop"
if ($PreviewOnly -and $SkipRender) {
  throw "PreviewOnly and SkipRender cannot be combined."
}
```

Resolve Blender under `"$env:ProgramFiles\Blender Foundation\Blender *\blender.exe"` and require `ffmpeg`, `ffprobe`, `python`, and `node` via `Get-Command`. Create `output`, `output/newsroom-frames`, `output/newsroom-preview`, and `web/assets`. Delete only `newsroom-*` artifacts for a fresh full render; never delete `sample.*` or `output/frames/`.

- [ ] **Step 2: Implement preview and full branches**

For `-PreviewOnly`, call Blender with `--mode preview`, generate `web/scene-data.js`, run `node --check`, and print `NEWSROOM_PREVIEW_COMPLETE`.

For full mode, unless `-SkipRender`, remove existing `newsroom-frames/frame_*.png`, call Blender with `--mode full`, and assert exactly 120 contiguous frame files. Encode:

```powershell
ffmpeg -y -framerate 24 `
  -i (Join-Path $newsroomFrames "frame_%04d.png") `
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart `
  (Join-Path $output "newsroom.mp4")
```

Then generate `web/scene-data.js`, run `python src/verify_outputs.py output --newsroom`, copy the MP4, cover, and six highlight PNGs to `web/assets`, compare each source/destination SHA-256 with `Get-FileHash`, and print `NEWSROOM_PIPELINE_COMPLETE`.

- [ ] **Step 3: Keep generated full-scene artifacts out of source control without changing sample rules**

Add:

```gitignore
output/newsroom-frames/
output/newsroom-preview/
output/newsroom-*
web/assets/newsroom-*
```

Do not remove existing ignore entries.

- [ ] **Step 4: Document cost controls and commands**

Update `README.md` with:

- the approved sample command remains `scripts/render-sample.ps1`;
- Blender 5.2.0 LTS is installed and is the tested complete-scene renderer;
- `scripts/render-newsroom.ps1 -PreviewOnly` is mandatory before a full render;
- the full render creates 120 base frames plus seven stills (cover and six highlights), while preview creates only four base frames plus seven stills;
- `-SkipRender` is for encoding/verifier/browser iteration after a successful complete frame render;
- full outputs and the six existing `demo/pages/m1-topics.html` through `m6-insights.html` destinations;
- preview server and all verification commands from the Completion Gate.

- [ ] **Step 5: Exercise preview mode**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1 -PreviewOnly
```

Expected: exit 0 ending in `NEWSROOM_PREVIEW_COMPLETE`; no sample artifact hash or modification time changes.

### Task 5: Build the Six-Desk SVG and Information Interface

**Files:**
- Modify: `web/index.html`
- Modify: `web/styles.css`
- Create: `tests/test_web_contract.py`

**Interfaces:**
- Consumes: `window.NEWSROOM_DESKS`, `assets/newsroom.mp4`, `assets/newsroom-cover.png`, and six highlight paths.
- Produces: six native SVG `<a>` links with polygon hit regions, six independent highlight `<img>` elements, one reusable card, and live status/fallback regions.
- `preserveAspectRatio="xMidYMid slice"` must match CSS `object-fit: cover` so hit polygons remain aligned at every viewport ratio.

- [ ] **Step 1: Write the failing static web contract test**

Create `tests/test_web_contract.py`:

```python
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]

class WebContractTests(unittest.TestCase):
    def test_scene_contains_six_native_links_and_configured_destinations(self):
        html = (ROOT / "web/index.html").read_text(encoding="utf-8")
        config = (ROOT / "web/scene-data.js").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r'data-desk-id="a[1-6]"', html)), 6)
        for index, slug in enumerate(
            ("topics", "collection", "writing", "review", "channels", "insights"),
            start=1,
        ):
            destination = f"../../demo/pages/m{index}-{slug}.html"
            self.assertIn(destination, html)
            self.assertIn(destination, config)
            self.assertTrue((ROOT / "web" / destination).resolve().is_file())

    def test_each_hit_link_owns_a_polygon_and_highlight(self):
        html = (ROOT / "web/index.html").read_text(encoding="utf-8")
        for index in range(1, 7):
            self.assertRegex(
                html,
                rf'<a[^>]+data-desk-id="a{index}"[\s\S]+?'
                rf'<polygon[^>]+data-hit-id="a{index}"',
            )
            self.assertIn(f'data-highlight-id="a{index}"', html)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the static contract and observe the one-desk failure**

Run:

```powershell
python -m unittest tests.test_web_contract -v
```

Expected: both tests fail because the current page has one HTML link and no generated six-desk configuration.

- [ ] **Step 3: Replace the one-desk shell with six native SVG links**

Keep the HTML concise and explicit:

```html
<main class="hero" data-scene data-active-desk="">
  <video class="scene-video" data-video autoplay muted playsinline
         poster="assets/newsroom-cover.png" aria-hidden="true">
    <source src="assets/newsroom.mp4" type="video/mp4">
  </video>
  <div class="highlight-stack" aria-hidden="true">
    <img class="highlight" data-highlight-id="a1" data-src="assets/newsroom-a1-highlight.png" alt="">
    <img class="highlight" data-highlight-id="a2" data-src="assets/newsroom-a2-highlight.png" alt="">
    <img class="highlight" data-highlight-id="a3" data-src="assets/newsroom-a3-highlight.png" alt="">
    <img class="highlight" data-highlight-id="a4" data-src="assets/newsroom-a4-highlight.png" alt="">
    <img class="highlight" data-highlight-id="a5" data-src="assets/newsroom-a5-highlight.png" alt="">
    <img class="highlight" data-highlight-id="a6" data-src="assets/newsroom-a6-highlight.png" alt="">
  </div>
  <svg class="hit-map" viewBox="0 0 1280 720"
       preserveAspectRatio="xMidYMid slice" aria-label="智媒编辑部六个工位">
    <a data-desk-id="a1" id="desk-link-a1" href="../../demo/pages/m1-topics.html"
       aria-label="A1 智能选题，策划编辑" aria-controls="role-card" aria-expanded="false">
      <polygon data-hit-id="a1" points=""></polygon>
    </a>
    <a data-desk-id="a2" id="desk-link-a2" href="../../demo/pages/m2-collection.html"
       aria-label="A2 智能采集，记者" aria-controls="role-card" aria-expanded="false">
      <polygon data-hit-id="a2" points=""></polygon>
    </a>
    <a data-desk-id="a3" id="desk-link-a3" href="../../demo/pages/m3-writing.html"
       aria-label="A3 智能写作，文字编辑" aria-controls="role-card" aria-expanded="false">
      <polygon data-hit-id="a3" points=""></polygon>
    </a>
    <a data-desk-id="a4" id="desk-link-a4" href="../../demo/pages/m4-review.html"
       aria-label="A4 智能审校，审校编辑" aria-controls="role-card" aria-expanded="false">
      <polygon data-hit-id="a4" points=""></polygon>
    </a>
    <a data-desk-id="a5" id="desk-link-a5" href="../../demo/pages/m5-channels.html"
       aria-label="A5 全渠道分发，运营编辑" aria-controls="role-card" aria-expanded="false">
      <polygon data-hit-id="a5" points=""></polygon>
    </a>
    <a data-desk-id="a6" id="desk-link-a6" href="../../demo/pages/m6-insights.html"
       aria-label="A6 效果洞察，数据分析师" aria-controls="role-card" aria-expanded="false">
      <polygon data-hit-id="a6" points=""></polygon>
    </a>
  </svg>
  <aside class="role-card" id="role-card" data-card hidden>
    <span data-card-kicker></span><h1 data-card-title></h1>
    <b data-card-role></b><p data-card-copy></p><small data-card-action></small>
    <em>点击进入模块 →</em>
  </aside>
  <p class="sr-status" data-status role="status" aria-live="polite" aria-atomic="true"></p>
  <p class="fallback-message" data-fallback role="status" aria-live="polite" aria-atomic="true"></p>
</main>
<script src="scene-data.js"></script>
<script src="app.js"></script>
```

At startup, JavaScript fills each empty polygon from the corresponding generated `points`. Keeping explicit native `href` values provides navigation if scripting fails.

- [ ] **Step 4: Implement alignment, state, focus, and fallback CSS**

Use one common absolute layer geometry:

```css
.scene-video,.highlight-stack,.highlight,.hit-map{
  position:absolute;inset:0;width:100%;height:100%;
}
.scene-video,.highlight{object-fit:cover}
.hit-map{pointer-events:auto}
.hit-map polygon{fill:transparent;stroke:transparent;transition:fill .1s ease,stroke .1s ease}
.hit-map a:focus-visible polygon{stroke:var(--desk-color);stroke-width:5;fill:#ffffff12}
.highlight{opacity:0;pointer-events:none;transition:opacity .1s ease}
.hero[data-active-desk="a1"] [data-highlight-id="a1"],
.hero[data-active-desk="a2"] [data-highlight-id="a2"],
.hero[data-active-desk="a3"] [data-highlight-id="a3"],
.hero[data-active-desk="a4"] [data-highlight-id="a4"],
.hero[data-active-desk="a5"] [data-highlight-id="a5"],
.hero[data-active-desk="a6"] [data-highlight-id="a6"]{opacity:1}
.hero.has-selection .scene-video{filter:brightness(.78) saturate(.72)}
.hero.has-selection .highlight{filter:drop-shadow(0 15px 26px var(--desk-glow))}
.scene-video,.highlight-stack{transition:filter .22s ease,transform .35s ease}
.hero.is-confirming .scene-video,.hero.is-confirming .highlight-stack{transform:scale(1.015)}
.hero.is-confirming .highlight{filter:brightness(1.08) drop-shadow(0 15px 26px var(--desk-glow))}
.hero.low-performance .scene-video,.hero.video-failed .scene-video{display:none}
.hero.low-performance .highlight-stack{display:none}
.hero.highlight-failed .hit-map a[aria-expanded="true"] polygon{
  fill:var(--desk-wash);stroke:var(--desk-color);stroke-width:4
}
```

Keep the existing hidden live-region utility. Position `.role-card[data-side="right"]` on the right and `[data-side="left"]` on the left; on screens below 700 px place it across the bottom with a maximum height of 38vh. Use `pointer-events:none` so the card cannot block a desk. Set card border and copy accents from `--desk-color`.

The `.is-confirming` scale is the click camera-push cue and lasts only for the controller's 350 ms navigation delay; the selected frame-70 highlight supplies the role confirmation pose. Under `prefers-reduced-motion: reduce`, set every animation/transition and confirming transform to none and hide the video. Ensure highlight opacity is immediate. Under coarse pointer, increase the SVG polygon stroke hit target with transparent `stroke-width:16` while retaining the projected visible fill boundary.

- [ ] **Step 5: Run static web tests**

Run:

```powershell
python -m unittest tests.test_web_contract -v
```

Expected: two tests pass and all six destination existence checks succeed.

### Task 6: Implement Six-Desk Interaction and Browser Coverage

**Files:**
- Modify: `web/app.js`
- Create: `.superpowers/sdd/six-desk-browser-smoke.mjs`

**Interfaces:**
- `activate(deskId, source)`, `deactivate(message)`, `requestNavigation(desk, event)`, `applyMotionPreference()`, and `applyPerformanceMode()` are the controller boundaries.
- Active state is represented only by `scene.dataset.activeDesk`, `scene.classList.contains("has-selection")`, six links' `aria-expanded`, and one visible card.
- Browser smoke base URL remains `http://localhost:4173/interactive-newsroom-hero/web/`.

- [ ] **Step 1: Extend the browser harness first and observe the expected failure**

Copy the proven Edge startup, WebSocket command helper, media blocking, reduced-motion emulation, autoplay injection, and cleanup code from `.superpowers/sdd/task4-browser-smoke.mjs` into the new harness. Replace the one-desk assertions with loops over:

```javascript
const expected = [
  ["a1", "A1 智能选题", "策划编辑", "/demo/pages/m1-topics.html"],
  ["a2", "A2 智能采集", "记者", "/demo/pages/m2-collection.html"],
  ["a3", "A3 智能写作", "文字编辑", "/demo/pages/m3-writing.html"],
  ["a4", "A4 智能审校", "审校编辑", "/demo/pages/m4-review.html"],
  ["a5", "A5 全渠道分发", "运营编辑", "/demo/pages/m5-channels.html"],
  ["a6", "A6 效果洞察", "数据分析师", "/demo/pages/m6-insights.html"],
];
```

Assert:

1. exactly six SVG native links exist in A1–A6 DOM order;
2. every link has a distinct non-empty four-point polygon and the expected `href`;
3. pointer enter switches the active ID, card copy, card side, CSS color, and matching highlight within 100 ms;
4. only one link is expanded and only one highlight is opaque;
5. non-selected desks remain in the DOM and visible under the dimmed video;
6. focus activates each link; Escape collapses while retaining focus; Enter reaches the expected target;
7. first touch tap selects without navigation and second touch tap reaches each expected target;
8. blocked `newsroom.mp4` shows the cover and keeps all links usable;
9. blocking only `newsroom-a3-highlight.png` produces an A3 SVG/CSS ring and leaves A3 navigation usable;
10. reduced motion pauses/hides video, sets transition durations to zero, and navigates without a delay timer;
11. low-performance emulation sets `navigator.hardwareConcurrency` to 2 before load, makes zero highlight image requests, shows the cover, and retains navigation;
12. a rewritten A6 destination returning 404 does not navigate and announces `目标页面暂不可用，请稍后重试。`;
13. autoplay rejection retries on first pointer interaction;
14. natural playback reaches the end and seeks to `20 / 24`;
15. media reports 1280×720 and 5.0 seconds.

Run while the preview server is active:

```powershell
node .superpowers/sdd/six-desk-browser-smoke.mjs
```

Expected before the controller rewrite: FAIL on the first assertion that requires six initialized polygon links.

- [ ] **Step 2: Implement data initialization and one-active-desk state**

On `DOMContentLoaded`, require exactly six `window.NEWSROOM_DESKS` records. For each record:

- locate its link, polygon, and highlight;
- assert the native `href` equals the config destination;
- set polygon `points`;
- set `--desk-color`, `--desk-wash` as `${color}22`, and `--desk-glow` as `${color}44` on the link;
- attach `load` and `error` listeners before assigning `highlight.src = highlight.dataset.src`;
- skip assigning all highlight sources when low-performance mode is active.

`activate(id, source)` must set one active ID, set only that link's `aria-expanded` to `true`, populate all five card fields, set `data-side`, unhide the card, and announce module, role, responsibility, and action. It must not remove or hide the other five role links.

`deactivate(message)` clears the active ID, collapses every link, hides and clears the card, resets the touch-armed ID, and writes the optional announcement.

- [ ] **Step 3: Implement pointer, touch, keyboard, and guarded navigation**

For each link:

- `pointerenter` activates for non-touch pointers;
- `pointerleave` deactivates only when that link is not focused;
- `focus` activates unless that focused link was just Escape-dismissed;
- `blur` clears the Escape guard and deactivates;
- Escape prevents default, retains focus, collapses, and announces `已取消 <module>。`;
- first touch click on a non-active desk prevents default and activates it;
- second touch click uses guarded navigation;
- mouse click and keyboard Enter use guarded navigation.

`requestNavigation` must prevent default, call `fetch(link.href, {method: "HEAD", cache: "no-store"})`, and navigate only for an OK response. On failure, remove confirmation state and announce the exact missing-target message. For reduced motion, assign `location.href` immediately after the successful HEAD. Otherwise add `.is-confirming`, wait 350 ms, and assign the URL; this remains below the 500 ms limit.

- [ ] **Step 4: Preserve and generalize proven media degradation**

Carry forward the sample's bounded no-source watcher, source-element error listener, autoplay `NotAllowedError` recovery, reduced-motion `change` listener, and ended seek to `20 / 24`. Change filenames and messages only where required.

Performance mode is true when any condition holds:

```javascript
const lowPerformance =
  navigator.connection?.saveData === true
  || (Number.isFinite(navigator.deviceMemory) && navigator.deviceMemory <= 4)
  || navigator.hardwareConcurrency <= 4;
```

In that mode add `.low-performance`, pause video, do not assign highlight `src`, and announce no warning unless media also fails. An individual highlight error adds its desk ID to a `Set`; when that failed desk becomes active, add `.highlight-failed`. Clear that class when activating a desk whose image loaded.

- [ ] **Step 5: Run syntax, static, and browser tests**

Run:

```powershell
node --check web/app.js
node --check .superpowers/sdd/six-desk-browser-smoke.mjs
python -m unittest tests.test_web_contract -v
node .superpowers/sdd/six-desk-browser-smoke.mjs
```

Expected: syntax checks emit no errors; two static web tests pass; browser output contains one PASS line for each of the 15 contracts above and exits 0.

### Task 7: Render Once, Verify Everything, and Complete Visual Acceptance

**Files:**
- Modify: `README.md`
- Generated only: `output/newsroom-*`, `output/newsroom-frames/*`, `web/assets/newsroom-*`, `web/scene-data.js`

**Interfaces:**
- Consumes all earlier task outputs.
- Produces the final complete-scene MP4, cover, six transparent highlights, six projected hit regions, synchronized web assets, browser proof, and documented evidence.

- [ ] **Step 1: Run all inexpensive checks before the full render**

Run:

```powershell
python -m unittest discover -s tests -v
python -m py_compile src/scene_config.py src/build_scene.py src/build_newsroom.py src/export_web_config.py src/verify_outputs.py
node --check web/scene-data.js
node --check web/app.js
node --check .superpowers/sdd/task4-browser-smoke.mjs
node --check .superpowers/sdd/six-desk-browser-smoke.mjs
powershell -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1 -PreviewOnly
```

Expected: all Python tests pass, compilation and Node syntax checks are silent, and preview ends in `NEWSROOM_PREVIEW_COMPLETE`. Stop and fix failures before starting the expensive render.

- [ ] **Step 2: Run the complete render exactly once after preview approval**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1
```

Expected: Blender renders exactly 120 base frames and seven stills, FFmpeg encodes H.264/yuv420p, verifier prints `newsroom media verification passed`, asset hash comparisons pass, and output ends with `NEWSROOM_PIPELINE_COMPLETE`.

- [ ] **Step 3: Run media probes and both regression suites**

Run:

```powershell
python -m unittest discover -s tests -v
python src/verify_outputs.py output
python src/verify_outputs.py output --newsroom
ffprobe -v error -count_frames -select_streams v:0 `
  -show_entries stream=codec_name,pix_fmt,width,height,r_frame_rate,nb_read_frames:format=duration `
  -of json output/newsroom.mp4
```

Expected:

```text
sample media verification passed
newsroom media verification passed
codec_name=h264
pix_fmt=yuv420p
width=1280
height=720
r_frame_rate=24/1
nb_read_frames=120
duration=5.000000
```

If the retained sample verifier still prints its current `media verification passed` string, accept that exact sample line; the new newsroom mode must print `newsroom media verification passed`.

- [ ] **Step 4: Run both browser smoke suites from the parent-directory server**

In one terminal:

```powershell
python -m http.server 4173 --directory ..
```

In another:

```powershell
$env:EDGE_EXECUTABLE = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$env:EDGE_DEBUG_PORT = "9333"
node .superpowers/sdd/task4-browser-smoke.mjs
$env:EDGE_DEBUG_PORT = "9334"
node .superpowers/sdd/six-desk-browser-smoke.mjs
```

Expected: the approved A1 sample regression smoke exits 0, followed by the six-desk smoke exiting 0 with all A1–A6 navigation and degradation PASS lines.

- [ ] **Step 5: Perform final visual and physical-input checks**

At `http://localhost:4173/interactive-newsroom-hero/web/`, verify:

1. entry order reads spatially and the idle seam has no camera jump or brightness flash;
2. all six characters share the approved shape and remain visible;
3. colors, roles, actions, props, card copy, and destinations match Task 1;
4. each SVG region follows its own desktop perspective and does not activate a neighbor along shared visual boundaries;
5. each transparent highlight aligns with its base desk and starts within 100 ms;
6. information cards remain on the configured opposite side and do not cover the selected character;
7. physical touch requires two taps and physical keyboard completes Tab, Enter, and Escape flows;
8. normal laptop playback is smooth; low-performance and reduced-motion modes remain fully navigable;
9. DevTools-blocked main video, one blocked highlight, and a missing target each produce the specified fallback without breaking other desks;
10. no sample asset was overwritten and no visual or source element resembles copied Marvis material.

- [ ] **Step 6: Record final hashes and update README status**

Record SHA-256 hashes for `newsroom.mp4`, cover, Blend source, hit-region JSON, and all six highlights; record that matching `web/assets` hashes were verified. Add the final automated command list and manual-check result to README. Do not include generated frame files in documentation.

## Completion Gate

The six-desk expansion is complete only when:

- all Python tests, Python compilation, and JavaScript syntax checks pass;
- the approved one-desk media verifier and browser smoke still pass unchanged;
- the complete-scene verifier confirms H.264, yuv420p, 1280×720, 24 fps, 120 decoded frames, 5.0 seconds, white background, contact shadows, and all six clothing colors;
- all six 1280×720 RGBA highlight PNGs contain both transparent and visible pixels;
- all six generated four-point SVG regions are in bounds, distinct, visibly aligned to their rendered desktops, and do not produce obvious cross-activation;
- Edge smoke verifies six destinations, one-at-a-time selection, 100 ms feedback, touch, keyboard, reduced motion, low performance, video failure, individual-highlight failure, autoplay recovery, and missing-target handling;
- manual review confirms the approved unified role shape, miniature lighting, camera language, restrained animation, and interaction quality were preserved;
- original sample assets and commands remain reproducible;
- no Git repository was initialized and no commit was created.

If any gate fails, keep the complete scene behind the existing approved sample and report the failed command or visual criterion. Do not substitute a screen recording, hand-drawn hit boxes, opaque highlights, or broken links for the required artifacts.
