# Interactive Newsroom Sample Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a five-second original miniature-newsroom MP4 sample with one colored character, a transparent hover layer, and a browser interaction proof.

**Architecture:** A standalone Blender Python script procedurally builds and animates the sample scene. Blender renders deterministic PNG frames; FFmpeg encodes them to H.264 MP4; a dependency-free HTML viewer overlays an SVG hit area, transparent highlight, role copy, and navigation behavior.

**Tech Stack:** Blender 4.x Python API, Python 3.11 standard library, FFmpeg 8.1, HTML5 video, SVG, CSS, vanilla JavaScript.

## Global Constraints

- Build an original white miniature newsroom; do not copy third-party models, characters, layout, camera, or animation assets.
- Keep the character visible in every visual state.
- Use one unified rounded character design with red clothing for the A1 sample.
- Render 120 frames at 24 fps and 1280×720 for an exact five-second sample.
- Keep entry motion in frames 1–20 and a loop-compatible idle section in frames 21–120.
- Generate `sample.mp4`, `sample-cover.png`, and transparent `sample-highlight.png`.
- Hover feedback must start within 100 ms and show role, module, responsibility, and entry prompt.
- The parent directory is not a Git repository; verification replaces commit steps in this plan.

---

## File Map

- `README.md` — setup, render, verify, and preview commands.
- `.gitignore` — excludes generated frame sequences and local render artifacts.
- `src/scene_config.py` — renderer-independent constants and output contract.
- `src/build_scene.py` — procedural Blender scene, animation, and render passes.
- `src/verify_outputs.py` — validates image dimensions, transparency, MP4 duration, and frame rate.
- `scripts/render-sample.ps1` — locates Blender, renders frames, encodes MP4, and verifies outputs.
- `tests/test_scene_config.py` — unit tests for timing, colors, and output names.
- `tests/test_verify_outputs.py` — unit tests for media-probe parsing and validation rules.
- `web/index.html` — sample viewer structure and accessible interaction controls.
- `web/styles.css` — full-screen white miniature presentation and hover states.
- `web/app.js` — mouse, touch, keyboard, fallback, and navigation behavior.
- `web/assets/` — generated MP4, cover, and transparent highlight copied by the render script.
- `output/` — disposable Blender PNG frame sequence and final render outputs.

### Task 1: Lock the Render Contract

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `src/scene_config.py`
- Create: `tests/test_scene_config.py`

**Interfaces:**
- Produces: `RenderSpec`, `A1_ROLE`, `OUTPUT_NAMES`, and `rgba_hex()` for the Blender builder and verifier.

- [ ] **Step 1: Write the failing render-contract test**

```python
# tests/test_scene_config.py
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from scene_config import A1_ROLE, OUTPUT_NAMES, RenderSpec, rgba_hex


class RenderSpecTests(unittest.TestCase):
    def test_sample_is_exactly_five_seconds(self):
        spec = RenderSpec()
        self.assertEqual(spec.fps, 24)
        self.assertEqual(spec.frame_start, 1)
        self.assertEqual(spec.frame_end, 120)
        self.assertEqual(spec.duration_seconds, 5.0)

    def test_sample_uses_hd_canvas(self):
        spec = RenderSpec()
        self.assertEqual((spec.width, spec.height), (1280, 720))

    def test_a1_role_contract(self):
        self.assertEqual(A1_ROLE["module"], "A1 智能选题")
        self.assertEqual(A1_ROLE["role"], "策划编辑")
        self.assertEqual(rgba_hex(A1_ROLE["color"]), "#c8102eff")

    def test_required_outputs_are_named(self):
        self.assertEqual(
            OUTPUT_NAMES,
            {
                "video": "sample.mp4",
                "cover": "sample-cover.png",
                "highlight": "sample-highlight.png",
            },
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and confirm the missing module**

Run:

```powershell
python -m unittest tests.test_scene_config -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scene_config'`.

- [ ] **Step 3: Implement the render contract**

```python
# src/scene_config.py
from dataclasses import dataclass


@dataclass(frozen=True)
class RenderSpec:
    fps: int = 24
    frame_start: int = 1
    frame_end: int = 120
    width: int = 1280
    height: int = 720
    entry_end: int = 20
    idle_start: int = 21

    @property
    def duration_seconds(self) -> float:
        return self.frame_end / self.fps


A1_ROLE = {
    "module": "A1 智能选题",
    "role": "策划编辑",
    "responsibility": "聚合热点信号，形成可执行的报道方向。",
    "color": (0.784, 0.063, 0.180, 1.0),
}

OUTPUT_NAMES = {
    "video": "sample.mp4",
    "cover": "sample-cover.png",
    "highlight": "sample-highlight.png",
}


def rgba_hex(color: tuple[float, float, float, float]) -> str:
    return "#" + "".join(f"{round(channel * 255):02x}" for channel in color)
```

