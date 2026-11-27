### Task 1: 分镜元数据 + Hero 结构壳

**Files:**
- Modify: `demo/assets/data.js`
- Modify: `demo/assets/app.js`（`renderDashboard`）
- Test: 浏览器打开 `demo/pages/m0-dashboard.html`；Node 检查 JS 语法

**Interfaces:**
- Consumes: `D.steps`（现有）
- Produces: `D.pipelineFrames` — 长度 6 的数组，元素形状：
  ```js
  {
    id: "topics"|"collection"|"writing"|"review"|"channels"|"insights",
    code: "A1"|"A2"|"A3"|"A4"|"A5"|"A6",
    name: string,
    blurb: string,          // ≤18 汉字职责句
    accent: "yellow"|"cyan"|"pink"|"red",
    frame: "a1-topics.svg", // 相对 frames/ 的文件名
    shape: "square"|"tall"|"wide" // 框比例暗示
  }
  ```
- Produces: `frameHTML(frames, idx)` 辅助函数（可写在 `app.js` 内），返回 Hero section 字符串

- [ ] **Step 1: 在 `data.js` 的 `ZM_DATA` 中增加 `pipelineFrames`**

在 `steps` 数组之后插入（文案逐字使用设计文档 §4.2）：

```js
pipelineFrames: [
  { id: "topics", code: "A1", name: "智能选题", blurb: "聚合热点，决定报道角度", accent: "yellow", frame: "a1-topics.svg", shape: "square" },
  { id: "collection", code: "A2", name: "智能采集", blurb: "公开资料与原创采录并行", accent: "cyan", frame: "a2-collection.svg", shape: "tall" },
  { id: "writing", code: "A3", name: "智能写作", blurb: "多信源成稿，人机共写", accent: "yellow", frame: "a3-writing.svg", shape: "square" },
  { id: "review", code: "A4", name: "智能审校", blurb: "证据核对，总编签发", accent: "red", frame: "a4-review.svg", shape: "square" },
  { id: "channels", code: "A5", name: "全渠道分发", blurb: "一稿适配多平台发布", accent: "pink", frame: "a5-channels.svg", shape: "square" },
  { id: "insights", code: "A6", name: "效果洞察", blurb: "读传播信号，回流选题", accent: "cyan", frame: "a6-insights.svg", shape: "wide" }
],
```

- [ ] **Step 2: 在 `app.js` 增加 `storyboardHTML(idx)`**

放在 `renderDashboard` 之前：

```js
function storyboardHTML(idx){
  return `<section class="storyboard" aria-label="生产流水线分镜">${D.pipelineFrames.map((f,i)=>{
    const step=D.steps.find(s=>s.id===f.id);
    const href=step?step.file:"#";
    return `<a class="storyboard-frame shape-${f.shape} accent-${f.accent}${i===idx?" is-current":""}" href="${href}" data-frame="${f.id}" data-frame-index="${i}" aria-label="${f.code} ${f.name}，${f.blurb}">
      <span class="storyboard-art" aria-hidden="true"><img src="../assets/frames/${f.frame}" alt="" width="220" height="220" loading="lazy"></span>
      <span class="storyboard-caption"><span class="storyboard-lines" aria-hidden="true"></span><span class="storyboard-copy"><b>${f.code} ${f.name}</b><small>${f.blurb}</small></span></span>
    </a>`;
  }).join("")}</section>`;
}
function goFrame(id,full){
  const step=D.steps.find(s=>s.id===id);
  if(!step)return;
  if(full)renderPage(id,true);
  else location.href=step.file;
}
function bindStoryboard(full){
  let armed=null;
  $$("[data-frame]").forEach(el=>{
    el.addEventListener("click",e=>{
      const id=el.dataset.frame;
      const coarse=matchMedia("(hover:none)").matches;
      if(coarse){
        if(armed!==id){
          e.preventDefault();
          $$("[data-frame]").forEach(x=>x.classList.toggle("is-armed",x.dataset.frame===id));
          armed=id;
          return;
        }
      }
      e.preventDefault();
      goFrame(id,full);
    });
  });
}
```

