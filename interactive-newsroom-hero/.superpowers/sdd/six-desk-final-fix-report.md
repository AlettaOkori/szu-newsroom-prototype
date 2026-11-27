# Six-Desk Final Whole-Project Fix Report

## Superseded status

The status and evidence below are superseded by the authoritative final
re-review section appended at the end.

Correction: the earlier statement that no Blender command was run was
inaccurate. The prior pipeline tests resolved and started the installed Blender
executable for preview, repair, and artifacts scenarios, although they used
stub scene scripts and did not perform a production media rerender. Those tests
are now hermetic.

The project is not a Git repository, so no commit was created.

## Surgical changes

- `web/index.html`
  - Replaced the sample title with
    `智媒编辑部 · 六工位互动新闻编辑部`.
  - Embedded the six generated, distinct four-point desk polygons directly in
    the native SVG links.
- `web/app.js`
  - Validates all configured polygon strings, bounds, nonzero areas,
    distinctness, and destinations before making any DOM mutation.
  - Missing, unsafe, duplicate, or malformed configuration therefore leaves
    all static polygons and native destinations intact.
- `.superpowers/sdd/six-desk-browser-smoke.mjs`
  - Requires unchanged fallback points, four native SVG points, focusability,
    and destinations for missing, duplicate, unsafe, and malformed-polygon
    configuration.
- `src/verify_outputs.py`
  - Keeps the sample verification path unchanged.
  - Requires six pairwise-distinct newsroom highlight pixel contents.
  - Requires at least 100 visible pixels within RGB Euclidean distance 65 of
    each configured clothing color.
  - Requires at least 80% visible-alpha coverage of the matching projected
    desk polygon and alpha of at least 200 at its centroid.
- `scripts/render-newsroom.ps1`
  - Runs `src/verify_frame_content.py output/newsroom-frames` after complete
    media verification and before synchronization or
    `NEWSROOM_PIPELINE_COMPLETE`.
  - Parses bounded repair selections before Blender, deletes only requested
    frame targets, and requires each target to be recreated nonempty.
  - Deletes only intended scene artifacts before `-ArtifactsOnly` or
    artifact-regenerating repair, then requires fresh nonempty outputs.
- Tests add static fallback/title assertions; duplicate, swapped-color, and
  displaced-highlight negatives; a failing frame-content pipeline gate; and
  repair/artifact no-write stale-output regressions.

## Regression-first evidence

Before implementation, the focused web/highlight test run failed on the old
sample title and empty static polygon points. The four new highlight calls
failed because the old verifier had no projected-region input.

Before the PowerShell changes, all four focused pipeline regressions failed:

- the script lacked `src\verify_frame_content.py`;
- the failing frame verifier still allowed exit 0 and the success sentinel;
- stale requested repair frames passed when Blender wrote nothing;
- stale artifacts passed `-ArtifactsOnly` when Blender wrote nothing.

After implementation, those four focused pipeline tests passed in 5.715
seconds. The complete suite then passed all 52 tests in 59.881 seconds.

## Final verifier evidence

All commands exited 0:

```text
python -m unittest discover -s tests -v
  Ran 52 tests in 59.881s — OK

python src/verify_outputs.py output
  media verification passed

python src/verify_outputs.py output --newsroom
  newsroom media verification passed

python src/verify_frame_content.py output/newsroom-frames
  newsroom frame-content verification passed
```

The existing final highlights passed with:

```text
A1 visible=30599 color=785  polygon coverage=99.63% centroid alpha=255
A2 visible=25296 color=747  polygon coverage=99.01% centroid alpha=255
A3 visible=29991 color=778  polygon coverage=99.47% centroid alpha=255
A4 visible=38889 color=1123 polygon coverage=98.94% centroid alpha=255
A5 visible=52184 color=1669 polygon coverage=99.35% centroid alpha=255
A6 visible=40662 color=2195 polygon coverage=98.15% centroid alpha=255
```

Their decoded pixel digests were pairwise distinct. The negative tests reject
duplicate contents, A1/A2 swaps, wrong clothing evidence, displaced alpha, and
transparent desk centroids.

Python compilation and Node syntax checks passed for all project sources and
both browser smoke harnesses. Cursor diagnostics reported no lint errors.

## Browser evidence

The preserved sample smoke passed all 12 reported checks, including natural
looping, native navigation, blocked-media fallback, reduced motion, and
autoplay recovery.

The six-desk smoke passed all 15 reported checks. Its pre-initialization cases
also verified that missing/malformed configuration retained the exact six
fallback polygons, four points per polygon, focusable native links, and all
six destinations.

## Media, hashes, and preservation

FFprobe still reports H.264, `yuv420p`, 1280×720, 24/1 fps, 120 decoded
frames, and 5.000000 seconds.

All newsroom output hashes exactly match their `web/assets` copies:

```text
newsroom.mp4                 41D951C6A1C2DC66710F7BB62E379D40C81F15597FDDDEBA32561F4B418E9515
newsroom-cover.png           22D719966EE557330885594468F79994E2500BBE95D6FED9F29F5BD5E21C0A9F
newsroom-a1-highlight.png    9D7A7B04F4DBC9F1F584998EBE9817C8B58DB29D234206A6874B9CB313D60DEC
newsroom-a2-highlight.png    6001E0A9858AF4359BC9BFD57A35805EFA8A86B54420022F2925D3D2F6067926
newsroom-a3-highlight.png    46953C6279E603FE76C66B785ED21E3602C0F3CBDBE5D1D8828F102F252D05E2
newsroom-a4-highlight.png    BA3126C254EEBFC38730F957FD9773D785E19E919941910CF0BE1A92C8D64349
newsroom-a5-highlight.png    730CE0378D0E4C878F116AF92EEDD1AFCF7081658C2788E23C073202BF904BE9
newsroom-a6-highlight.png    E1DCCE32C3B55AC63F9AB2A01946FD4BA244AA9BD0D632FA8BE44B898CBD9E9F
```

