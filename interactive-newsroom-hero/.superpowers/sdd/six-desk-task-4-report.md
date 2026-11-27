# Six-Desk Newsroom — Task 4 Review

## Verdict

- **Spec compliance: REJECTED**
- **Quality: REJECTED**

The mode controls and happy-path pipeline order are mostly correct, but the
pipeline can accept stale Blender artifacts after an uncaught Python traceback.
The checked-in documentation also omits required Completion Gate commands.

## Blocking findings

1. **Blender tracebacks are not detected.** Both Blender calls rely only on
   `$LASTEXITCODE`. Blender 5.2.0 was directly probed with an uncaught
   `RuntimeError`: it printed a traceback and returned exit code `0`. The script
   does not pass `--python-exit-code` or inspect Blender output for `Traceback`,
   so a failed scene script can continue into artifact checks and a success
   sentinel.
2. **Preview artifacts are not freshness-gated.** Preview deletes only
   `newsroom-preview/frame_*.png`; it leaves the cover, six highlights,
   hit-region JSON, Blend source, and generated JavaScript in place. If Blender
   renders the four frames and then raises, old top-level artifacts can satisfy
   `Assert-SceneArtifacts`, allowing `NEWSROOM_PREVIEW_COMPLETE` for a mixed
   run.
3. **Fresh full cleanup misses the Blend source.** The cleanup filter
   `newsroom-*` does not match `newsroom.blend`, so a stale Blend can satisfy the
   full artifact gate. Blender also leaves `newsroom.blend1`; it is neither
   cleaned nor ignored by `output/newsroom-*` or `output/*.blend`.
4. **The A2 color failure is a real upstream blocker before Task 7.** The
   preview cover and full cover are both frame 21. Against the verifier's
   required minimum of 100 matching pixels, A2 has 0 in the cover, 1 in frame
   1, and 0 in frames 21, 70, and 120. Therefore the eventual full pipeline
   will fail complete-scene verification unless the renderer/color-management
   output or the approved verifier criterion is corrected before paying for
   the 120-frame render.
5. **README does not contain all exact Completion Gate commands.** It omits the
   specified `python -m py_compile ...` command, direct `ffprobe` command, and
   six-desk browser-smoke syntax/execution commands. The present static README
   test checks only a subset of required phrases.

## Compliant areas

- `-PreviewOnly` and `-SkipRender` are mutually exclusive.
- Preview requests frames 1, 21, 70, and 120 and does not invoke FFmpeg.
- Full mode requests exactly 120 contiguous names; `-SkipRender` does not invoke
  Blender and rejects the current incomplete sequence before encoding.
- The full happy path is ordered encode → config generation/Node check →
  newsroom verification → asset copy/SHA-256 comparison → success sentinel.
- Cleanup is scoped away from `sample.*` and `output/frames/`. The four recorded
  sample hashes still match, and all 120 sample frames remain present.
- The required newsroom ignore rules were added without removing existing
  sample rules.

## Review evidence

- Inspected the complete script, README, ignore file, verifier dispatch/tests,
  all four preview frames, cover, six highlights, projection JSON, and artifact
  inventory.
- `python -m unittest tests.test_render_newsroom_pipeline
  tests.test_verify_outputs -v`: 20 tests passed.
- `python src/verify_outputs.py output --newsroom`: failed for missing full
  media/frames and the A2 clothing-color criterion, as expected for the current
  preview-only state.
- No full render was run.

## Implementation status recorded before review

The mandatory preview completed. The final expensive 120-frame newsroom render
was not run. `-SkipRender` was exercised against the current incomplete
`output/newsroom-frames/` directory and stopped before encoding, as designed.

## Changed files

- Created `scripts/render-newsroom.ps1`.
- Added newsroom-only generated artifact rules to `.gitignore` without removing
  the sample rules.
- Updated `README.md` with the preserved sample command, Blender version,
  preview/full costs, `-SkipRender`, output inventory, all six destinations,
  preview server, and Completion Gate commands.
- Added `tests/test_render_newsroom_pipeline.py`.
- Added focused newsroom CLI dispatch coverage to
  `tests/test_verify_outputs.py`.
- Updated `src/verify_outputs.py` so the required `--newsroom` command actually
  calls `validate_newsroom` instead of silently verifying sample outputs.

