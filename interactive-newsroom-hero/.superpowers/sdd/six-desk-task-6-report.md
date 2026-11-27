# Six-Desk Newsroom — Task 6 Implementation Report

## Status

Task 6 is implemented. `web/app.js` now initializes all six desks from
`window.NEWSROOM_DESKS`, preserves the six native SVG destinations, maintains
one active desk, fills the shared five-field card, and supports pointer, focus,
Escape, Enter, touch confirmation, guarded navigation, reduced motion,
low-performance mode, per-highlight fallback, video fallback, autoplay
recovery, and the 20/24-second restart.

The Edge harness covers all 15 required browser contracts. The existing Task 5
ownership test was tightened so a polygon match cannot spill across a closing
link.

## Changed files

- Modified `web/app.js`.
- Created `.superpowers/sdd/six-desk-browser-smoke.mjs`.
- Modified `tests/test_web_contract.py`.
- Created this report.

No Git repository was initialized and no Git command was run.

## Browser assets used

The reserved final render was not run. Browser verification used allowed
existing artifacts:

- `web/assets/newsroom.mp4`: preserved five-second `output/sample.mp4`
  placeholder, 276,013 bytes.
- `web/assets/newsroom-cover.png`: current verified newsroom preview cover,
  1,040,895 bytes.
- `web/assets/newsroom-a1-highlight.png` through
  `newsroom-a6-highlight.png`: current verified newsroom preview highlights,
  respectively 290,433; 264,990; 282,003; 307,946; 327,443; and 308,620 bytes.

These browser assets are generated/ignored artifacts and are not represented as
source changes.

## TDD evidence

The six-desk browser harness was created before the controller rewrite.

Red command:

```powershell
node .superpowers/sdd/six-desk-browser-smoke.mjs
```

After correcting the harness's SVG `href` inspection itself, the intended red
run exited `1` on the first six-initialized-polygons assertion:

```text
Error: six-link initialization mismatch:
[{"id":"a1","href":"/demo/pages/m1-topics.html","points":"","pointCount":0},
 {"id":"a2","href":"/demo/pages/m2-collection.html","points":"","pointCount":0},
 {"id":"a3","href":"/demo/pages/m3-writing.html","points":"","pointCount":0},
 {"id":"a4","href":"/demo/pages/m4-review.html","points":"","pointCount":0},
 {"id":"a5","href":"/demo/pages/m5-channels.html","points":"","pointCount":0},
 {"id":"a6","href":"/demo/pages/m6-insights.html","points":"","pointCount":0}]
```

This was the expected failure caused by the old one-desk controller leaving all
six polygon `points` attributes empty.

## Browser server and smoke evidence

Server command, run from the project root:

```powershell
python -m http.server 4173 --directory ..
```

Smoke command:

```powershell
node .superpowers/sdd/six-desk-browser-smoke.mjs
```

Final result: exit `0` in 22.687 seconds:

```text
PASS 1: six native SVG links initialize in A1-A6 order
PASS 2: six distinct four-point polygons retain expected hrefs
PASS 3: pointer activation updates ID, card, side, color, and highlight under 100 ms
PASS 4: exactly one link expands and one highlight is opaque
PASS 5: non-selected desks remain visible in the dimmed scene
PASS 6: focus activates; Escape retains focus; Enter reaches every target
PASS 7: first touch selects and second touch reaches every target
PASS 8: blocked newsroom.mp4 shows cover and preserves all links
PASS 9: blocked A3 highlight uses SVG ring and retains navigation
PASS 10: reduced motion pauses video, zeros transitions, and navigates immediately
PASS 11: low-performance mode makes zero highlight requests and retains navigation
PASS 12: A6 404 is blocked and announces the exact failure message
PASS 13: autoplay rejection retries on first pointer interaction
PASS 14: natural playback reached end and sought to 0.900s
PASS 15: media is 1280x720 and 5.000 seconds
```