- [ ] **Step 3: 改写 `renderDashboard` 插入 Hero，并截断灰卡**

将 `renderDashboard` 主体替换为（保留原 `stats` / `idx` / `target` / `statusLabel` 计算）：

```js
function renderDashboard(full){
  const stats=[["328","今日新增线索"],["12","在产稿件"],["47","本周已发布"],["63%","采编平均提效"]];
  const ghosts=[["台风“木兰”路径追踪","AI眼镜消费观察"],["城中村改造两年回访"],["音乐节效应复盘","地铁33号线体验"],["高考录取数据解读"],["暑期文旅消费图鉴"],["社区食堂调查","跨境电商新政"]];
  const idx={线索:0,选题卡:1,素材就绪:2,草稿:2,审校中:3,待分发:4,已发布:5,已复盘:5}[state.storyStatus]??0;
  const target=["topics","collection","writing","review","channels","insights"][idx];
  const statusLabel={线索:"等待立项",选题卡:"采集中",素材就绪:"素材就绪",草稿:"撰写中",审校中:"审校中",待分发:"已签发",已发布:"已发布",已复盘:"已复盘"}[state.storyStatus];
  const slimGhosts=ghosts.map(col=>col.slice(0,2));
  shell("dashboard",
    head("M0","编辑部工作台","一条新闻从线索到复盘的完整旅程",
      `<button class="btn primary" id="start">${state.storyStatus==="线索"?"开始演示":"继续当前稿件"} →</button>`)+
    `<section class="grid stats">${stats.map(x=>`<div class="card stat"><b>${x[0]}</b><span>${x[1]}</span></div>`).join("")}</section>`+
    `<h2 class="storyboard-heading">生产流水线</h2>`+
    storyboardHTML(idx)+
    `<h2 class="kanban-heading">稿件看板</h2>`+
    `<section class="kanban kanban-compact">${D.steps.slice(1).map((s,i)=>`<div class="kanban-col"><h3>${s.code} ${s.name} <span class="pill">${slimGhosts[i].length+(i===idx?1:0)}</span></h3>${i===idx?`<div class="story-card main" data-open="${target}"><h4>${state.storyStatus==="线索"?"（等待立项）新选题":D.topicCard.title}</h4><small>${statusLabel} · ${role(target)[0]}</small></div>`:""}${slimGhosts[i].map(g=>`<div class="story-card ghost"><h4>${g}</h4><small>编辑部稿件</small></div>`).join("")}</div>`).join("")}</section>`,
    full);
  $("#start").innerHTML=`${state.storyStatus==="线索"?"启动流程":"继续当前稿件"} →`;
  $("#start").onclick=()=>full?renderPage(target,true):location.href=`${D.steps.find(x=>x.id===target).file}`;
  $("[data-open]")?.addEventListener("click",()=>full?renderPage(target,true):location.href=`${D.steps.find(x=>x.id===target).file}`);
  bindStoryboard(full);
}
```

注意：`full-demo.html` 下 `goFrame` 必须 `renderPage(id,true)`；分页面模式下 `href` 指向 `../pages` 相对路径——`m0-dashboard.html` 在 `demo/pages/`，故 `step.file` 已是同目录文件名（如 `m1-topics.html`），`href="${href}"` 正确。`img src` 使用 `../assets/frames/...`。

- [ ] **Step 4: 语法检查**

Run:

```powershell
node --check demo/assets/data.js
node --check demo/assets/app.js
```

Expected: 无输出，exit code 0。

- [ ] **Step 5: 浏览器冒烟（图片可 404）**

打开 `demo/pages/m0-dashboard.html`，确认出现 6 个 `.storyboard-frame` 链接、下方仍有 `.kanban-compact`，主按钮仍可点。缺图可接受，Task 3 补齐。

---
