### Task 4: full-demo 路径与交互收尾

**Files:**
- Modify: `demo/assets/app.js`（若 Task 1 的 `img` 路径在 full-demo 下错误则修）
- Test: `demo/full-demo.html` 与 `demo/pages/m0-dashboard.html`

**Interfaces:**
- Consumes: `bindStoryboard` / `goFrame`
- Produces: 两种入口下图片与跳转均正确

- [ ] **Step 1: 修正资源路径**

`m0-dashboard.html` 在 `demo/pages/` → `../assets/frames/...`  
`full-demo.html` 在 `demo/` → 若也调用同一 `storyboardHTML`，`img` 会 404。改为按页面位置解析：

```js
function assetBase(){
  return location.pathname.indexOf("/pages/")>=0?"../assets/":"assets/";
}
// storyboardHTML 内：
`<img src="${assetBase()}frames/${f.frame}" alt="" width="220" height="220" loading="lazy">`
```

- [ ] **Step 2: 验证 full-demo**

打开 `demo/full-demo.html`（或站点根对应 URL），确认分镜图加载；点击 A3 进入写作视图且不整页刷新（`renderPage`）；触屏逻辑：模拟 `(hover:none)` 时第一次点加 `.is-armed`，第二次才跳转。

- [ ] **Step 3: 键盘**

Tab 聚焦分镜，Enter 触发与点击相同的 `goFrame`（因是 `<a href>`，原生 Enter 可用；`preventDefault` 后需保证 keydown Enter 也调用 `goFrame`）：

```js
el.addEventListener("keydown",e=>{
  if(e.key!=="Enter"&&e.key!==" ")return;
  e.preventDefault();
  goFrame(el.dataset.frame,full);
});
```

- [ ] **Step 4: 语法复查**

```powershell
node --check demo/assets/app.js
```

Expected: exit 0。

---
