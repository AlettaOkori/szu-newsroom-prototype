# Task 1 Report: Lock the Render Contract

## Status

DONE

## Files changed

- Created `.gitignore` with exclusions for generated frames, Blender files, videos, images, web assets, and Python bytecode caches.
- Created `README.md` with project purpose, tool requirements, render command, preview instructions, and unit-test command.
- Created `src/scene_config.py` with the frozen `RenderSpec` data class, `A1_ROLE`, `OUTPUT_NAMES`, and `rgba_hex()`.
- Created `tests/test_scene_config.py` with the four render-contract tests specified by Task 1.
- Created this report at `.superpowers/sdd/task-1-report.md`.

No files outside the project root were changed. Git was not initialized and no commit was created.

## TDD record

### Red

Command:

```powershell
python -m unittest tests.test_scene_config -v
```

Result before `src/scene_config.py` existed:

- Exit code: `1`
- `Ran 1 test in 0.000s`
- `FAILED (errors=1)`
- Expected cause observed: `ModuleNotFoundError: No module named 'scene_config'`

### Green

Command:

```powershell
python -m unittest tests.test_scene_config -v
```

Result after implementation:

- Exit code: `0`
- `Ran 4 tests in 0.000s`
- `OK`
- All four contract tests passed.

## Additional verification

Command:

```powershell
python -m unittest discover -s tests -v
```

Result:

- Exit code: `0`
- `Ran 4 tests in 0.000s`
- `OK`

IDE diagnostics for `src/scene_config.py` and `tests/test_scene_config.py` reported no linter errors.

## Self-review

- Confirmed `RenderSpec` is frozen and has the exact required defaults: 24 fps, frames 1-120, 1280x720, entry ending at frame 20, and idle beginning at frame 21.
- Confirmed `duration_seconds` evaluates to `5.0`.
- Confirmed the A1 module name, role, responsibility, and RGBA color match the Task 1 contract.
- Confirmed `rgba_hex(A1_ROLE["color"])` produces `#c8102eff`.
- Confirmed all three required output filenames match exactly.
- Confirmed README instructions and generated-file exclusions match the Task 1 requirements.
- Confirmed implementation is limited to the requested contract without speculative features.

## Concerns

None.
