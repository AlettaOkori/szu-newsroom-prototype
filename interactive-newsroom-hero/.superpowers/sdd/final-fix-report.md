# Final Whole-Project Fix Report

## Status

DONE_WITH_CONCERNS

All Important findings were fixed within the one-desk A1 Completion Gate. No
Git repository was initialized and no commit was created.

## Changed files

- `src/build_scene.py`
  - Detects `BLENDER_EEVEE_NEXT` first and falls back to `BLENDER_EEVEE`.
  - Builds explicit World nodes. Camera rays use a strong white background,
    while non-camera rays retain the low-strength gray environment so the
    character, desk, and contact shadows are not washed out.
  - Enlarges the white floor to keep the miniature presentation continuous.
- `src/verify_outputs.py`
  - Uses FFprobe decoded-frame counting and validates H.264, `yuv420p`,
    1280x720, 24 fps, 120 decoded frames, and five-second duration.
  - Requires both transparent and visible highlight alpha.
  - Validates near-white upper-background samples plus visible shadow and red
    clothing evidence in the cover and frames 1, 21, 70, and 120.
- `tests/test_verify_outputs.py`
  - Adds negative tests for codec, pixel format, decoded frame count,
    all-transparent/all-opaque highlights, dark backgrounds, missing shadows,
    and missing red clothing.
- `web/app.js`
  - Avoids starting video in reduced-motion mode, pauses it when that preference
    becomes active, and prevents idle-loop restart while reduced motion applies.
- `.superpowers/sdd/task4-browser-smoke.mjs`
  - Supports `EDGE_EXECUTABLE` and `EDGE_DEBUG_PORT`.
  - Requires reduced-motion playback to be paused.
- `README.md`
  - Records tested Blender 5.2.0 LTS, generated outputs and synchronization,
    A1 destination, smoke prerequisites/command/configuration, and the explicit
    one-desk boundary.
- Regenerated `output/frames/frame_0001.png` through `frame_0120.png`,
  `output/sample.mp4`, `output/sample-cover.png`,
  `output/sample-highlight.png`, `output/sample.blend`, and synchronized
  `web/assets/` media.
- Created `.superpowers/sdd/final-fix-report.md`.

## Regression-first evidence

- `python -m unittest tests.test_verify_outputs -v`
  - Before implementation: exit 1 because `validate_cover` and
    `validate_highlight` did not exist.
  - After implementation: 5 verifier tests passed.
- `node .superpowers\sdd\task4-browser-smoke.mjs`
  - Before the playback change: exit 1 with
    `Error: reduced-motion static mode failed`.
  - After the change: reduced-motion video-paused assertion passed.
- Blender one-frame compatibility probe
  - First runtime-detection attempt exposed a `KeyError` because the engine RNA
    was read from `scene` rather than `scene.render`; the corrected lookup
    rendered successfully in Blender 5.2.0 LTS.
- `python src\verify_outputs.py output`
  - The tightened upper-edge grid rejected the first regenerated set with
    `frame_0001.png: cover background samples must be near-white`.
  - Replacing the finite backdrop edge with camera-ray-specific white World
    nodes made entry and idle previews pass before the final 120-frame rerender.

## Final commands and results

### Full render pipeline

Command:

`powershell -ExecutionPolicy Bypass -File scripts\render-sample.ps1`

Result: exit 0 after rendering all 120 frames, cover, highlight, and Blend
source; FFmpeg encoded the MP4; output ended with:

```text
media verification passed
RENDER_PIPELINE_COMPLETE
```

Blender reported `5.2.0 LTS`. FFmpeg reported `8.1.1`.

### Python tests, media verifier, and syntax

Commands:

```text
python -m unittest discover -s tests -v
python src\verify_outputs.py output
python -m py_compile src\scene_config.py src\build_scene.py src\verify_outputs.py tests\test_scene_config.py tests\test_verify_outputs.py
node --check web\app.js
node --check .superpowers\sdd\task4-browser-smoke.mjs
```

