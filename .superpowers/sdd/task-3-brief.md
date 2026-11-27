### Task 3: 六帧精细漫画 SVG

**Files:**
- Create: `demo/assets/frames/a1-topics.svg`
- Create: `demo/assets/frames/a2-collection.svg`
- Create: `demo/assets/frames/a3-writing.svg`
- Create: `demo/assets/frames/a4-review.svg`
- Create: `demo/assets/frames/a5-channels.svg`
- Create: `demo/assets/frames/a6-insights.svg`

**Interfaces:**
- Consumes: 设计文档 §4 语义与 §4.1 精细度门槛
- Produces: 六个 `viewBox="0 0 200 200"`（tall/wide 可用 `0 0 160 220` / `0 0 240 150`）的手绘感 SVG；`stroke="#1a1817"`；淡彩仅用 `#ffe96b` / `#9fd8dd` / `#f3b3c2` / `#e9b5bf` 填 1–2 物件；背景透明

**Quality bar (blocker):** 对照用户参考截图。若某帧像图标或火柴人，不得标完成——继续加 path 细节（头发分缕、衣褶、手指、道具厚度、抖动描边）。

- [ ] **Step 1: 创建目录并绘制 A1 `a1-topics.svg`**

语义：编辑侧坐看热力屏，手持选题卡；屏上淡彩黄热区；线稿含头发、眉眼、衣领、座椅一角。使用多段 `path`，`stroke-linecap="round"`，局部 `stroke-width` 在 1.6–3.2 间变化。文件需为完整可渲染 SVG（含 `xmlns`）。

最小结构示例（实现时必须远比此更密，此仅示命名空间与图层习惯）：

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none">
  <rect x="18" y="22" width="164" height="156" rx="2" stroke="#1a1817" stroke-width="2.4"/>
  <!-- 以下为示意层名：实际提交需完整手绘人物+道具 path，禁止只留注释 -->
</svg>
```

实现者须用真实 path 填满画面；验收时打开 SVG 文件单独预览。

- [ ] **Step 2: 绘制 A2 `a2-collection.svg`（tall，`viewBox="0 0 160 220"`）**

记者戴耳机、持录音笔或麦克风；身侧散落素材纸片；耳机垫或麦头用青色 `#9fd8dd` 填充。

- [ ] **Step 3: 绘制 A3 `a3-writing.svg`**

人物上半身探出上沿或侧沿打字；黄色纸页飞出框外一点；键盘/笔可见。

- [ ] **Step 4: 绘制 A4 `a4-review.svg`**

伏案人物 + 打开的稿纸；红色浅底批注条或红笔（`#e9b5bf` / 描边可略偏红但不使用高饱和 neon）。

- [ ] **Step 5: 绘制 A5 `a5-channels.svg`（含溢出）**

框内人物持手机/面对多屏；**框外**右上或上方画浅青无人机 + 波浪轨迹（`stroke-dasharray` 可选）；袜子或手机壳可用粉 `#f3b3c2`。溢出元素的坐标可超出内框矩形，由父级 `.storyboard-art { overflow: visible }` 显示。

- [ ] **Step 6: 绘制 A6 `a6-insights.svg`（wide，`viewBox="0 0 240 150"`）**

人物戴耳机看笔记本/仪表；屏上青色节点或折线；键盘与耳机线有手绘抖动。

- [ ] **Step 7: 目视对照参考截图**

并排打开用户参考图与 M0 页。检查清单（全部勾选才过）：

1. 线不是均匀 1px 几何描边  
2. 每框能认出具体动作与道具  
3. 只有局部上色  
4. A5 有框外运动元素  
5. 投屏距离下六框气质统一、像同一套分镜而非六种图标集  

不通过则继续改 SVG，不进入 Task 4 验收关闭。

---
