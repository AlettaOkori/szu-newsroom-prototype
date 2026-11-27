# Task 2 Report: 错落排版 + 悬停 CSS

**Date:** 2026-07-19  
**Status:** Complete  
**Files modified:** `demo/assets/styles.css`  
**Files not modified:** `demo/assets/app.js`, SVG assets (per scope)

---

## Summary

Added the M0 storyboard hero CSS block immediately after the existing `/* dashboard */` section in `styles.css`. Hover backgrounds use **fixed pastel colors** (not `color-mix`) for older Edge compatibility, as specified in the brief and task constraints.

---

## Implementation Details

### Placement
- Inserted after line 15 (`/* dashboard */` kanban rules), before `/* topics */`.
- Comment anchor: `/* M0 storyboard hero */`.

### Hover background choice
- Brief allows `color-mix` **or** fixed accent pastels.
- Implemented fixed colors per brief:
  - `accent-yellow` → `#fff8d0`
  - `accent-cyan` → `#e7f6f8`
  - `accent-pink` → `#fde8ee`
  - `accent-red` → `#f9e9ec`
- Shared hover rule retains `box-shadow: 0 10px 0 rgba(26,24,23,.06)` only (no `color-mix`).

### Scope consumed from Task 1
All selectors match Task 1 markup in `app.js`:
`.storyboard`, `.storyboard-frame`, `.shape-*`, `.accent-*`, `.is-current`, `.is-armed`, `.storyboard-caption`, `.storyboard-lines`, `.storyboard-copy`, `.kanban-compact`, `.storyboard-heading`, `.kanban-heading`.

---

## Self-Review Checklist (vs brief)

| Requirement | Status | Notes |
|-------------|--------|-------|
| CSS after `/* dashboard */` | ✅ | Block inserted before `/* topics */` |
| Six-frame staggered layout (`nth-child` margins) | ✅ | 36/88/28/96/12/84 px |
| `shape-tall` / `shape-wide` widths & aspect ratios | ✅ | 128/168 px; 3/4 and 5/3 |
| Accent CSS variables | ✅ | yellow/cyan/pink/red |
| Hover/focus/armed: `translateY(-6px) scale(1.04)` | ✅ | |
| Other frames fade to ~0.55 opacity on hover/focus | ✅ | `:not(:hover):not(:focus-visible):not(.is-armed)` + `:has(:focus-visible)` |
| Hover: pastel background + bottom shadow | ✅ | Fixed pastels + box-shadow |
| Caption swap: hide lines, show copy | ✅ | `display:none` / `display:flex` |
| Active press: `translateY(-2px) scale(.98)` | ✅ | |
| `.is-current` red left bar on art | ✅ | `:before` pseudo on `.storyboard-art` |
| `.kanban-compact` reduced kanban sizing | ✅ | min-height 280px, tighter padding/fonts |
| Responsive `@media (max-width:1100px)` | ✅ | horizontal scroll, uniform 24px margin |
| `prefers-reduced-motion: reduce` | ✅ | transitions off, transforms none |
| No JS/SVG changes | ✅ | CSS only |
| No git commit | ✅ | Skipped per plan |

---

## Browser Verification (Step 2)

**Page:** `demo/pages/m0-dashboard.html` (or `demo/index.html` → M0)

**Expected behavior:**
1. Six storyboard frames display in a staggered vertical rhythm (not a flat row).
2. Hover one frame → it lifts (`translateY(-6px) scale(1.04)`), gets accent pastel background and drop shadow.
3. Caption: decorative lines hide; code/name + blurb text appear.
4. Other five frames fade to ~55% opacity.
5. Frame matching current story status (`storyStatus === "线索"` → A1) shows red left bar via `.is-current`.
6. Kanban below uses compact spacing when `.kanban-compact` is present.
7. With OS reduced-motion enabled, hover lift/scale is disabled.

**Test method:** Static CSS review + selector/markup alignment verified against `app.js`. Live hover test recommended in browser (not run in this session).

---

## Deviations from brief template

| Item | Deviation |
|------|-----------|
| Hover `background` on art | Used fixed pastels instead of `color-mix(in srgb, var(--accent) 28%, #fff)` — intentional per brief option B and task constraint |

No other deviations.

---

## Concerns / Follow-ups

1. **`:has()` selector** — Used for focus-within dimming; unsupported in very old browsers (pre-Chromium Edge). Acceptable for demo; brief specifies this pattern.
2. **Live browser test** — CSS-only verification done; manual hover QA on M0 still recommended before merge.
3. **`is-armed` class** — Styled in CSS; JS wiring for armed state is out of Task 2 scope (Task 1 markup only).

---

## Commits

None (no git repo; per task instructions).

---

## Fix

Added peer-dim rule for armed state in `demo/assets/styles.css`, immediately after the existing `.storyboard:hover` / `:has(:focus-visible)` opacity block:

```css
.storyboard:has(.storyboard-frame.is-armed) .storyboard-frame:not(.is-armed){opacity:.55}
```

**Confirmed:** Rule present at lines 28–28 in `styles.css` (directly following the hover/focus-visible dimming rules). Non-armed frames now fade to 55% opacity when any frame has `.is-armed`.
