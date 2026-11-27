# Task 4 Report: Build the One-Desk Interaction Proof

## Status

DONE_WITH_CONCERNS

## Files changed

- Created `web/index.html`: accessible A1 scene markup consuming the synchronized video, cover, and highlight assets.
- Created `web/styles.css`: full-viewport scene, 100 ms highlight, role card, responsive target, video fallback, and reduced-motion presentation.
- Created `web/app.js`: pointer, focus, Escape, two-tap touch, idle-loop, media-error, autoplay-retry, and module-navigation behavior.
- Created `.superpowers/sdd/task4-browser-smoke.mjs`: repeatable headless Edge interaction checks against the served parent directory.
- Created `.superpowers/sdd/task-4-report.md`: this evidence report.

No Git repository was initialized and no commit was created.

> **SUPERSEDED HISTORICAL EVIDENCE:** The original implementation and first accessibility-review results below record earlier iterations. They are not the current acceptance result. The authoritative final state is the appended **Final Blocked-Media Re-Review Resolution** section.

## TDD evidence

Before creating the viewer, this command was run:

`python -c "from pathlib import Path; root=Path('web'); required=['index.html','styles.css','app.js']; missing=[name for name in required if not (root/name).is_file()]; assert not missing, f'missing viewer files: {missing}'"`

It exited 1 with the expected failure:

`AssertionError: missing viewer files: ['index.html', 'styles.css', 'app.js']`

After implementation, the corresponding presence check exited 0 and printed:

`viewer files present`

## Automated results

### Project tests

Command:

`python -m unittest discover -s tests -v`

Result: exit code 0. Exact summary:

- `test_a1_role_contract ... ok`
- `test_required_outputs_are_named ... ok`
- `test_sample_is_exactly_five_seconds ... ok`
- `test_sample_uses_hd_canvas ... ok`
- `test_accepts_expected_video ... ok`
- `test_reports_wrong_duration_and_size ... ok`
- `Ran 6 tests in 0.001s`
- `OK`

### Media verification

Command:

`python src/verify_outputs.py output`

Result: exit code 0, exact output:

`media verification passed`

### Viewer syntax and diagnostics

- `node --check web/app.js`: exit code 0 with no output.
- IDE diagnostics for `web/index.html`, `web/styles.css`, and `web/app.js`: no linter errors.

### Browser interaction automation

The temporary server command was:

`python -m http.server 4173 --directory ..`

The server returned HTTP 200 for the viewer HTML, CSS, JavaScript, MP4, cover, highlight, destination page, and destination assets. The destination request was:

`GET /demo/pages/m1-topics.html HTTP/1.1` → 200.

Command:

`node .superpowers/sdd/task4-browser-smoke.mjs`

Result: exit code 0. Exact output:

```text
PASS media: 1280x720, 5.000s
PASS natural loop: reached 4.955s, restarted at 0.923s
PASS red clothing evidence: 401 sampled red pixels
PASS hover: active immediately, highlight transition 0.1s
PASS card copy: A1 title, role, responsibility, and prompt
PASS keyboard: focus activates; Escape deactivates and blurs
PASS touch/navigation: first tap revealed; second resolved http://localhost:4173/demo/pages/m1-topics.html
PASS video failure: cover, message, and interaction remained usable
PASS reduced motion: static cover, zero transition, immediate activation
PASS idle restart: ended event sought to 0.833s
```

## Interaction checklist and evidence

1. **Idle loop:** Headless Edge decoded the real MP4, naturally reached 4.955 seconds, fired `ended`, and resumed at 0.923 seconds. The explicit ended-event check also sought to 0.833 seconds (`20 / 24`), so the opening camera interval is skipped on repeat.
2. **Visible red character:** Both supplied PNGs were visually inspected. The cover shows the seated character in red clothing; browser canvas sampling found 401 red samples in the decoded cover.
3. **Hover within 100 ms:** A real browser `PointerEvent` activated the scene synchronously; computed highlight transition duration was exactly `0.1s`.
4. **Card copy:** Browser DOM text contained A1/TOPIC PLANNING, `智能选题`, `策划编辑`, `聚合热点信号，形成可执行的报道方向。`, and `点击进入模块 →`.
5. **Keyboard:** Browser focus activated the scene. Escape removed the active class and moved focus away from the desk button.
6. **Touch:** A touch-pointer click left the viewer URL unchanged and revealed the active state. The second touch-pointer click navigated to the existing module page, which returned HTTP 200.
7. **Video failure:** Dispatching the media element's error event hid the video, retained the cover background, displayed the fallback message, and left pointer activation usable.
8. **Reduced motion:** DevTools emulation made the media query match; the video computed to `display: none`, the cover remained, transitions computed to `0s`, and activation remained immediate.

## Unverified manual checks