The approved sample remains unchanged, with 120 preserved frames:

```text
sample.mp4        F38BAC8366C715AD1B5C38E8BA57A918C7E4C430020B3F1699170A055F2124BB
sample-cover.png  2A518399E74A6C71FED2E49FF33AFEA2D00F2D45C9D7831F09FFEC8990AA71C8
sample-highlight.png EFC0F2574918828AAEF0F743B8DB11E5845A56D28D3DE64B93FEADB601D84C46
sample.blend      ECFCA96D56248EA75F478DA4AD8D4FCE2352CB884A3B1E3BA84EFE9DF9F93627
```

## Concerns

- Blender 5.2 compatibility and driver concerns recorded in the prior report
  remain unchanged. The earlier claim that installed Blender was not invoked
  by this report's pipeline tests was incorrect and is superseded below.
- The pipeline freshness guarantee is deletion-based: a requested target must
  be recreated nonempty after invocation. This is stronger than comparing
  timestamps on filesystems with coarse timestamp resolution.
- Physical touchscreen feel and non-Chromium rendering remain manual checks;
  native keyboard, CDP touch, reduced-motion, and failure behavior passed.

## Authoritative final re-review — 2026-07-19

### Status

PASS — the two final Important issues and the Minor issue are fixed without
Blender or media rerender. This section supersedes all status, Blender-process,
test-count, geometry-authority, and highlight-digest claims above.

### Final corrections

- Static SVG polygons are authoritative. `web/app.js` parses configured and
  embedded coordinates numerically, requires four finite in-bounds points,
  enforces the Python verifier's minimum doubled area of 4000, and requires
  every configured coordinate to match its desk's embedded coordinate within
  `1e-6`. It never writes the `points` attribute.
- The static contract checks every embedded polygon against the 4000 minimum.
  Browser negatives reject six structurally valid tiny polygons and a
  substantial but stale A3 polygon while preserving all six exact embedded
  point strings, focusable native links, and destinations.
- `scripts/render-newsroom.ps1` supports an explicit `BLENDER_EXECUTABLE`
  override. An existing override path is resolved first; otherwise production
  still selects the newest installed `blender.exe` under Program Files.
  Python fake-runner paths are executed by the resolved Python command solely
  to support hermetic test runners.
- Every preview, repair, and artifacts pipeline test now supplies a temporary
  fake runner. The guard test also provides an invalid installed-Blender trap,
  observes `FAKE_BLENDER_RUNNER_INVOKED`, reaches
  `NEWSROOM_PREVIEW_COMPLETE`, and confirms the fake log contains no
  `Blender Foundation` path.
- Highlight distinction now normalizes every fully transparent pixel to
  `(0,0,0,0)` before hashing. A negative test proves two visually identical
  highlights that differ only in hidden RGB are still rejected as duplicates.

### Regression-first evidence

- The static geometry test failed because `app.js` still called
  `polygon.setAttribute("points", ...)`.
- The hidden-RGB duplicate test failed because raw RGBA hashes treated a
  changed RGB triplet under alpha zero as distinct.
- The pipeline contract test failed because `BLENDER_EXECUTABLE` was absent.
- The new browser cases would have accepted tiny/stale polygons under the old
  nonzero-area-only validation; the final six-desk browser smoke now passes
  those cases.

### Authoritative verification

All commands exited 0:

```text
python -m unittest discover -s tests -v
  Ran 54 tests in 57.298s — OK

python src/verify_outputs.py output
  media verification passed

python src/verify_outputs.py output --newsroom
  newsroom media verification passed

python src/verify_frame_content.py output/newsroom-frames
  newsroom frame-content verification passed
```

Python compilation and all Node syntax checks passed. The preserved sample
browser smoke passed all 12 reported checks. The six-desk browser smoke passed
all 15 reported checks, including the expanded invalid-config gate before its
numbered interaction checks. Cursor diagnostics reported no lint errors.

All eight newsroom output hashes still exactly match their `web/assets`
destinations and remain the hashes recorded above. The four approved sample
hashes also remain exact, and `output/frames` still contains 120 sample frames.

### No-Blender evidence

- Process checks before and after this final re-review returned
  `NO_BLENDER_PROCESS_AT_START` and `NO_BLENDER_PROCESS_AT_END`.
- The full suite's render-mode tests used only temporary `.py` fake runners
  through `BLENDER_EXECUTABLE`; the installed-path trap would have failed if
  selected.
- No production render, preview, repair, artifacts, or `-SkipRender` pipeline
  command was run. No media or frame file was regenerated.

### Remaining concerns

- `BLENDER_EXECUTABLE` is an intentional process override; production
  environments should leave it unset unless selecting a reviewed Blender
  executable or controlled runner.
- Physical touchscreen feel and non-Chromium rendering remain manual checks.
- Existing Blender 5.2 deprecation and graphics-driver concerns are unchanged
  because Blender was not invoked in this final re-review.
