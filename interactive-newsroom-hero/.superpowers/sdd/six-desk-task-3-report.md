# Six-Desk Newsroom — Task 3 Review

## Verdict

- **Spec compliance: REJECTED**
- **Code quality: REJECTED**

No tests or renders were run during this review.

## Blocking finding

1. **The complete-scene verifier checks the sample frame directory.**  
   `src/verify_outputs.py:235-238` looks for representative frames under
   `root / "frames"`. The approved six-desk contract uses
   `output/newsroom-frames/` for full-render frames and
   `output/newsroom-preview/` for preview representatives
   (`2026-07-19-six-desk-newsroom-implementation.md:14, 50-51, 247-248`).
   Consequently, `validate_newsroom(root)` can pass its representative-frame
   check using stale one-desk sample frames, and it fails against an otherwise
   correctly laid-out six-desk output that has only `newsroom-frames/`.
   This violates the complete-scene requirement at plan line 483 and creates a
   hidden dependency on preserved sample output.

## Polygon and generated-config checks

- `output/newsroom-hit-regions.json` has the exact `1280x720` view box and keys
  ordered `a1` through `a6`.
- All six regions are distinct, four-point, integer, in-bounds polygons.
  Their polygon areas are respectively 7,780; 6,444; 7,885; 11,867; 15,663;
  and 12,492 square pixels, all above the required 2,000-square-pixel minimum
  (`twice_area >= 4000`).
- The six polygon bounding boxes are pairwise disjoint, so the checked-in
  projected regions do not overlap.
- `validate_hit_regions` implements the plan's exact order, bounds, minimum
  area, and duplicate-polygon rules (`src/verify_outputs.py:78-104`).
  It does **not** detect geometric overlap between different polygons. The
  cited Task 3 requirements require distinct polygons but do not explicitly
  require an overlap-rejection algorithm; if “overlap rules” means overlaps
  must be rejected, that rule is missing.
- `web/scene-data.js` contains six records in `DESKS` order. Every `points`
  string exactly matches its corresponding JSON quad.
- Module/title/English label, role, responsibility copy, action, six-digit
  color, destination, highlight path, and card side all match the approved
  `DESKS` interface. Destinations and highlight paths are unique and correctly
  keyed A1–A6.
- Generation is deterministic: UTF-8 input, fixed `DESKS` order,
  `ensure_ascii=False`, two-space indentation, fixed wrapper and newline.
  It derives points from validated projection JSON without clamping or
  hard-coded polygon fallback.
- Config generation depends only on the hit-region JSON plus Python metadata;
  it does not invoke Blender, FFmpeg, rendering, or `validate_newsroom`, so
  there is no hidden full-render dependency in the generation path.

## Verifier and regression checks

- Six-highlight validation requires every A1–A6 image to be `1280x720` RGBA
  with both transparent and visible pixels.
- Video validation covers H.264, `yuv420p`, `1280x720`, 24 fps, 120 decoded
  frames, and 5.0 seconds. Cover validation checks near-white samples, contact
  shadows, and evidence for every configured clothing color.
- The existing `verify(root)` function and its sample-oriented messages are
  not called or altered by the new `validate_newsroom(root)` path; the sample
  API remains separate.

## Code-quality findings

1. **No unit test exercises `validate_newsroom`.**  
   `tests/test_verify_outputs.py` imports neither `validate_newsroom` nor
   verifies its path selection, artifact prefixes, video/cover integration, or
   missing-output behavior. This is why the blocking `frames/` regression is
   undetected.
2. **The claimed verifier coverage is narrower than the report implied.**  
   The added polygon test checks only one valid fixture and exact duplication;
   it does not test wrong order, out-of-bounds points, minimum area, malformed
   payloads, or geometric overlap. There are also no Task 3 tests for
   `load_hit_regions`, deterministic serialization, or config-to-projection
   equality.
3. **Malformed JSON can crash validation instead of returning errors.**  
   `validate_hit_regions` assumes `regions` is a mapping, each region is sized,
   and each coordinate is numeric. Inputs such as a list for `regions`, a
   scalar point, or string coordinates can raise `AttributeError`, `TypeError`,
   or comparison errors. This is a robustness issue for a public validator,
   though the checked-in generated payload is valid.

Approval requires correcting the six-desk representative-frame path and adding
focused coverage for `validate_newsroom`. Geometric overlap rejection should
also be added if it is intended as an acceptance rule beyond the plan's
explicit distinctness requirement.

## Review Fix Evidence — 2026-07-19

### Implemented fixes

- `validate_newsroom(root)` now defaults exclusively to representative frames
  under `newsroom-frames/`. Preserved sample files under `frames/` cannot
  satisfy newsroom validation.
- `validate_newsroom(root, preview=True)` is the only path that reads
  `newsroom-preview/`.
- Each selected representative frame is opened and checked for `1280x720`
  dimensions, near-white background, contact-shadow pixels, and all six
  configured clothing colors. Missing and content errors carry the
  `newsroom-frames/...` or `newsroom-preview/...` artifact prefix.
- Focused temporary-artifact tests execute `validate_newsroom` with real cover,
  highlight, hit-region, and frame files. Only `ffprobe` is mocked, avoiding a
  render and encoded-video fixture.
- `validate_hit_regions` now returns errors for non-object payloads, non-object
  region collections, non-list polygons, malformed point pairs, non-integer
  coordinates, and booleans instead of raising type-related exceptions.
- Added focused order, bounds, minimum-area, malformed-type, and exact-duplicate
  polygon tests.
- Added `load_hit_regions` valid/invalid tests and a deterministic export test
  that proves every generated SVG point string equals its projected JSON quad
  and the serialization equals checked-in `web/scene-data.js`.

Geometric non-overlap is not an acceptance rule in Task 3: the approved plan
requires distinct polygons, while the reviewed projection already has
pairwise-disjoint bounding boxes. No additional overlap algorithm was added.

### TDD red evidence

Before the fixes, the expanded focused suite failed exactly at the reviewed
boundaries:

```text
python -m unittest tests.test_verify_outputs tests.test_export_web_config -v
validate_hit_regions(None): AttributeError
validate_hit_regions(scalar polygon): TypeError
validate_hit_regions(string coordinate): TypeError
validate_newsroom(..., preview=True): unexpected keyword argument 'preview'
default newsroom path did not report newsroom-frames/frame_0001.png
Ran 18 tests
FAILED (failures=1, errors=6)
```

### Focused green evidence

```text
python -m unittest tests.test_verify_outputs tests.test_export_web_config -v
Ran 18 tests in 26.249s
OK
```

### Full regression evidence

```text
python -m unittest discover -s tests -v
Ran 27 tests in 26.702s
OK
```

### Generation and diagnostics

```powershell
python src/export_web_config.py output/newsroom-hit-regions.json web/scene-data.js
node --check web/scene-data.js
```

Both commands exited `0`; `node --check` emitted no errors. IDE diagnostics
reported no lint errors in the two source files and two focused test files.
The valid generated `web/scene-data.js` remains projection-equal and
deterministic.

No full render, Git initialization, or commit was performed.