Result: exit 0; 9 tests passed; `media verification passed`; Python compilation
and both Node syntax checks emitted no errors.

### Browser smoke

Command:

`$env:EDGE_EXECUTABLE='C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'; $env:EDGE_DEBUG_PORT='9333'; node .superpowers\sdd\task4-browser-smoke.mjs`

Result: exit 0. It verified 1280x720/5.000-second media, native-link
semantics, idle restart, red clothing, 100 ms highlight, A1 copy, keyboard,
two-tap touch navigation to `/demo/pages/m1-topics.html`, real blocked-MP4
fallback, paused reduced-motion mode, autoplay recovery, and idle seeking.

### FFprobe

Command:

`ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=codec_name,pix_fmt,width,height,r_frame_rate,nb_read_frames:format=duration -of json output\sample.mp4`

Result:

```text
codec_name=h264
pix_fmt=yuv420p
width=1280
height=720
r_frame_rate=24/1
nb_read_frames=120
duration=5.000000
```

### Pixel and alpha evidence

The verifier samples 19 points across both upper edges and validates scene
evidence over the complete image:

```text
sample-cover.png: background_min=238 background_range=(238,238,238)..(239,239,239) shadows=657163 red=6968
frame_0001.png: background_min=238 background_range=(238,238,238)..(239,239,239) shadows=651200 red=5337
frame_0021.png: background_min=238 background_range=(238,238,238)..(239,239,239) shadows=657163 red=6968
frame_0070.png: background_min=238 background_range=(238,238,238)..(239,239,239) shadows=657031 red=7290
frame_0120.png: background_min=238 background_range=(238,238,238)..(239,239,239) shadows=657163 red=6968
highlight: alpha_extrema=(0,255) transparent=734052 visible=187548
```

The final cover and highlight were also visually inspected. The background has
no dark upper-corner or upper-edge gap; contact shadows remain visible and the
character remains red.

### Lints

Cursor diagnostics were read for all changed Python and JavaScript files:
`No linter errors found.`

## Final media SHA-256 hashes

```text
output/sample.mp4
F38BAC8366C715AD1B5C38E8BA57A918C7E4C430020B3F1699170A055F2124BB

output/sample-cover.png
2A518399E74A6C71FED2E49FF33AFEA2D00F2D45C9D7831F09FFEC8990AA71C8

output/sample-highlight.png
EFC0F2574918828AAEF0F743B8DB11E5845A56D28D3DE64B93FEADB601D84C46

output/sample.blend
ECFCA96D56248EA75F478DA4AD8D4FCE2352CB884A3B1E3BA84EFE9DF9F93627
```

The three corresponding `web/assets/` hashes exactly match the output MP4,
cover, and highlight. The frame directory contains exactly 120 PNGs.

## Self-review

- Every change maps to an Important finding or the requested low-risk minors.
- Verification now checks decoded media properties rather than trusting encoder
  arguments or container frame metadata.
- The white camera background is isolated from scene illumination, preserving
  the existing model contrast and shadows.
- The highlight contract rejects both fully opaque and fully transparent files.
- Reduced-motion behavior changes actual playback, not only CSS visibility.
- Edge configuration is environment-based and the non-default port was used in
  the final smoke run.
- Scope remains one A1 desk. No A2-A6 content or six-desk expansion was added.

## Concerns

- Blender 4.x was not installed on this machine, so the
  `BLENDER_EEVEE_NEXT` branch is implemented through runtime enum discovery but
  was not executed here; the `BLENDER_EEVEE` branch was executed on Blender
  5.2.0 LTS.
- Blender 5.2 emits deprecation warnings that `World.use_nodes` and
  `Material.use_nodes` are expected to be removed in Blender 6.0. They do not
  affect this tested 5.2 render, but Blender 6 will require an API update.
- Physical touchscreen feel, subjective loop-seam judgment, and non-Chromium
  browser polish remain manual checks.
