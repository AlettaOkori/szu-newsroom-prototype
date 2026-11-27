# Six-Desk Newsroom Task 1 Report

## Status

DONE_WITH_CONCERNS

## Files changed

- Modified `src/scene_config.py` to add the frozen `DeskSpec` contract, six immutable `DESKS`, newsroom output names, hit-region name, and `validate_desks()`.
- Modified `tests/test_scene_config.py` to add the three specified six-desk contract tests while retaining all four sample tests.
- Created `.superpowers/sdd/six-desk-task-1-report.md`.

No Git repository was initialized and no commit was created.

## TDD evidence

### Red

Command:

```powershell
python -m unittest tests.test_scene_config -v
```

Result before implementation:

- Exit code: `1`
- `Ran 1 test in 0.000s`
- `FAILED (errors=1)`
- Expected missing-contract cause observed: `ImportError: cannot import name 'DESKS' from 'scene_config'`

### Green

Command:

```powershell
python -m unittest tests.test_scene_config -v
```

Result after implementation:

- Exit code: `0`
- `Ran 7 tests in 0.000s`
- `OK`

## Exact tests

Focused suite:

- `test_sample_is_exactly_five_seconds`
- `test_sample_uses_hd_canvas`
- `test_a1_role_contract`
- `test_required_outputs_are_named`
- `test_six_desk_contract`
- `test_each_desk_has_role_specific_action_and_props`
- `test_newsroom_outputs_do_not_replace_sample_outputs`

Regression command:

```powershell
python -m unittest discover -s tests -v
```

Result:

- Exit code: `0`
- `Ran 12 tests in 0.169s`
- `OK`

IDE diagnostics reported no linter errors in either modified Python file.

## Self-review

- Preserved `RenderSpec`, `A1_ROLE`, `OUTPUT_NAMES`, and `rgba_hex()` unchanged.
- Confirmed `DeskSpec` is frozen and declares all 13 required fields in the specified order.
- Confirmed `DESKS` contains ordered IDs `a1` through `a6` and exact modules, roles, colors, destinations, actions, props, placements, rotations, and card sides.
- Confirmed newsroom outputs are additive and do not replace the approved sample outputs.
- Confirmed `validate_desks(DESKS)` returns no errors and checks IDs, unique colors, unique destinations, card sides, and minimum prop counts.
- Kept changes limited to the exact Task 1 production and test files plus this required report.

## Concerns

- The plan says the four existing tests should pass during the red run while the new tests fail with an import error. Because `DESKS` is imported at module scope exactly as specified, Python cannot load the test module, so unittest reports one import error and does not execute the existing four tests. The observed failure is still the specified missing-`DESKS` failure, and all seven focused tests pass after implementation.
