# Task 2 Report: Build and Animate the Original Blender Scene

## Status

DONE_WITH_CONCERNS

The procedural Blender scene was built and rendered successfully. The required
120 animation frames, cover image, transparent highlight image, and `.blend`
source file are present.

## Files changed

- Created `src/build_scene.py`.
- Created `.superpowers/sdd/task-2-report.md`.

Generated render artifacts:

- `output/frames/frame_0001.png` through
  `output/frames/frame_0120.png`
- `output/sample-cover.png`
- `output/sample-highlight.png`
- `output/sample.blend`

No Git repository was initialized and no commit was created.

## Blender installation

Command:

```powershell
winget install --id BlenderFoundation.Blender --exact --accept-package-agreements --accept-source-agreements
```

Result:

- Exit code: `0`
- winget selected and successfully installed Blender `5.2.0 LTS`.
- Installed build hash: `fbe6228777e7`
- Platform: Windows release build
- The plan expected Blender 4.x, but the current winget package was Blender
  5.2.0 LTS.

## Scene implementation

`src/build_scene.py` consumes `RenderSpec` and `A1_ROLE` from
`src/scene_config.py`. It procedurally creates:

- a white floor and white desk;
- a monitor with a blue emissive screen;
- a keyboard, drawer, and chair;
- an A1-red role figure with animated torso, head, and arms;
- an animated camera entrance ending at frame 20;
- area-key and fill lighting;
- a full animation render, cover still, transparent highlight still, and
  saved Blender source.

The only Blender-version compatibility change from the plan's source listing
was changing the Eevee engine identifier from `BLENDER_EEVEE_NEXT` to
`BLENDER_EEVEE`. Blender 5.2 explicitly rejected the former and listed the
latter as its supported Eevee enum. This preserves the required Eevee renderer.

## Exact render command and results

Command used for both attempts:

```powershell
$blender = Get-ChildItem "$env:ProgramFiles\Blender Foundation\Blender *\blender.exe" |
  Sort-Object FullName |
  Select-Object -Last 1 -ExpandProperty FullName
& $blender --background --python src/build_scene.py -- "$PWD\output"
```

### Attempt 1

- Process exit code: `0`
- Blender's Python script failed before rendering with:
  `TypeError: enum "BLENDER_EEVEE_NEXT" not found in
  ('BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES')`.
- Blender returned process code 0 despite the Python traceback, so the log was
  inspected rather than relying on the process code alone.
- The engine identifier was updated to Blender 5.2's supported
  `BLENDER_EEVEE`.

### Attempt 2

- Process exit code: `0`
- Elapsed time: `609351 ms` (about 10 minutes 9 seconds)
- Blender logged successful saves for frame 0001 through frame 0120,
  `sample-cover.png`, `sample-highlight.png`, and `sample.blend`.
- Blender exited without a traceback.
- One non-fatal deprecation warning was emitted for `Material.use_nodes`,
  which Blender says is expected to be removed in Blender 6.0.

## Output verification

FFprobe was run against the numbered image sequence:

```powershell
ffprobe -v error -f image2 -start_number 1 `
  -i "output\frames\frame_%04d.png" -count_frames `
  -show_entries stream=nb_read_frames,width,height,pix_fmt -of json
```

Result:

- Frame count: `120`
- Frame dimensions: `1280 x 720`
- Frame pixel format: `rgba`

FFprobe results for both still images:

- `output/sample-cover.png`: `1280 x 720`, `rgba`
- `output/sample-highlight.png`: `1280 x 720`, `rgba`

An FFmpeg alpha-channel signal check on `sample-highlight.png` reported alpha
values from `0` to `255`, confirming that the highlight contains transparent
and opaque regions.

Visual inspection of `sample-cover.png` confirmed:

- the desk is visible;
- the A1-red-clothed role is visible;
- the monitor and blue screen are visible;
- the chair is visible;
- the white floor is visible;
- cast and contact shadows are visible.

Visual inspection of `sample-highlight.png` confirmed that the floor is
excluded while the interactive desk, role, monitor, keyboard, drawer, and
chair remain visible on transparency.

## Self-review

- The implementation stays within Task 2's requested scope.
- `RenderSpec` controls frames, FPS, and 1280-by-720 output dimensions.
- `A1_ROLE["color"]` supplies the role material color.
- Object and collection names preserve the required `base` and `interactive`
  organization.
- Required camera and role animation keyframes are present.
- All required files were rendered and independently counted/inspected.
- IDE lint inspection reported no errors for `src/build_scene.py`.
- No project files outside the project root were changed; the only external
  change was the required system Blender installation.

## Concerns

1. winget installed Blender 5.2.0 LTS rather than the plan's expected Blender
   4.x. The script was rendered end-to-end under 5.2 after the Eevee enum
   compatibility adjustment.
2. Blender 5.2 emits a non-fatal warning that `Material.use_nodes` is expected
   to be removed in Blender 6.0. It works in the installed version and was
   retained to preserve the prescribed implementation.
3. Blender may return process exit code 0 even when a background Python script
   raises an exception. Future automation should inspect Blender output or
   additionally verify expected artifacts, as done here.