- [ ] **Step 4: Add project instructions and generated-file exclusions**

```markdown
<!-- README.md -->
# Interactive Newsroom Hero

This isolated prototype generates a five-second original miniature-newsroom sample.

## Requirements

- Windows 10 or later
- Python 3.11+
- Blender 4.x
- FFmpeg and FFprobe

## Render and verify

```powershell
powershell -ExecutionPolicy Bypass -File scripts/render-sample.ps1
```

## Preview

```powershell
python -m http.server 4173 --directory ..
```

Open `http://localhost:4173/interactive-newsroom-hero/web/`.

## Unit tests

```powershell
python -m unittest discover -s tests -v
```
```

```gitignore
# .gitignore
output/frames/
output/*.blend
output/*.mp4
output/*.png
web/assets/*.mp4
web/assets/*.png
__pycache__/
```

- [ ] **Step 5: Run the contract tests**

Run:

```powershell
python -m unittest tests.test_scene_config -v
```

Expected: 4 tests pass.

### Task 2: Build and Animate the Original Blender Scene

**Files:**
- Create: `src/build_scene.py`

**Interfaces:**
- Consumes: `RenderSpec` and `A1_ROLE` from `scene_config.py`.
- Produces: `output/frames/frame_0001.png` through `frame_0120.png`, `output/sample-cover.png`, `output/sample-highlight.png`, and `output/sample.blend`.

- [ ] **Step 1: Install Blender through the available Windows package manager**

Run:

```powershell
winget install --id BlenderFoundation.Blender --exact --accept-package-agreements --accept-source-agreements
```

Expected: winget reports a successful Blender 4.x installation. If it reports an existing installation, continue without reinstalling.

- [ ] **Step 2: Create the procedural scene builder**

```python
# src/build_scene.py
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
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=location)
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
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


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
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = SPEC.width
    scene.render.resolution_y = SPEC.height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.world.color = (0.94, 0.94, 0.94)
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
    dark = material("screen body", (0.035, 0.045, 0.055, 1), roughness=0.35)
    red = material("A1 red", A1_ROLE["color"], roughness=0.48)
    screen = material("topic screen", (0.15, 0.52, 0.90, 1), emission=(0.12, 0.42, 1.0, 1))

    cube("base.floor", (0, 0, -0.18), (6.3, 4.2, 0.15), white, 0.22, base)
    cube("interactive.desk.top", (0, 0.25, 1.45), (2.55, 0.95, 0.12), white, 0.10, interactive)
    for x in (-2.15, 2.15):
        cube(f"interactive.desk.leg.{x}", (x, 0.25, 0.68), (0.13, 0.70, 0.70), pale, 0.05, interactive)
    cube("interactive.drawer", (1.82, 0.22, 0.73), (0.48, 0.68, 0.63), pale, 0.08, interactive)
    cube("interactive.monitor", (0, 0.28, 2.55), (1.18, 0.12, 0.72), dark, 0.10, interactive)
    cube("interactive.screen", (0, 0.13, 2.56), (1.02, 0.035, 0.56), screen, 0.04, interactive)
    cube("interactive.monitor.stand", (0, 0.33, 1.83), (0.10, 0.10, 0.30), dark, 0.04, interactive)
    cube("interactive.keyboard", (0, -0.42, 1.63), (0.76, 0.25, 0.05), pale, 0.05, interactive)

    cube("interactive.chair.back", (0, -1.62, 1.13), (0.80, 0.14, 0.72), pale, 0.18, interactive)
    cube("interactive.chair.seat", (0, -1.35, 0.63), (0.72, 0.62, 0.12), pale, 0.14, interactive)
    cube("interactive.chair.post", (0, -1.35, 0.18), (0.10, 0.10, 0.42), dark, 0.04, interactive)

    torso = uv_sphere("interactive.role.torso", (0, -1.16, 1.33), (0.64, 0.46, 0.72), red, interactive)
    head = uv_sphere("interactive.role.head", (0, -1.03, 2.20), (0.47, 0.43, 0.48), white, interactive)
    left_arm = cube("interactive.role.arm.left", (-0.50, -0.76, 1.38), (0.13, 0.48, 0.13), red, 0.12, interactive)
    right_arm = cube("interactive.role.arm.right", (0.50, -0.76, 1.38), (0.13, 0.48, 0.13), red, 0.12, interactive)
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
    keyframe(head, 70, rotation=(math.radians(2), 0, math.radians(-3)))
    keyframe(head, 120, rotation=(math.radians(8), 0, 0))
    for arm, sign in ((left_arm, -1), (right_arm, 1)):
        keyframe(arm, 21, rotation=(math.radians(-24), 0, math.radians(sign * 4)))
        keyframe(arm, 48, rotation=(math.radians(-19), 0, math.radians(sign * 2)))
        keyframe(arm, 74, rotation=(math.radians(-25), 0, math.radians(sign * 5)))
        keyframe(arm, 98, rotation=(math.radians(-20), 0, math.radians(sign * 3)))
        keyframe(arm, 120, rotation=(math.radians(-24), 0, math.radians(sign * 4)))

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
```

- [ ] **Step 3: Render and inspect the source outputs**

Run:

```powershell
$blender = Get-ChildItem "$env:ProgramFiles\Blender Foundation\Blender *\blender.exe" |
  Sort-Object FullName |
  Select-Object -Last 1 -ExpandProperty FullName
& $blender --background --python src/build_scene.py -- "$PWD\output"
```

Expected: Blender exits with code 0 and creates 120 frame PNGs plus cover, highlight, and `.blend` outputs. Inspect `output/sample-cover.png` and confirm the desk, red-clothed role, monitor, chair, white floor, and shadows are visible.

### Task 3: Encode and Validate the Media Contract

**Files:**
- Create: `src/verify_outputs.py`
- Create: `tests/test_verify_outputs.py`
- Create: `scripts/render-sample.ps1`

**Interfaces:**
- Consumes: PNG outputs from Task 2 and FFprobe JSON.
- Produces: validated `output/sample.mp4` and synchronized copies in `web/assets/`.

- [ ] **Step 1: Write failing verifier tests**

```python
# tests/test_verify_outputs.py
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from verify_outputs import validate_probe


class ProbeValidationTests(unittest.TestCase):
    def test_accepts_expected_video(self):
        probe = {
            "streams": [{"width": 1280, "height": 720, "r_frame_rate": "24/1"}],
            "format": {"duration": "5.000000"},
        }
        self.assertEqual(validate_probe(probe), [])

    def test_reports_wrong_duration_and_size(self):
        probe = {
            "streams": [{"width": 640, "height": 360, "r_frame_rate": "30/1"}],
            "format": {"duration": "4.250000"},
        }
        errors = validate_probe(probe)
        self.assertIn("resolution must be 1280x720", errors)
        self.assertIn("frame rate must be 24 fps", errors)
        self.assertIn("duration must be 5.0 seconds", errors)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Confirm the verifier module is missing**

Run:

```powershell
python -m unittest tests.test_verify_outputs -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'verify_outputs'`.

- [ ] **Step 3: Implement media validation**

```python
# src/verify_outputs.py
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

from PIL import Image

from scene_config import OUTPUT_NAMES, RenderSpec


def validate_probe(probe: dict) -> list[str]:
    stream = probe["streams"][0]
    spec = RenderSpec()
    errors = []
    if (stream["width"], stream["height"]) != (spec.width, spec.height):
        errors.append("resolution must be 1280x720")
    if float(Fraction(stream["r_frame_rate"])) != spec.fps:
        errors.append("frame rate must be 24 fps")
    if abs(float(probe["format"]["duration"]) - spec.duration_seconds) > 0.05:
        errors.append("duration must be 5.0 seconds")
    return errors


def probe_video(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=width,height,r_frame_rate:format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def verify(root: Path) -> list[str]:
    spec = RenderSpec()
    errors = []
    video = root / OUTPUT_NAMES["video"]
    cover = root / OUTPUT_NAMES["cover"]
    highlight = root / OUTPUT_NAMES["highlight"]
    for path in (video, cover, highlight):
        if not path.exists():
            errors.append(f"missing output: {path.name}")
    if errors:
        return errors
    errors.extend(validate_probe(probe_video(video)))
    with Image.open(cover) as image:
        if image.size != (spec.width, spec.height):
            errors.append("cover must be 1280x720")
    with Image.open(highlight) as image:
        if image.size != (spec.width, spec.height):
            errors.append("highlight must be 1280x720")
        if image.mode != "RGBA" or image.getextrema()[3][0] == 255:
            errors.append("highlight must contain transparency")
    return errors


if __name__ == "__main__":
    problems = verify(Path(sys.argv[1]))
    if problems:
        print("\n".join(problems), file=sys.stderr)
        raise SystemExit(1)
    print("media verification passed")
```

- [ ] **Step 4: Run verifier unit tests**

Run:

```powershell
python -m unittest tests.test_verify_outputs -v
```

Expected: 2 tests pass.

- [ ] **Step 5: Add the one-command render pipeline**

```powershell
# scripts/render-sample.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$output = Join-Path $root "output"
$frames = Join-Path $output "frames"
$webAssets = Join-Path $root "web\assets"

$blender = Get-ChildItem "$env:ProgramFiles\Blender Foundation\Blender *\blender.exe" |
  Sort-Object FullName |
  Select-Object -Last 1 -ExpandProperty FullName
if (-not $blender) {
  throw "Blender was not found under Program Files."
}

New-Item -ItemType Directory -Force -Path $output, $frames, $webAssets | Out-Null
Remove-Item (Join-Path $frames "frame_*.png") -Force -ErrorAction SilentlyContinue

& $blender --background --python (Join-Path $root "src\build_scene.py") -- $output
if ($LASTEXITCODE -ne 0) { throw "Blender render failed." }

ffmpeg -y -framerate 24 -i (Join-Path $frames "frame_%04d.png") `
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart `
  (Join-Path $output "sample.mp4")
if ($LASTEXITCODE -ne 0) { throw "FFmpeg encoding failed." }

python (Join-Path $root "src\verify_outputs.py") $output
if ($LASTEXITCODE -ne 0) { throw "Output verification failed." }

Copy-Item (Join-Path $output "sample.mp4") $webAssets -Force
Copy-Item (Join-Path $output "sample-cover.png") $webAssets -Force
Copy-Item (Join-Path $output "sample-highlight.png") $webAssets -Force
Write-Output "RENDER_PIPELINE_COMPLETE"
```

- [ ] **Step 6: Run the full render pipeline**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/render-sample.ps1
```

Expected: output ends with `media verification passed` and `RENDER_PIPELINE_COMPLETE`.

### Task 4: Build the One-Desk Interaction Proof

**Files:**
- Create: `web/index.html`
- Create: `web/styles.css`
- Create: `web/app.js`

**Interfaces:**
- Consumes: `web/assets/sample.mp4`, `sample-cover.png`, and `sample-highlight.png`.
- Produces: pointer, touch, keyboard, reduced-motion, video-failure, and navigation behavior for the A1 sample.

- [ ] **Step 1: Create accessible scene markup**

```html
<!-- web/index.html -->
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>智媒编辑部 · 互动场景样片</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <main class="hero" data-scene>
    <video
      class="scene-video"
      data-video
      autoplay
      muted
      playsinline
      poster="assets/sample-cover.png"
      aria-hidden="true"
    >
      <source src="assets/sample.mp4" type="video/mp4">
    </video>
    <img class="highlight" data-highlight src="assets/sample-highlight.png" alt="">
    <svg class="hit-map" viewBox="0 0 1280 720" aria-hidden="true">
      <polygon points="330,235 920,235 1020,570 260,570"></polygon>
    </svg>
    <button
      class="desk-target"
      data-desk
      type="button"
      aria-label="A1 智能选题，策划编辑"
      aria-describedby="role-card"
    ></button>
    <aside class="role-card" id="role-card" data-card aria-live="polite">
      <span>A1 / TOPIC PLANNING</span>
      <h1>智能选题</h1>
      <b>策划编辑</b>
      <p>聚合热点信号，形成可执行的报道方向。</p>
      <em>点击进入模块 →</em>
    </aside>
    <p class="fallback-message" data-fallback>动画未加载，仍可选择工位进入模块。</p>
  </main>
  <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Implement the miniature presentation and hover states**

```css
/* web/styles.css */
:root{color-scheme:light;--red:#c8102e;--ink:#171717}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%;background:#f4f5f5;color:var(--ink);font-family:Inter,"Segoe UI","Microsoft YaHei",sans-serif}
.hero{position:relative;width:100vw;height:100vh;min-height:560px;overflow:hidden;background:#f4f5f5 url("assets/sample-cover.png") center/cover no-repeat}
.scene-video,.highlight,.hit-map{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.scene-video{transition:filter .22s ease}
.highlight{opacity:0;pointer-events:none;transition:opacity .1s ease;filter:drop-shadow(0 18px 30px #c8102e33)}
.hit-map{pointer-events:none}
.hit-map polygon{fill:transparent;stroke:transparent}
.desk-target{position:absolute;left:20%;top:31%;width:61%;height:49%;border:0;background:transparent;cursor:pointer}
.desk-target:focus-visible{outline:3px solid var(--red);outline-offset:-8px}
.role-card{position:absolute;right:5vw;top:12vh;width:min(360px,34vw);padding:22px 24px;background:#ffffffea;border:1px solid #d8d8d8;border-left:5px solid var(--red);box-shadow:0 24px 70px #20252b26;opacity:0;transform:translateY(12px);pointer-events:none;transition:.18s ease}
.role-card span{font:700 11px/1.2 Consolas,monospace;letter-spacing:.15em;color:var(--red)}
.role-card h1{font:700 clamp(28px,3vw,46px)/1.05 Georgia,"Songti SC",serif;margin:10px 0}
.role-card b{font-size:15px}.role-card p{font-size:14px;line-height:1.7;color:#555}.role-card em{font-style:normal;font-size:12px;font-weight:800}
.hero.is-active .scene-video{filter:brightness(.82) saturate(.82)}
.hero.is-active .highlight,.hero.is-active .role-card{opacity:1}
.hero.is-active .role-card{transform:none}
.fallback-message{position:absolute;left:50%;bottom:20px;transform:translateX(-50%);display:none;background:#fff;padding:9px 13px;font-size:12px}
.hero.video-failed .scene-video{display:none}.hero.video-failed .fallback-message{display:block}
@media(max-width:700px){.role-card{left:5vw;right:5vw;top:auto;bottom:5vh;width:auto}.desk-target{left:8%;top:22%;width:84%;height:52%}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}.scene-video{display:none}}
```

- [ ] **Step 3: Implement input, video fallback, and navigation**

```javascript
// web/app.js
(() => {
  const scene = document.querySelector("[data-scene]");
  const desk = document.querySelector("[data-desk]");
  const video = document.querySelector("[data-video]");
  let touchArmed = false;

  const activate = () => scene.classList.add("is-active");
  const deactivate = () => {
    scene.classList.remove("is-active");
    touchArmed = false;
  };
  const navigate = () => {
    window.location.href = "../../demo/pages/m1-topics.html";
  };

  desk.addEventListener("pointerenter", activate);
  desk.addEventListener("pointerleave", event => {
    if (event.pointerType !== "touch") deactivate();
  });
  desk.addEventListener("focus", activate);
  desk.addEventListener("blur", deactivate);
  desk.addEventListener("click", event => {
    if (event.pointerType === "touch" && !touchArmed) {
      event.preventDefault();
      touchArmed = true;
      activate();
      return;
    }
    navigate();
  });
  desk.addEventListener("keydown", event => {
    if (event.key === "Escape") {
      desk.blur();
      deactivate();
    }
  });

  video.addEventListener("ended", () => {
    video.currentTime = 20 / 24;
    video.play().catch(() => {});
  });
  video.addEventListener("error", () => scene.classList.add("video-failed"));
  video.play().catch(() => {
    document.addEventListener("pointerdown", () => video.play().catch(() => {}), {once: true});
  });
})();
```

- [ ] **Step 4: Run the complete automated checks**

Run:

```powershell
python -m unittest discover -s tests -v
python src/verify_outputs.py output
```

Expected: 6 unit tests pass and media verification prints `media verification passed`.

- [ ] **Step 5: Preview and perform the interaction checklist**

Run:

```powershell
python -m http.server 4173 --directory ..
```

Verify at `http://localhost:4173/interactive-newsroom-hero/web/`:

1. Video enters and then repeats the idle section without replaying the camera move.
2. The character remains visible and wears red clothing.
3. Hover starts highlighting within 100 ms.
4. The card shows `A1 智能选题`, `策划编辑`, responsibility copy, and entry prompt.
5. Tab focuses the desk; Escape clears the active state.
6. Touch requires one tap to reveal and a second tap to navigate.
7. Blocking the MP4 request leaves the cover/interaction usable and shows the fallback message.
8. Reduced-motion mode shows the static cover and immediate interaction states.

## Completion Gate

Stop after Task 4 and present the MP4, cover, transparent highlight, and browser proof for visual review. Do not expand to six desks until the user approves the sample’s character shape, lighting, camera, red clothing, and motion quality.