- No physical touchscreen was available; touch semantics were exercised with browser-native touch `PointerEvent` objects.
- MP4 failure was exercised through the browser media-error path rather than an interactive DevTools request-blocking UI.
- The loop timing proves the opening interval is skipped, but a human did not watch and judge the camera movement or seam quality in a visible browser window.
- Visual polish, text legibility across arbitrary displays, and browsers other than the installed Edge/Chromium engine were not manually evaluated.

## Self-review

- The implementation follows Task 4's one-A1-desk boundary and adds no other desks or speculative modules.
- The navigation value is `../../demo/pages/m1-topics.html`; from `/interactive-newsroom-hero/web/` it resolved to `/demo/pages/m1-topics.html` and loaded successfully.
- The empty decorative highlight alt text and hidden video avoid duplicate screen-reader content; the button carries the A1 role label and description.
- Pointer, keyboard, touch, reduced-motion, autoplay rejection, playback end, and media error paths are all explicit and independently exercised where browser tooling permits.
- The cover remains the hero background, so both reduced-motion and video-failure modes retain a usable desk target.
- The only observed HTTP 404 was the browser's unsolicited `/favicon.ico` request. Headless browser shutdown also reset a few in-flight server connections; neither affected viewer assets or behavior.

## Concerns

The supported automated checks pass. Remaining concerns are limited to the manual-only checks above: physical-device touch feel, an actual request-blocking exercise, subjective loop seam/camera assessment, and cross-browser visual review.

## Accessibility and Test-Quality Review Fixes

This section supersedes the earlier button, Escape, autoplay, and MP4-blocking notes.

### Changes made

- Replaced the empty navigating button with an `<a href="../../demo/pages/m1-topics.html">`. Normal mouse and keyboard activation now use native link navigation; the first touch activation still prevents navigation to reveal the desk, and the second follows the link.
- Added `aria-controls="role-card"` and synchronized `aria-expanded`. The role card now has `hidden` while inactive, is absent from the accessibility tree until selected, and becomes available when selected.
- Added a persistent, initially empty polite status region. Selection announces the A1 title, role, and responsibility; Escape announces cancellation.
- Escape now collapses the selection while retaining focus on the link. A focus-dismissed guard prevents retained focus from immediately reopening the card; leaving and returning through normal tab order resets the guard.
- Reworked the fallback as an initially empty `role="status"` live region. Media failure populates it after page load while the CSS changes it from visually hidden to visible.
- The failure handler now listens to both the media element and its `<source>`, and non-autoplay `play()` failures also enter the fallback state.
- Removed `--autoplay-policy=no-user-gesture-required` from the browser harness. A new-document override rejects the first application `play()` with `NotAllowedError`; a browser pointerdown then produces a second play attempt and advancing playback.
- Added native-link, expanded/collapsed, focus-retention, live-region, and Chromium accessibility-tree assertions to the browser harness.
- Added deterministic CDP Fetch interception for the MP4 request. Headless Edge confirms one intercepted request and `HTMLMediaElement.NETWORK_NO_SOURCE` (`networkState === 3`), but CDP's `Fetch.failRequest` does not emit a DOM `error` event or populate `video.error`. The harness therefore separately dispatches the source's real `error` event to deterministically cover the production media-error handler and announcement.

### Red evidence

After extending the harness but before changing the viewer:

`node .superpowers/sdd/task4-browser-smoke.mjs`

Exited 1 with:

`Error: desk is not a native destination link`

During real-request investigation, CDP interception produced this exact diagnostic:

`blocked-video fallback missing: {"blockedMp4Requests":1,"failureDiagnostic":{"url":"http://localhost:4173/interactive-newsroom-hero/web/?blocked-media=1","failed":false,"videoError":null,"readyState":0,"networkState":3,"currentSrc":"http://localhost:4173/interactive-newsroom-hero/web/assets/sample.mp4","sourceExists":true}}`

This demonstrates why the intercepted network request and deterministic DOM media-error handler are asserted separately.

### Final exact commands and results

`node --check web/app.js`

Result: exit code 0, no output.

`node --check .superpowers/sdd/task4-browser-smoke.mjs`

Result: exit code 0, no output.

`node .superpowers/sdd/task4-browser-smoke.mjs`

Result: exit code 0. Exact output:

```text
PASS media: 1280x720, 5.000s
PASS semantics: native link, collapsed disclosure, inactive content hidden
PASS natural loop: reached 4.891s, restarted at 0.929s
PASS red clothing evidence: 401 sampled red pixels
PASS hover: active immediately, highlight transition 0.1s
PASS card copy: A1 title, role, responsibility, and prompt
PASS keyboard: focus activates; Escape deactivates while retaining focus
PASS touch/navigation: first tap revealed; second resolved http://localhost:4173/demo/pages/m1-topics.html
PASS video failure: MP4 request blocked; deterministic source-error path announced fallback
PASS reduced motion: static cover, zero transition, immediate activation
PASS autoplay recovery: rejected once, recovered after pointerdown (2 play attempts)
PASS idle restart: ended event sought to 0.833s
```

`python -m unittest discover -s tests -v`