No Git repository was initialized and no commit was created.

## TDD evidence

Initial command:

```powershell
python -m unittest tests.test_render_newsroom_pipeline -v
```

Result before implementation: exit `1`; four tests failed/errored because
`render-newsroom.ps1`, the ignore rules, and the README contract did not exist.

After implementation, the same command exited `0` with four passing tests.

The verifier integration defect was also reproduced before its fix:

```powershell
python -m unittest tests.test_verify_outputs.NewsroomValidationTests.test_newsroom_cli_selects_complete_scene_verification -v
```

Red result: exit `1`; `--newsroom` emitted sample errors such as
`missing output: sample.mp4`. Green result after minimal CLI dispatch: exit `0`.

## Preview exercise

Command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1 -PreviewOnly
```

Result: exit `0` in about 49 seconds, ending in:

```text
NEWSROOM_PREVIEW_COMPLETE
```

Artifact gate result:

```text
preview artifact gate passed: 4 frames, 7 stills, JSON, Blend, no MP4
```

The preview produced frames 1, 21, 70, and 120, one cover, six transparent
highlights, projection JSON, `web/scene-data.js`, and `newsroom.blend`.

## Cost-control and verification exercises

Mutually exclusive mode coverage ran through the unit test and confirmed that
`-PreviewOnly -SkipRender` fails before dependency checks with:

```text
PreviewOnly and SkipRender cannot be combined.
```

Command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1 -SkipRender
```

Expected result with no complete full frame sequence: exit `1` before FFmpeg:

```text
Expected 120 contiguous newsroom frames in ...\output\newsroom-frames.
```

This confirms that `-SkipRender` does not start Blender and cannot encode a
partial or stale sequence.

Sample regression verification:

```powershell
python src/verify_outputs.py output
```

Result: exit `0`, `media verification passed`.

The preserved sample hashes still match the previously recorded final hashes:

```text
sample.mp4           F38BAC8366C715AD1B5C38E8BA57A918C7E4C430020B3F1699170A055F2124BB
sample-cover.png     2A518399E74A6C71FED2E49FF33AFEA2D00F2D45C9D7831F09FFEC8990AA71C8
sample-highlight.png EFC0F2574918828AAEF0F743B8DB11E5845A56D28D3DE64B93FEADB601D84C46
sample.blend         ECFCA96D56248EA75F478DA4AD8D4FCE2352CB884A3B1E3BA84EFE9DF9F93627
```

All 120 sample frames remain present. Their latest modification time is
`2026-07-19T03:17:33.8811171+08:00`; sample top-level artifacts remain dated
between `03:17:39` and `03:17:44`, before this Task 4 preview run.

## Final test results

```powershell
python -m unittest discover -s tests -v
```

Result: exit `0`; `Ran 32 tests in 27.646s`, `OK`.

```powershell
node --check web/scene-data.js
node --check web/app.js
```

Both commands exited `0` with no output. IDE diagnostics reported no lint
errors in the edited PowerShell, Python, and test files.

## Concerns and boundary

- The reserved 120-frame render was intentionally not executed, so full FFmpeg
  encoding, SHA-256 web synchronization, and the success sentinel
  `NEWSROOM_PIPELINE_COMPLETE` remain unexercised until Task 7.
- Running `python src/verify_outputs.py output --newsroom` against preview-only
  artifacts correctly exits `1` for the missing MP4 and full-frame sequence.
  It also reports
  `newsroom-cover.png: a2: cover must contain visible clothing-color evidence`.
  Preview and full mode generate the cover from the same frame, so the current
  renderer/verifier pair may reject the eventual full render on A2 color
  evidence. This is an upstream scene/verifier acceptance concern; Task 4 did
  not alter approved scene geometry, materials, or verifier thresholds.

## Authoritative Fix Evidence — Supersedes Rejected Review

This section supersedes the rejected verdict and all earlier implementation
status and concern sections above. The five blocking findings from the review
were fixed and verified without running the reserved full render.

### Blender failure and freshness gates

Both Blender branches now run with `--python-exit-code 1`. Blender stdout and
stderr are captured through `System.Diagnostics.Process`, preserving normal
warnings without allowing PowerShell 5 to convert stderr into a terminating
`NativeCommandError`. The gate rejects either a nonzero process exit or
`Traceback (most recent call last)` in captured output.

