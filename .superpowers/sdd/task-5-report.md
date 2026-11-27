# Task 5 验收报告：M0 漫画分镜 Hero

## 结论

状态：DONE

服务路径按要求从仓库根目录启动并验证：

- `python -m http.server 8765`
- `http://localhost:8765/demo/pages/m0-dashboard.html`
- `http://localhost:8765/demo/full-demo.html`

Edge headless 可用；Playwright 不在当前环境中。验收采用 Edge headless 截图 / DOM dump、HTTP served-path 检查、代码路径核对与 SVG/CSS 目视对照完成。`file://` 路径未作为验收依据。

## 运行与烟测记录

- HTTP served-path 检查：
  - `200 http://localhost:8765/demo/pages/m0-dashboard.html`
  - `200 http://localhost:8765/demo/full-demo.html`
  - `200 http://localhost:8765/demo/assets/frames/a5-channels.svg`
- Edge 截图：
  - `.superpowers/sdd/task-5-m0-desktop-final.png`
  - `.superpowers/sdd/task-5-m0-narrow.png`
- Edge DOM dump 确认 `full-demo.html` 渲染出：
  - 6 个 `.storyboard-frame`
  - 6 个外链 SVG 注入后的 `.storyboard-svg`
  - `.kanban.kanban-compact`
- touched file lints：
  - `demo/assets/frames/a5-channels.svg`：No linter errors found.

## §9 验收逐项对照

1. 首屏主视觉为六框错落漫画分镜：PASS
   - M0 首屏中，四个统计卡下方优先展示 `生产流水线` 分镜 Hero。
   - 看板已下移到 Hero 之后，首屏主视觉不再是六列等高看板。

2. 六框语义可辨认为选题 → 采集 → 写作 → 审校 → 分发 → 洞察：PASS
   - A1：编辑 + 热力屏 / 选题卡。
   - A2：记者耳机 / 话筒 / 采录素材。
   - A3：人物举稿 / 多页输出。
   - A4：伏案审校 / 红笔批注。
   - A5：多屏分发 + 无人机轨迹。
   - A6：传播趋势屏 + 分析人员。

3. 插画精细度达到参考截图观感级别：PASS
   - 六框均为多路径线稿，人物具备发型、五官、体态、道具层次。
   - 每框仅局部淡彩：黄 / 青 / 粉 / 红等。
   - A5 无人机已调整为明确溢出 SVG / 分镜边界。

4. 悬停 A + C：轻抬 + 淡彩铺开 + 旁白露出，其余框降透：PASS
   - `.storyboard-frame:hover`, `:focus-visible`, `.is-armed` 均触发 `translateY(-6px) scale(1.04)`。
   - 各 accent class 在 hover/focus/armed 时设置浅底色。
   - 默认 `.storyboard-lines`，交互态切换为 `.storyboard-copy`。
   - `.storyboard:hover ...` 与 `:has(...)` 规则使其他框 `opacity:.55`。

5. 点击分镜进入正确模块；主线卡 / 主按钮行为不变：PASS
   - 分镜 `data-frame` 与 `D.steps` 共用 id，`goFrame(id, full)` 对 standalone 跳文件、full-demo 调 `renderPage(id,true)`。
   - 主按钮仍由 `storyStatus` 推导 `target`。
   - 看板主线卡仍使用 `data-open="${target}"` 进入当前环节。

6. 当前 `storyStatus` 红标与看板列一致：PASS
   - `renderDashboard` 中同一个 `idx` 同时驱动：
     - `.storyboard-frame.is-current`
     - 看板主线卡所在列
     - 主按钮 / 主线卡目标模块
   - 抽测 `storyStatus: "选题卡"` 时，映射目标为 A2 `collection`，看板主线卡进入 A2 采集列。

7. 看板仍可见且更矮；灰卡密度下降：PASS
   - 看板保留在 Hero 下方。
   - `.kanban.kanban-compact` 将 `min-height` 从基础看板的 480px 降到 280px。
   - 灰卡来源通过 `ghosts.map(col=>col.slice(0,2))` 截断，每列最多 1-2 张。

8. 键盘可聚焦分镜并 Enter 进入；`prefers-reduced-motion` 降级正确：PASS
   - 分镜为 `<a>`，天然可聚焦。
   - `bindStoryboard` 监听 `keydown`，Enter / Space 调 `goFrame(...)`。
   - `@media (prefers-reduced-motion:reduce)` 取消 transition 与 transform，仅保留浅底与旁白显隐。

9. 桌面宽度正常；窄屏下分镜可横向滚动，不重叠不可点：PASS
   - 桌面截图正常显示六框错落。
   - 窄屏截图中 `.storyboard` 出现横向滚动条，框体不互相重叠，仍保持可点击区域。
   - `.storyboard{overflow-x:auto}` 与 `@media (max-width:1100px)` 的 `justify-content:flex-start` 生效。

## Task Brief Step 1-2

### Step 1：按 §9 逐条勾选

完成。详见上方 §9 验收逐项对照，9 项均 PASS。

### Step 2：状态一致性抽测

完成。代码路径和 session 状态抽测显示：

- `storyStatus: "线索"` → 当前分镜 `topics`，主线卡在 A1。
- `storyStatus: "选题卡"` → 当前分镜 `collection`，主线卡在 A2 采集列。
- 分镜红标与看板主线列均由 `renderDashboard` 内同一个 `idx` 计算，不存在两套状态源。

## 本次修复

只做了一个小 SVG 修复，未重设计：

- `demo/assets/frames/a5-channels.svg`
  - 将 A5 无人机和轨迹包进 `transform="translate(24 -22)"`。
  - 目的：让无人机明确溢出 SVG / 分镜边界，满足“至少一框有溢出框外元素”的验收要求。
  - 其他分镜、布局和交互逻辑未改。

## 未发现阻塞项

- 两个指定 served URL 均可访问。
- Edge headless 渲染通过。
- 最终截图中 A5 drone 溢出可见。
- touched SVG 无 linter error。

## Final-review fixes（未提交）

### Fix 1：`file://` SVG 加载回退

- 文件：`demo/assets/app.js` → `loadStoryboardArt()`
- 变更：`fetchSVG` 失败时不再清空 `el.dataset.loaded`；改为注入 `<img class="storyboard-svg" src="...">` 作为回退，保留 `loaded=true`，避免 `file://` 下无限重试。

### Fix 2：分镜 peer-dim 仅作用于帧 hover/focus/armed

- 文件：`demo/assets/styles.css`
- 变更：将 `.storyboard:hover ...` 替换为 `:has(.storyboard-frame:hover)` / `:has(:focus-visible)` / `:has(.is-armed)` 作用域规则；合并原独立 `.is-armed` 规则，避免悬停 `.storyboard` 空白 padding 时全体降透。

### 校验

- `node --check demo/assets/app.js` → exit 0
