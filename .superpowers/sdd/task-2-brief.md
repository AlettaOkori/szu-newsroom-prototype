### Task 2: 错落排版 + 悬停 CSS

**Files:**
- Modify: `demo/assets/styles.css`
- Test: 浏览器悬停分镜框

**Interfaces:**
- Consumes: Task 1 的 class 名：`.storyboard`、`.storyboard-frame`、`.shape-*`、`.accent-*`、`.is-current`、`.is-armed`、`.storyboard-caption`、`.storyboard-lines`、`.storyboard-copy`、`.kanban-compact`
- Produces: 视觉行为符合设计 §3 / §5

- [ ] **Step 1: 在 `styles.css` 的 `/* dashboard */` 段落后追加分镜与压缩看板样式**

```css
/* M0 storyboard hero */
.storyboard-heading{margin:8px 0 6px;font-size:22px}
.kanban-heading{margin:28px 0 10px;font-size:18px;color:var(--muted)}
.storyboard{
  display:flex;align-items:flex-start;justify-content:center;gap:18px;
  min-height:340px;padding:28px 8px 36px;margin:0 0 8px;
  background:#fff;border:1px solid var(--line);overflow-x:auto;
}
.storyboard:hover .storyboard-frame:not(:hover):not(:focus-visible):not(.is-armed),
.storyboard:has(.storyboard-frame:focus-visible) .storyboard-frame:not(:focus-visible):not(.is-armed){
  opacity:.55;
}
.storyboard-frame{
  --accent:#ffe96b;
  position:relative;flex:0 0 auto;width:148px;text-decoration:none;color:var(--ink);
  display:flex;flex-direction:column;align-items:center;gap:10px;
  transition:transform .2s ease,opacity .2s ease,filter .2s ease;
  scroll-snap-align:center;
}
.storyboard-frame.shape-tall{width:128px}
.storyboard-frame.shape-wide{width:168px}
.storyboard-frame:nth-child(1){margin-top:36px}
.storyboard-frame:nth-child(2){margin-top:88px}
.storyboard-frame:nth-child(3){margin-top:28px}
.storyboard-frame:nth-child(4){margin-top:96px}
.storyboard-frame:nth-child(5){margin-top:12px}
.storyboard-frame:nth-child(6){margin-top:84px}
.storyboard-frame.accent-yellow{--accent:#ffe96b}
.storyboard-frame.accent-cyan{--accent:#9fd8dd}
.storyboard-frame.accent-pink{--accent:#f3b3c2}
.storyboard-frame.accent-red{--accent:#e9b5bf}
.storyboard-art{
  position:relative;display:block;width:100%;aspect-ratio:1;background:#fff;
  border:2.5px solid var(--ink);box-shadow:none;overflow:visible;
  transition:background-color .2s ease,transform .2s ease,box-shadow .2s ease;
}
.storyboard-frame.shape-tall .storyboard-art{aspect-ratio:3/4}
.storyboard-frame.shape-wide .storyboard-art{aspect-ratio:5/3}
.storyboard-art img{width:100%;height:100%;object-fit:contain;display:block;pointer-events:none}
.storyboard-frame.is-current .storyboard-art:before{
  content:"";position:absolute;left:-7px;top:12%;bottom:12%;width:3px;background:var(--red);
}
.storyboard-caption{min-height:42px;width:100%;text-align:center;position:relative}
.storyboard-lines:before,.storyboard-lines:after{
  content:"";display:block;height:2px;background:#cfc8ba;margin:7px auto;border-radius:1px;
}
.storyboard-lines:before{width:72%}.storyboard-lines:after{width:54%}
.storyboard-copy{display:none;flex-direction:column;gap:2px}
.storyboard-copy b{font:700 13px Georgia,"Noto Serif SC",serif}
.storyboard-copy small{font-size:11px;color:var(--muted);line-height:1.35}
.storyboard-frame:hover,.storyboard-frame:focus-visible,.storyboard-frame.is-armed{
  transform:translateY(-6px) scale(1.04);opacity:1;z-index:2;outline:none;
}
.storyboard-frame:hover .storyboard-art,
.storyboard-frame:focus-visible .storyboard-art,
.storyboard-frame.is-armed .storyboard-art{
  background:color-mix(in srgb,var(--accent) 28%,#fff);
  box-shadow:0 10px 0 rgba(26,24,23,.06);
}
.storyboard-frame:hover .storyboard-lines,
.storyboard-frame:focus-visible .storyboard-lines,
.storyboard-frame.is-armed .storyboard-lines{display:none}
.storyboard-frame:hover .storyboard-copy,
.storyboard-frame:focus-visible .storyboard-copy,
.storyboard-frame.is-armed .storyboard-copy{display:flex}
.storyboard-frame:active{transform:translateY(-2px) scale(.98)}
.kanban.kanban-compact{min-height:280px}
.kanban.kanban-compact .kanban-col{padding:8px}
.kanban.kanban-compact .story-card{padding:10px;margin-bottom:8px}
.kanban.kanban-compact .story-card h4{font-size:12px}
@media (max-width:1100px){
  .storyboard{justify-content:flex-start;scroll-snap-type:x proximity;padding-bottom:20px}
  .storyboard-frame{margin-top:24px!important}
}
@media (prefers-reduced-motion:reduce){
  .storyboard-frame,.storyboard-art{transition:none}
  .storyboard-frame:hover,.storyboard-frame:focus-visible,.storyboard-frame.is-armed,
  .storyboard-frame:active{transform:none}
}
```

若目标浏览器对 `color-mix` 支持不足，改用固定浅色：

```css
.storyboard-frame.accent-yellow:hover .storyboard-art,
.storyboard-frame.accent-yellow:focus-visible .storyboard-art,
.storyboard-frame.accent-yellow.is-armed .storyboard-art{background:#fff8d0}
.storyboard-frame.accent-cyan:hover .storyboard-art,
.storyboard-frame.accent-cyan:focus-visible .storyboard-art,
.storyboard-frame.accent-cyan.is-armed .storyboard-art{background:#e7f6f8}
.storyboard-frame.accent-pink:hover .storyboard-art,
.storyboard-frame.accent-pink:focus-visible .storyboard-art,
.storyboard-frame.accent-pink.is-armed .storyboard-art{background:#fde8ee}
.storyboard-frame.accent-red:hover .storyboard-art,
.storyboard-frame.accent-red:focus-visible .storyboard-art,
.storyboard-frame.accent-red.is-armed .storyboard-art{background:#f9e9ec}
```

（实现时二选一即可；优先固定浅色以保证离线老 Edge 稳定。）

- [ ] **Step 2: 浏览器验收布局**

打开 M0：六框呈高低错落；悬停一框时其上浮、浅底出现、旁白替换横线、其余变淡；当前阶段有左侧红标（初始 `storyStatus==="线索"` 时在 A1）。

---
