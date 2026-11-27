# Task 1 Report: 分镜元数据 + Hero 结构壳

**Status:** DONE  
**Date:** 2026-07-19  
**Agent:** Task 1 dispatch (subagent)

## Summary

Implemented storyboard metadata and Hero HTML shell for the M0 dashboard per `task-1-brief.md`. Only `demo/assets/data.js` and `demo/assets/app.js` were modified. No CSS, SVG assets, or git commits.

## Changes

### `demo/assets/data.js`

- Added `pipelineFrames` array (6 items) immediately after `steps`, with verbatim copy from design doc §4.2:
  - A1–A6 ids, codes, names, blurbs (≤18 汉字), accent colors, frame filenames, and shape hints.

### `demo/assets/app.js`

- Added `storyboardHTML(idx)` before `renderDashboard` — renders `<section class="storyboard">` with six `<a class="storyboard-frame">` links, each with art img (`../assets/frames/…`), caption, `data-frame`, `is-current` on active index.
- Added `goFrame(id, full)` — navigates via `renderPage(id, true)` in full-demo mode or `location.href = step.file` in standalone pages.
- Added `bindStoryboard(full)` — touch two-tap arm pattern on coarse pointers; otherwise prevents default and calls `goFrame`.
- Rewrote `renderDashboard(full)`:
  - Preserved `stats`, `ghosts`, `idx`, `target`, `statusLabel` logic.
  - Added `slimGhosts` (max 2 ghost cards per column).
  - Inserted storyboard Hero between stats and kanban.
  - Added `storyboard-heading` / `kanban-heading` class hooks for Task 2 CSS.
  - Switched kanban to `kanban-compact` with truncated ghosts.
  - Preserved `#start` button and `[data-open]` main story-card click handlers.
  - Calls `bindStoryboard(full)` after render.

## Verification

| Check | Result |
|-------|--------|
| `node --check demo/assets/data.js` | exit 0, no output |
| `node --check demo/assets/app.js` | exit 0, no output |
| `pipelineFrames.length === 6` | confirmed in source |
| Render path symbols present | `storyboardHTML`, `goFrame`, `bindStoryboard`, `kanban-compact`, `slimGhosts` |
| Browser smoke | Not run (no browser in agent env); structure verified via static grep |

## Self-Review

- **Brief compliance:** All specified code blocks applied verbatim; function name is `storyboardHTML` (brief Step 2 heading says `storyboardHTML`; Interfaces section mentions `frameHTML` — implemented as `storyboardHTML` per Step 2 code).
- **Scope:** No CSS, no SVG files, no other files touched.
- **Existing behavior:** Start button and main story-card `data-open` handlers unchanged in logic; only shell layout expanded.
- **Missing assets:** Frame SVGs under `demo/assets/frames/` do not exist yet (Task 3); img tags will 404 until then — expected.
- **Styling:** Hero will appear unstyled until Task 2 adds `.storyboard*` / `.kanban-compact` rules — expected.

## Concerns

None blocking. Visual layout depends on Task 2 CSS; frame images depend on Task 3 SVGs.

## Commits

None (per dispatch instructions; workspace is not a git repository).
