# Task 3 Report: Encode and Validate the Media Contract

## Status

DONE

## Files changed

- Created `src/verify_outputs.py`: FFprobe contract validation plus cover/highlight validation.
- Created `tests/test_verify_outputs.py`: expected-video and invalid-video unit tests.
- Created `scripts/render-sample.ps1`: one-command Blender render, artifact gate, FFmpeg encode, verification, and web asset synchronization.
- Created `.superpowers/sdd/task-3-report.md`: this evidence report.
- Generated/refreshed `output/sample.mp4` and synchronized all three media assets under `web/assets/`.

## TDD evidence

### Red

Command:

`python -m unittest tests.test_verify_outputs -v`

Result before implementation: exit code 1. Importing the new test module failed with the expected:

`ModuleNotFoundError: No module named 'verify_outputs'`

### Green

The same command after implementing `src/verify_outputs.py` exited 0:

- `test_accepts_expected_video ... ok`
- `test_reports_wrong_duration_and_size ... ok`
- `Ran 2 tests`
- `OK`

Final project test command:

`python -m unittest tests.test_scene_config tests.test_verify_outputs -v`

Result: exit code 0, 6 tests run, all passed.

## Encoding and probe results

The full pipeline encoded all 120 PNG frames with FFmpeg 8.1.1 and libx264 using `-preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart`.

FFmpeg final result:

- Frames: 120
- Encoded size: 271 KiB (`277207` bytes by FFprobe)
- Final timestamp: `00:00:04.91`
- Reported mux bitrate: `451.0 kbits/s`
- x264 video bitrate: `438.73 kb/s`

Exact FFprobe contract result:

- Codec: `h264`
- Pixel format: `yuv420p`
- Resolution: `1280x720`
- Frame rate: `24/1`
- Frame count: `120`
- Duration: `5.000000`
- File size: `277207` bytes

Direct verification command:

`python src/verify_outputs.py output`

Result: exit code 0, `media verification passed`.

Still and frame checks:

- Frames: 120, from `frame_0001.png` through `frame_0120.png`
- Cover: `(1280, 720)`, RGBA
- Highlight: `(1280, 720)`, RGBA, minimum alpha `0`

Synchronized output/web hashes:

- `sample.mp4`: `3b45a105cc4f41add3bbe2c668f09d0a8972020844226f8fe4d313abf4b03ccf`
- `sample-cover.png`: `fedce84b489767dbb528cae74849d0a2979214784cceac154de99a54ea56ea66`
- `sample-highlight.png`: `dc772516cf748e00bbdcec38c9c75db5f573cfc7a9afcea116f20ad94cb1b59d`

Each output hash exactly matched its `web/assets/` copy.

## Pipeline result

Command:

`powershell -ExecutionPolicy Bypass -File scripts/render-sample.ps1`

Result: exit code 0 after 534099 ms. Output ended with:

- `media verification passed`
- `RENDER_PIPELINE_COMPLETE`

The wrapper deletes prior render outputs before invoking Blender, then requires exactly the complete `frame_0001.png` through `frame_0120.png` sequence and non-empty cover/highlight files before encoding. This catches Blender Python tracebacks that may still leave a zero process exit code.

## Self-review

- The verifier consumes the existing `OUTPUT_NAMES` and `RenderSpec` interfaces rather than duplicating output names or media dimensions in its file lookup logic.
- Duration tolerance is the specified 0.05 seconds, and frame rate parsing supports rational FFprobe values.
- Missing outputs are reported together before attempting FFprobe or Pillow reads.
- Web assets are copied only after encoding and verification succeed.
- Script changes are limited to the Task 3 pipeline and artifact-integrity requirement.
- Linter diagnostics reported no errors for the three implementation files.

## Concerns

No Task 3 correctness concerns. Blender 5.2 emitted a non-blocking deprecation warning that `Material.use_nodes` is expected to be removed in Blender 6.0; this originates in the approved Task 2 scene builder and did not affect rendering or verification.