The harness starts a fresh headless Edge profile, drives the page through the
DevTools WebSocket, blocks real media requests for degradation checks, emulates
reduced motion and two-core hardware before load, injects one autoplay
rejection, and cleans up Edge and its temporary profile.

## Static, full-suite, media, syntax, and lint evidence

Focused static contract:

```powershell
python -m unittest tests.test_web_contract -v
```

Result: exit `0`; both tests passed:

```text
test_each_hit_link_owns_a_polygon_and_highlight ... ok
test_scene_contains_six_native_links_and_configured_destinations ... ok
Ran 2 tests in 0.002s
OK
```

Full suite:

```powershell
python -m unittest discover -s tests -v
```

Result: exit `0`; `Ran 38 tests in 60.284s`, `OK`.

Media/sample checks:

```powershell
python src/verify_outputs.py output --newsroom --preview
python src/verify_outputs.py output
```

Result: both exited `0`:

```text
newsroom preview verification passed
media verification passed
```

Preserved sample evidence:

```text
sample.mp4           F38BAC8366C715AD1B5C38E8BA57A918C7E4C430020B3F1699170A055F2124BB
sample-cover.png     2A518399E74A6C71FED2E49FF33AFEA2D00F2D45C9D7831F09FFEC8990AA71C8
sample-highlight.png EFC0F2574918828AAEF0F743B8DB11E5845A56D28D3DE64B93FEADB601D84C46
sample.blend         ECFCA96D56248EA75F478DA4AD8D4FCE2352CB884A3B1E3BA84EFE9DF9F93627
sample frame count   120
```

Syntax commands:

```powershell
python -m py_compile src/scene_config.py src/build_scene.py src/build_newsroom.py src/export_web_config.py src/verify_outputs.py
node --check web/scene-data.js
node --check web/app.js
node --check .superpowers/sdd/task4-browser-smoke.mjs
node --check .superpowers/sdd/six-desk-browser-smoke.mjs
```

All exited `0` with no output. IDE diagnostics reported no lint errors in
`web/app.js`, `.superpowers/sdd/six-desk-browser-smoke.mjs`, or
`tests/test_web_contract.py`.

## Remaining manual and final-render checks

- Do not treat the placeholder `web/assets/newsroom.mp4` as final newsroom
  visual evidence. It proves the five-second media/controller contract only.
- The final 120-frame newsroom render, encode, direct newsroom `ffprobe`,
  `python src/verify_outputs.py output --newsroom`, web asset hash
  synchronization, and `NEWSROOM_PIPELINE_COMPLETE` sentinel remain reserved
  for Task 7.
- After final asset synchronization, manually inspect all six highlight masks
  against the encoded newsroom video at desktop and narrow/mobile viewport
  sizes. Automated checks prove geometry, state, and fallback behavior but not
  subjective visual alignment against the future final encode.

## Authoritative Review Fix Evidence — Supersedes Prior Claims

This section supersedes the original status, smoke-integrity claims, and final
verification results above. The review correctly identified controller defects
and assertions whose labels were stronger than their evidence.

### Controller corrections

- Activation now writes the exact selected desk `--desk-color`,
  `--desk-wash`, and `--desk-glow` to the scene root. The card and highlight
  siblings inherit the active color, while every native link retains its own
  color variables for focus and fallback rings. Deactivation removes all three
  scene overrides and restores stylesheet defaults.
- Low-performance mode still assigns no highlight `src` values and now always
  renders the selected desk polygon with the inherited color/wash ring.
- Before any config-derived lookup, the controller requires exactly six IDs
  matching `^a[1-6]$` with a set size of six. It builds maps from existing DOM
  nodes using fixed selectors, verifies every config ID maps to an existing
  native link and highlight, and then performs direct map lookup. No config ID
  is interpolated into a selector.

`web/styles.css` was additionally modified for the low-performance selected
ring. No existing accessibility, navigation, media degradation, or fallback
behavior was removed.

### Review-fix red evidence

The strengthened smoke was run before the controller corrections:

```powershell
node .superpowers/sdd/six-desk-browser-smoke.mjs
```

