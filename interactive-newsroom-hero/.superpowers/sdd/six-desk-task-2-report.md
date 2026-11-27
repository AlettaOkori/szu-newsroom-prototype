# Six-Desk Newsroom — Task 2 Report

## Status

Task 2 is implemented and verified with the required pure-Python geometry tests and low-cost Blender preview. The 120-frame full render was not run.

## Files

- Created `src/build_newsroom.py`
  - Import-safe `project_quad(projector, corners)`
  - Six-desk Blender scene, shared role/workstation geometry, role props, animation, camera, lighting, highlight rendering, hit-region projection, preview/full CLI modes
- Created `tests/test_newsroom_geometry.py`
  - Four-point rounding test
  - Off-canvas rejection test
- Created this report
- Did not modify `src/build_scene.py`, `src/scene_config.py`, or sample outputs

## TDD Evidence

Red:

```text
python -m unittest tests.test_newsroom_geometry -v
ModuleNotFoundError: No module named 'build_newsroom'
Ran 1 test
FAILED (errors=1)
```

Green:

```text
python -m unittest tests.test_newsroom_geometry -v
Ran 2 tests in 0.000s
OK
```

Fresh regression run:

```text
python -m unittest discover -s tests -v
Ran 14 tests in 0.170s
OK
```

## Blender Preview and Geometry Results

Command:

```powershell
$blender = Get-ChildItem "$env:ProgramFiles\Blender Foundation\Blender *\blender.exe" |
  Sort-Object FullName |
  Select-Object -Last 1 -ExpandProperty FullName
& $blender --background --python src/build_newsroom.py -- "$PWD\output" --mode preview
```

Final run:

- Blender: `5.2.0 LTS`
- Exit code: `0`
- Elapsed: `40.937s`
- Rendered only frames 1, 21, 70, and 120
- Rendered cover and six isolated transparent highlights
- Wrote six four-point hit regions inside the `1280x720` view box
- Saved `newsroom.blend`
- Did not create `output/newsroom-frames`

Preview review:

- Six unified role silhouettes and six required clothing colors are visible; A2 received a position-only visibility correction without changing its approved dimensions.
- Desks form an irregular ring and leave the center clear.
- Role props and frame-70 screen motifs are present.
- Camera remains the elevated 52 mm view.
- Background is near-white and contact shadows remain readable.
- Frames 21 and 120 are visually equivalent with negligible one-pixel noise.

The first Blender invocation exposed a script-path import failure despite Blender returning exit code 0. The renderer now adds its own `src` directory to `sys.path`; subsequent preview runs completed without a traceback.

## Output Evidence

Automated artifact checks:

```text
newsroom_expected_files 13 of 13
newsroom_nonempty True
image_sizes_ok True
highlight_alpha_ok True
hit_regions_ok True
endpoint_changed_pixels 4 max_channel_delta 1
full_sequence_absent True
sample_outputs_preserved True True True 120
```

Produced:

- `output/newsroom-preview/frame_0001.png`
- `output/newsroom-preview/frame_0021.png`
- `output/newsroom-preview/frame_0070.png`
- `output/newsroom-preview/frame_0120.png`
- `output/newsroom-cover.png`
- `output/newsroom-a1-highlight.png` through `output/newsroom-a6-highlight.png`
- `output/newsroom-hit-regions.json`
- `output/newsroom.blend`

Existing `sample-cover.png`, `sample-highlight.png`, `sample.blend`, and all 120 sample frame PNGs remain present.

## Self-Review

- Scene consumes only the approved `DESKS`, `RenderSpec`, and `NEWSROOM_OUTPUT_NAMES` interfaces.
- Sample renderer code was copied where required and left unchanged.
- Desk collections are named `desk_a1` through `desk_a6`; their objects are parented to desk-location empties.
- Role dimensions are exactly torso `(0.64, 0.46, 0.72)`, head `(0.47, 0.43, 0.48)`, and arm `(0.13, 0.48, 0.13)`.
- Workstation structure is shared across all six desks.
- Entry, breathing, role-action, response-motif, camera, and emission animation endpoints are implemented.
- Desktop hit regions use actual transformed top mesh bounds, not normalized proxy corners.
- Highlight state is restored after every isolated render.
- IDE diagnostics report no errors in the two new Python files.

## Concerns

- Blender 5.2 emits deprecation warnings for `World.use_nodes` and `Material.use_nodes`; these APIs still work and were retained to match the approved sample visual setup.
- Prop recognition was reviewed at preview resolution; final production polish remains appropriately deferred until the later full-render task.
- No Git repository initialization, commit, or full 120-frame newsroom render was performed.

## Review-Fix Evidence — 2026-07-19

The rejected preview was corrected without changing desk locations, the 52 mm
camera, or the shared torso/head/arm dimensions.

Visual fixes:

- Reworked frame-70 response motifs as high-contrast camera-facing displays:
  A1 trend bars, A2 audio waveform, A3 manuscript text lines, A4 marked issue,
  A5 channel tiles, and A6 chart bars.
- Enlarged and separated persistent desktop props from monitor and role
  silhouettes: A1 trend tablet and yellow movable card, A2 orange material
  folder, A3 backed manuscript page with text, A4 checked issue badge, A5
  colored side-channel screens, and A6 chart bars and signal posts.
- Offset A2's monitor and chair around the unchanged shared role geometry so
  its orange torso is clearly visible.
- Preserved the irregular six-desk ring and clear center.

Final preview command:

```powershell
& $blender --background --python src/build_newsroom.py -- "$PWD\output" --mode preview
```

Final Blender evidence:

```text
Blender 5.2.0 LTS
exit_code: 0
elapsed_ms: 51018
frame_0001.png saved
frame_0021.png saved
frame_0070.png saved
frame_0120.png saved
newsroom-cover.png saved
newsroom-a1-highlight.png through newsroom-a6-highlight.png saved
newsroom.blend saved
```

Manual inspection covered the final cover, frame 70, and all six transparent
highlights. Every named prop is visibly separated on its workstation, all six
response motifs are readable at frame 70, and A2's orange clothing is visible
in both the cover and isolated highlight.

Focused geometry tests:

```text
python -m unittest tests.test_newsroom_geometry -v
Ran 2 tests in 0.000s
OK
```

Full Python suite:

```text
python -m unittest discover -s tests -v
Ran 14 tests in 0.180s
OK
```

Final output checks:

```text
newsroom_expected_files 13 of 13
newsroom_nonempty True
image_sizes_ok True
highlight_alpha_ok True
hit_regions_ok True
endpoint_changed_pixels 4 max_channel_delta 1
full_sequence_absent True
sample_outputs_preserved True True True 120
```

Frames 21 and 120 are visually equivalent; only four pixels differ and the
maximum per-channel difference is one level. IDE diagnostics report no linter
errors in `src/build_newsroom.py` or `tests/test_newsroom_geometry.py`.

Review-fix concerns:

- Blender 5.2 still reports the existing `World.use_nodes` and
  `Material.use_nodes` Blender 6.0 deprecation warnings.
- The final 120-frame newsroom render remains intentionally unrun for Task 7.