Before preview, the pipeline removes preview frames, cover, all six highlights,
hit JSON, `newsroom.blend`, `newsroom.blend1`, and `web/scene-data.js`.
Nonempty frames and top-level artifacts are required after Blender returns.
Fresh full mode explicitly removes `newsroom.blend`, `newsroom.blend1`, and
generated scene data in addition to its existing `newsroom-*` cleanup.
Sample files and `output/frames/` are never part of either cleanup set.

The focused integration test creates four fresh frame names, stale top-level
newsroom artifacts, stale Blend/backup/config files, and preserved sample
markers, then runs a temporary Blender script that raises `RuntimeError`.
Before the fix, this command exited `0` and reached
`NEWSROOM_PREVIEW_COMPLETE`. After the fix:

```powershell
python -m unittest tests.test_render_newsroom_pipeline -v
```

Result: five tests passed. The injected traceback exits nonzero, no success
sentinel is printed, all stale preview artifacts are absent, and both sample
markers remain byte-identical.

`.gitignore` now includes `output/newsroom.blend1` while retaining all existing
sample ignore rules.

### A2 renderer-level correction

The approved A2 config remains `#e87524ff`; role geometry and dimensions are
unchanged. Only the A2 clothing material render inputs were compensated for
AgX/light desaturation: its render base is more saturated and a low-strength,
red-dominant emission restores visible orange evidence. The final cover visibly
remains orange.

The final preview command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1 -PreviewOnly
```

Result: exit `0` in about 42 seconds, ending in
`NEWSROOM_PREVIEW_COMPLETE`.

The new preview-only verifier mode does not require an encoded MP4:

```powershell
python src/verify_outputs.py output --newsroom --preview
```

Result: exit `0`, `newsroom preview verification passed`.

All configured colors exceed the required 100-pixel evidence floor in the
cover and every representative frame. Counts by A1–A6 were:

```text
cover:      608, 770, 4188, 2051, 1557, 2188
frame 1:    410, 558, 2785, 1391, 1071, 1490
frame 21:   608, 770, 4188, 2051, 1557, 2188
frame 70:   601, 729, 8712, 2280, 2243, 2423
frame 120:  608, 770, 4188, 2051, 1557, 2188
```

### Documentation and final checks

`README.md` now contains the exact Completion Gate commands for:

- full unittest discovery and Python `py_compile`;
- generated scene data, app, sample smoke, and six-desk smoke Node syntax;
- preview, sample, and complete newsroom verification;
- direct `ffprobe` with all required stream/format fields;
- parent-directory HTTP server plus sample and six-desk Edge smoke execution.

Static pipeline tests require these exact command strings.

Final verification:

```text
python -m unittest discover -s tests -v
Ran 36 tests in 52.456s
OK

python -m py_compile src/scene_config.py src/build_scene.py src/build_newsroom.py src/export_web_config.py src/verify_outputs.py
exit 0, silent

node --check web/scene-data.js
node --check web/app.js
node --check .superpowers/sdd/task4-browser-smoke.mjs
all exit 0, silent

python src/verify_outputs.py output
media verification passed
```

IDE diagnostics reported no lint errors in all edited PowerShell, Python, and
test files.

The four authoritative sample SHA-256 values remain unchanged:

```text
sample.mp4           F38BAC8366C715AD1B5C38E8BA57A918C7E4C430020B3F1699170A055F2124BB
sample-cover.png     2A518399E74A6C71FED2E49FF33AFEA2D00F2D45C9D7831F09FFEC8990AA71C8
sample-highlight.png EFC0F2574918828AAEF0F743B8DB11E5845A56D28D3DE64B93FEADB601D84C46
sample.blend         ECFCA96D56248EA75F478DA4AD8D4FCE2352CB884A3B1E3BA84EFE9DF9F93627
```

All 120 sample frames remain present.

### Remaining boundary

No full 120-frame newsroom render, MP4 encode, direct newsroom MP4 probe, web
asset synchronization, or full success sentinel was executed. Those remain
reserved for Task 7. The documented
`.superpowers/sdd/six-desk-browser-smoke.mjs` command cannot be syntax-checked
or executed yet because that later-task artifact is not present in the current
Task 1–4 workspace.