It exited `1` at the new malformed-config boundary:

```text
Error: duplicate config was not rejected by explicit safe-ID validation:
["Error: Native href does not match configuration for a1 ..."]
```

This proved the prior controller accepted duplicate IDs far enough to perform
record initialization instead of rejecting them before lookup. The prior
controller also failed the subsequently exercised root-color and
low-performance-ring assertions.

### Strengthened browser evidence

The revised harness now:

- replaces `scene-data.js` through DevTools request fulfillment to verify both
  duplicate and selector-injection-shaped IDs are explicitly rejected before
  native links or polygons are mutated;
- checks exact title, English label, role, responsibility, action, normalized
  full card copy, card side, link color, scene-root color, and inherited
  card/highlight color for A1–A6;
- measures activation state synchronously at no more than 100 ms, requires the
  declared 0.1-second opacity transition, and allows at most 250 ms for
  headless Edge to settle opacity—there is no multi-second polling path;
- waits at most 350 ms for and then checks the actual computed
  `brightness(0.78) saturate(0.72)` video filter;
- verifies Escape keeps focus while hiding and clearing the card and setting
  all six links to `aria-expanded="false"`;
- enables DevTools touch emulation and uses `Input.dispatchTouchEvent` at each
  polygon's actual center for both taps; no synthetic `PointerEvent("click")`
  is used for the touch contract;
- keeps the real MP4 request blocked while navigating all six native links and
  re-establishing fallback after each return;
- proves low-performance mode has no highlight sources or requests and has a
  visible selected polygon fill/stroke ring;
- observes natural playback crossing the end, then reloads with playback
  mocked and replaces the media-time accessor with a synchronous write recorder
  to prove the `ended` handler itself assigns exactly `20 / 24` before playback
  drift.

Final command:

```powershell
node .superpowers/sdd/six-desk-browser-smoke.mjs
```

Result: exit `0`:

```text
PASS 1: safe unique config initializes six native SVG links in A1-A6 order
PASS 2: six distinct four-point polygons retain expected hrefs
PASS 3: pointer activation updates exact card, side, propagated color, and state within 100 ms
PASS 4: exactly one link expands and one highlight is opaque
PASS 5: non-selected desks remain visible under the measured video dim/filter
PASS 6: Escape retains focus while clearing card and collapsing all links; Enter reaches targets
PASS 7: real CDP touch input selects first and reaches every target on second tap
PASS 8: blocked newsroom.mp4 shows cover and all six native links still navigate
PASS 9: blocked A3 highlight uses SVG ring and retains navigation
PASS 10: reduced motion pauses video, zeros transitions, and navigates immediately
PASS 11: low-performance mode shows selected ring, makes zero highlight requests, and navigates
PASS 12: A6 404 is blocked and announces the exact failure message
PASS 13: autoplay rejection retries on first pointer interaction
PASS 14: natural playback ended; deterministic handler seek was 0.833s
PASS 15: media is 1280x720 and 5.000 seconds
```

### Authoritative regression evidence

```powershell
python -m unittest discover -s tests -v
```

Result: exit `0`; `Ran 38 tests in 54.730s`, `OK`.

```powershell
python src/verify_outputs.py output --newsroom --preview
python src/verify_outputs.py output
```

Result: both exited `0`:

```text
newsroom preview verification passed
media verification passed
```

```powershell
python -m py_compile src/scene_config.py src/build_scene.py src/build_newsroom.py src/export_web_config.py src/verify_outputs.py
node --check web/scene-data.js
node --check web/app.js
node --check .superpowers/sdd/task4-browser-smoke.mjs
node --check .superpowers/sdd/six-desk-browser-smoke.mjs
```

All syntax commands exited `0` without output. IDE diagnostics reported no lint
errors in the controller, CSS, strengthened smoke, or static web test.

No full 120-frame render, complete newsroom encode/verification, Git
initialization, or Git command was run. The final-render and visual-alignment
concerns listed above remain the only outstanding checks.
