# Six-Desk Newsroom — Task 5 Implementation Report

## Status

Task 5 is implemented within its stated file boundary. The page now exposes six
native SVG links with explicit fallback destinations, six independent highlight
layers, one reusable role card, live status/fallback regions, and the required
alignment, interaction-state, focus, coarse-pointer, performance-fallback, and
reduced-motion CSS.

`web/app.js` was not changed; the Task 6 controller remains unimplemented.
Existing sample assets were not edited or removed. No full render or Git command
was run.

## Changed files

- Modified `web/index.html`.
- Modified `web/styles.css`.
- Created `tests/test_web_contract.py`.
- Created this report.

## TDD evidence

The prescribed static contract was created before production changes.

Red command:

```powershell
python -m unittest tests.test_web_contract -v
```

Initial result: exit `1`; both tests failed for the expected missing Task 5
interface. The page contained zero `data-desk-id` links and no matching native
SVG link/polygon/highlight structure.

After the minimal HTML and CSS implementation, the same command returned:

```text
test_each_hit_link_owns_a_polygon_and_highlight ... ok
test_scene_contains_six_native_links_and_configured_destinations ... ok

Ran 2 tests in 0.002s
OK
```

All six destination existence checks succeeded. IDE diagnostics reported no
lint errors in `web/index.html`, `web/styles.css`, or
`tests/test_web_contract.py`.

## Scope boundary

The SVG polygons intentionally retain empty `points` attributes for the later
controller to populate from `window.NEWSROOM_DESKS`. `scene-data.js` is loaded
before `app.js`, while every native SVG link retains its explicit `href` for
script-independent navigation.
