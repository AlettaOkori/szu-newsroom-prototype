# Review package Task 4
## Commits
none
## Stat
 demo/assets/app.js | assetBase, inline SVG load, keyboard
 demo/assets/styles.css | storyboard-svg overflow rule
## app.js region
```js
function assetBase(){return location.pathname.indexOf("/pages/")>=0?"../assets/":"assets/"}
function storyboardHTML(idx){
 return `<section class="storyboard" aria-label="生产流水线分镜">${D.pipelineFrames.map((f,i)=>{
  const step=D.steps.find(s=>s.id===f.id);
  const href=step?step.file:"#";
  return `<a class="storyboard-frame shape-${f.shape} accent-${f.accent}${i===idx?" is-current":""}" href="${href}" data-frame="${f.id}" data-frame-index="${i}" aria-label="${f.code} ${f.name}，${f.blurb}">
   <span class="storyboard-art" aria-hidden="true" data-frame-file="${f.frame}"></span>
   <span class="storyboard-caption"><span class="storyboard-lines" aria-hidden="true"></span><span class="storyboard-copy"><b>${f.code} ${f.name}</b><small>${f.blurb}</small></span></span>
  </a>`;
 }).join("")}</section>`;
}
function fetchSVG(url){
 return fetch(url).then(r=>{if(!r.ok)throw new Error(`Failed to load ${url}`);return r.text()}).catch(()=>new Promise((resolve,reject)=>{
  const xhr=new XMLHttpRequest();
  xhr.open("GET",url,true);
  xhr.onload=()=>xhr.status===0||xhr.status>=200&&xhr.status<300?resolve(xhr.responseText):reject(new Error(`Failed to load ${url}`));
  xhr.onerror=reject;
  xhr.send();
 }))
}
function loadStoryboardArt(){
 $$("[data-frame-file]").forEach(el=>{
  if(el.dataset.loaded)return;
  el.dataset.loaded="true";
  fetchSVG(`${assetBase()}frames/${el.dataset.frameFile}`).then(svg=>{
   el.innerHTML=svg.replace(/^\s*<\?xml[^>]*>\s*/i,"");
   const node=$("svg",el);
   if(node)node.classList.add("storyboard-svg");
  }).catch(()=>{el.dataset.loaded=""});
 });
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
  el.addEventListener("keydown",e=>{
   if(e.key!=="Enter"&&e.key!==" ")return;
   e.preventDefault();
   goFrame(el.dataset.frame,full);
  });
 });
 loadStoryboardArt();
}
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