Result: exit code 0:

```text
test_a1_role_contract (test_scene_config.RenderSpecTests.test_a1_role_contract) ... ok
test_required_outputs_are_named (test_scene_config.RenderSpecTests.test_required_outputs_are_named) ... ok
test_sample_is_exactly_five_seconds (test_scene_config.RenderSpecTests.test_sample_is_exactly_five_seconds) ... ok
test_sample_uses_hd_canvas (test_scene_config.RenderSpecTests.test_sample_uses_hd_canvas) ... ok
test_accepts_expected_video (test_verify_outputs.ProbeValidationTests.test_accepts_expected_video) ... ok
test_reports_wrong_duration_and_size (test_verify_outputs.ProbeValidationTests.test_reports_wrong_duration_and_size) ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.001s

OK
```

`python src/verify_outputs.py output`

Result: exit code 0, exact output:

`media verification passed`

IDE diagnostics for the three viewer files and browser harness: no linter errors.

### Updated concerns

- A physical touchscreen was not available; native touch-pointer events cover the two-step state machine.
- Headless Edge's CDP request failure reaches `NETWORK_NO_SOURCE` but emits no DOM media error, so request interception and the media-error handler are deterministic separate assertions as described above.
- Subjective loop seam quality and cross-browser visual polish remain manual checks.

## Final Blocked-Media Re-Review Resolution

This is the authoritative final Task 4 result. It supersedes all earlier claims that MP4 interception and fallback handling required separate assertions.

### Fix

- `web/app.js` now runs a bounded media-state watcher only while metadata has not become ready.
- Every 100 ms, it checks for the persistent failure pair `readyState === HAVE_NOTHING` and `networkState === NETWORK_NO_SOURCE`.
- It requires two consecutive matching checks before activating the existing fallback, preventing a one-sample transient from being treated as failure.
- Successful metadata readiness, including readiness already present when the script starts, permanently stops the watcher. The harness lets the successful video play through a complete five-second loop and asserts that no false fallback occurred.
- The watcher stops after four seconds, so it cannot poll indefinitely. Existing video/source error listeners and non-autoplay play rejection handling remain additional failure paths.
- The browser harness no longer dispatches any synthetic media event. Its intercepted MP4 request alone must produce the visible, announced, interactive fallback.

### Red evidence

After removing the synthetic source error from the harness and before adding the bounded watcher:

`node .superpowers/sdd/task4-browser-smoke.mjs`

Result: exit code 1, exact failure:

`Error: blocked MP4 did not activate fallback end-to-end`

### Final exact commands and results

`node --check web/app.js`

Result: exit code 0, no output.

`node --check .superpowers/sdd/task4-browser-smoke.mjs`

Result: exit code 0, no output.

`node .superpowers/sdd/task4-browser-smoke.mjs`

Result: exit code 0. Exact output:

```text
PASS media: 1280x720, 5.000s
PASS semantics: native link, collapsed disclosure, inactive content hidden
PASS natural loop: reached 4.973s, restarted at 0.924s
PASS red clothing evidence: 401 sampled red pixels
PASS hover: active immediately, highlight transition 0.1s
PASS card copy: A1 title, role, responsibility, and prompt
PASS keyboard: focus activates; Escape deactivates while retaining focus
PASS touch/navigation: first tap revealed; second resolved http://localhost:4173/demo/pages/m1-topics.html
PASS video failure: real blocked MP4 triggered bounded no-source fallback
PASS reduced motion: static cover, zero transition, immediate activation
PASS autoplay recovery: rejected once, recovered after pointerdown (2 play attempts)
PASS idle restart: ended event sought to 0.833s
```

`python -m unittest discover -s tests -v`

Result: exit code 0:

```text
test_a1_role_contract (test_scene_config.RenderSpecTests.test_a1_role_contract) ... ok
test_required_outputs_are_named (test_scene_config.RenderSpecTests.test_required_outputs_are_named) ... ok
test_sample_is_exactly_five_seconds (test_scene_config.RenderSpecTests.test_sample_is_exactly_five_seconds) ... ok
test_sample_uses_hd_canvas (test_scene_config.RenderSpecTests.test_sample_uses_hd_canvas) ... ok
test_accepts_expected_video (test_verify_outputs.ProbeValidationTests.test_accepts_expected_video) ... ok
test_reports_wrong_duration_and_size (test_verify_outputs.ProbeValidationTests.test_reports_wrong_duration_and_size) ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.000s

OK
```

`python src/verify_outputs.py output`

Result: exit code 0, exact output:

`media verification passed`

IDE diagnostics for `web/app.js` and `.superpowers/sdd/task4-browser-smoke.mjs`: no linter errors.

### Final concerns

- No concern remains for deterministic blocked-MP4 fallback: the real intercepted request now activates the production fallback end-to-end with no synthetic event.
- Physical touchscreen feel, subjective loop-seam quality, and non-Chromium visual review remain manual-only checks.
