import { spawn } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const expected = [
  ["a1", "A1 智能选题", "策划编辑", "/demo/pages/m1-topics.html"],
  ["a2", "A2 智能采集", "记者", "/demo/pages/m2-collection.html"],
  ["a3", "A3 智能写作", "文字编辑", "/demo/pages/m3-writing.html"],
  ["a4", "A4 智能审校", "审校编辑", "/demo/pages/m4-review.html"],
  ["a5", "A5 全渠道分发", "运营编辑", "/demo/pages/m5-channels.html"],
  ["a6", "A6 效果洞察", "数据分析师", "/demo/pages/m6-insights.html"],
];
const fallbackPoints = [
  "395,217 304,300 386,314 471,229",
  "734,190 553,188 548,223 735,225",
  "970,297 856,220 785,238 896,318",
  "980,478 1065,375 974,350 883,448",
  "566,543 817,563 823,499 584,481",
  "278,398 403,493 491,455 363,365",
];
const expectedDetails = {
  a1: ["智能选题", "TOPIC PLANNING", "聚合热点信号，形成可执行的报道方向。", "查看热点屏、移动选题卡", "#c8102e", "right"],
  a2: ["智能采集", "SMART COLLECTION", "汇集现场采访、音视频与公开信源，整理可用素材。", "戴耳机、整理采访素材", "#e87524", "right"],
  a3: ["智能写作", "ASSISTED WRITING", "组织事实与结构，协同生成并打磨新闻稿件。", "敲键盘、查看稿件", "#2d8c5a", "left"],
  a4: ["智能审校", "SMART REVIEW", "检查事实、语言与规范问题，确认修订结果。", "标记文本、确认问题", "#a83274", "left"],
  a5: ["全渠道分发", "OMNICHANNEL DELIVERY", "适配不同平台形态，编排并发布全渠道内容。", "切换多块平台屏幕", "#d4a514", "left"],
  a6: ["效果洞察", "IMPACT INSIGHTS", "观察传播表现与受众反馈，提炼下一轮优化信号。", "查看图表和传播信号", "#1596a5", "right"],
};
const edge = process.env.EDGE_EXECUTABLE
  || "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const debugPort = Number.parseInt(process.env.EDGE_DEBUG_PORT || "9334", 10);
if (!Number.isInteger(debugPort) || debugPort < 1 || debugPort > 65535) {
  throw new Error("EDGE_DEBUG_PORT must be an integer from 1 to 65535");
}
const viewerUrl = "http://localhost:4173/interactive-newsroom-hero/web/";
const origin = "http://localhost:4173";
const devtoolsUrl = `http://127.0.0.1:${debugPort}`;
const profile = await mkdtemp(join(tmpdir(), "six-desk-edge-"));
const browser = spawn(edge, [
  "--headless=new",
  "--disable-gpu",
  "--no-first-run",
  "--remote-allow-origins=*",
  `--remote-debugging-port=${debugPort}`,
  `--user-data-dir=${profile}`,
  viewerUrl,
], { stdio: "ignore" });

const sleep = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));
const assert = (condition, message) => {
  if (!condition) throw new Error(message);
};

let socket;
let nextId = 1;
let blockVideo = false;
let blockA3 = false;
let blockedVideoRequests = 0;
let blockedA3Requests = 0;
let highlightRequests = 0;
let configOverride = "";
const runtimeExceptions = [];
const pending = new Map();

async function waitForTarget() {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    try {
      const targets = await fetch(`${devtoolsUrl}/json/list`).then(response => response.json());
      const page = targets.find(target => target.type === "page" && target.url.startsWith(viewerUrl));
      if (page) return page;
    } catch {}
    await sleep(100);
  }
  throw new Error("Edge DevTools target did not start");
}

function command(method, params = {}) {
  const id = nextId++;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

async function evaluate(expression) {
  const response = await command("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (response.exceptionDetails) throw new Error(JSON.stringify(response.exceptionDetails));
  return response.result.value;
}

async function waitFor(expression, description, attempts = 70) {
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    if (await evaluate(expression)) return;
    await sleep(100);
  }
  throw new Error(`Timed out waiting for ${description}`);
}

async function waitForWithin(expression, description, maximumMilliseconds) {
  const started = performance.now();
  while (performance.now() - started <= maximumMilliseconds) {
    if (await evaluate(expression)) return performance.now() - started;
    await sleep(10);
  }
  throw new Error(`${description} exceeded ${maximumMilliseconds} ms`);
}

async function loadViewer(suffix = "") {
  await command("Page.navigate", { url: `${viewerUrl}${suffix}` });
  await waitFor(
    "document.readyState === 'complete' && document.querySelectorAll('[data-desk-id]').length === 6",
    `viewer load ${suffix}`,
  );
}

async function touchTap(id) {
  const point = await evaluate(`(() => {
    const bounds = document.querySelector('[data-desk-id="${id}"] polygon').getBoundingClientRect();
    return {x: bounds.left + bounds.width / 2, y: bounds.top + bounds.height / 2};
  })()`);
  await command("Input.dispatchTouchEvent", {
    type: "touchStart",
    touchPoints: [{...point, id: 0, radiusX: 1, radiusY: 1, force: 1}],
  });
  await command("Input.dispatchTouchEvent", {type: "touchEnd", touchPoints: []});
}

async function navigateFrom(id, kind) {
  const target = `${origin}${expected.find(record => record[0] === id)[3]}`;
  if (kind === "enter") {
    await evaluate(`document.querySelector('[data-desk-id="${id}"]').focus()`);
    await command("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
    await command("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
  } else {
    await touchTap(id);
  }
  await waitFor(`location.href === ${JSON.stringify(target)}`, `${kind} navigation for ${id}`);
  await loadViewer();
}

try {
  const target = await waitForTarget();
  socket = new WebSocket(target.webSocketDebuggerUrl);
  socket.addEventListener("message", event => {
    const message = JSON.parse(event.data);
    if (message.method === "Fetch.requestPaused") {
      const url = message.params.request.url;
      if (configOverride && url.includes("scene-data.js")) {
        void command("Fetch.fulfillRequest", {
          requestId: message.params.requestId,
          responseCode: 200,
          responseHeaders: [{name: "Content-Type", value: "application/javascript; charset=utf-8"}],
          body: Buffer.from(configOverride).toString("base64"),
        });
      } else if (blockVideo && url.includes("newsroom.mp4")) {
        blockedVideoRequests += 1;
        void command("Fetch.failRequest", {
          requestId: message.params.requestId,
          errorReason: "BlockedByClient",
        });
      } else if (blockA3 && url.includes("newsroom-a3-highlight.png")) {
        blockedA3Requests += 1;
        void command("Fetch.failRequest", {
          requestId: message.params.requestId,
          errorReason: "BlockedByClient",
        });
      } else {
        void command("Fetch.continueRequest", { requestId: message.params.requestId });
      }
      return;
    }
    if (message.method === "Runtime.exceptionThrown") {
      runtimeExceptions.push(message.params.exceptionDetails.exception?.description
        || message.params.exceptionDetails.text);
    }
    if (message.method === "Network.requestWillBeSent"
        && /newsroom-a[1-6]-highlight\.png/.test(message.params.request.url)) {
      highlightRequests += 1;
    }
    if (!message.id || !pending.has(message.id)) return;
    const { resolve, reject } = pending.get(message.id);
    pending.delete(message.id);
    if (message.error) reject(new Error(message.error.message));
    else resolve(message.result);
  });
  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", reject, { once: true });
  });
  await command("Runtime.enable");
  await command("Page.enable");
  await command("Network.enable");
  await command("Network.setCacheDisabled", { cacheDisabled: true });
  await command("Accessibility.enable");
  await command("Fetch.enable", {
    patterns: [
      { urlPattern: "*scene-data.js*" },
      { urlPattern: "*newsroom.mp4*" },
      { urlPattern: "*newsroom-a3-highlight.png*" },
    ],
  });
  await waitFor(
    "document.readyState === 'complete' && document.querySelectorAll('[data-desk-id]').length === 6",
    "initial viewer load",
  );

  const validFallbackConfig = expected.map(([id, , , destination], index) => ({
    id,
    destination,
    points: fallbackPoints[index],
    color: expectedDetails[id][4],
  }));
  const tinyConfig = validFallbackConfig.map((record, index) => {
    const x = 20 + index * 30;
    return {...record, points: `${x},20 ${x + 10},20 ${x + 10},30 ${x},30`};
  });
  const staleConfig = validFallbackConfig.map(record => (
    record.id === "a3"
      ? {...record, points: "971,297 856,220 785,238 896,318"}
      : record
  ));
  for (const [label, source, expectedError] of [
    [
      "missing",
      "delete window.NEWSROOM_DESKS;",
      "NEWSROOM_DESKS must contain exactly six records",
    ],
    [
      "duplicate",
      `window.NEWSROOM_DESKS = ${JSON.stringify(
        ["a1", "a1", "a3", "a4", "a5", "a6"].map(id => ({id})),
      )};`,
      "NEWSROOM_DESKS IDs must be six unique safe desk IDs",
    ],
    [
      "unsafe",
      `window.NEWSROOM_DESKS = ${JSON.stringify(
        ['a1"] polygon', "a2", "a3", "a4", "a5", "a6"].map(id => ({id})),
      )};`,
      "NEWSROOM_DESKS IDs must be six unique safe desk IDs",
    ],
    [
      "malformed-points",
      `window.NEWSROOM_DESKS = ${JSON.stringify(validFallbackConfig.map(record =>
        record.id === "a3" ? {...record, points: "not-a-polygon"} : record
      ))};`,
      "NEWSROOM_DESKS points must contain valid four-point polygons",
    ],
    [
      "tiny-polygons",
      `window.NEWSROOM_DESKS = ${JSON.stringify(tinyConfig)};`,
      "NEWSROOM_DESKS points must satisfy minimum polygon area",
    ],
    [
      "stale-polygons",
      `window.NEWSROOM_DESKS = ${JSON.stringify(staleConfig)};`,
      "NEWSROOM_DESKS points must match embedded fallback polygons",
    ],
  ]) {
    runtimeExceptions.length = 0;
    configOverride = source;
    await command("Page.navigate", {url: `${viewerUrl}?invalid-config=${label}`});
    await waitFor("document.readyState === 'complete'", `${label} config load`);
    for (let attempt = 0; attempt < 20 && runtimeExceptions.length === 0; attempt += 1) {
      await sleep(25);
    }
    const untouched = await evaluate(`(() => (
      [...document.querySelectorAll(".hit-map a[data-desk-id]")].map(link => ({
        href: new URL(link.getAttribute("href"), location.href).pathname,
        points: link.querySelector("polygon").getAttribute("points"),
        pointCount: link.querySelector("polygon").points.numberOfItems,
        focusable: link.tabIndex >= 0,
      }))
    ))()`);
    assert(
      runtimeExceptions.some(message =>
        message.includes(expectedError)),
      `${label} config was not rejected explicitly: ${JSON.stringify(runtimeExceptions)}`,
    );
    assert(
      untouched.length === 6
      && untouched.every((item, index) =>
        item.href === expected[index][3]
        && item.points === fallbackPoints[index]
        && item.pointCount === 4
        && item.focusable),
      `${label} config changed native fallbacks: ${JSON.stringify(untouched)}`,
    );
  }
  configOverride = "";
  await loadViewer();

  const structure = await evaluate(`(() => {
    const links = [...document.querySelectorAll(".hit-map a[data-desk-id]")];
    return links.map(link => ({
      id: link.dataset.deskId,
      href: new URL(link.getAttribute("href"), location.href).pathname,
      points: link.querySelector("polygon")?.getAttribute("points") || "",
      pointCount: link.querySelector("polygon")?.points.numberOfItems || 0,
    }));
  })()`);
  assert(structure.length === 6, `expected six native SVG links, got ${structure.length}`);
  assert(structure.every((item, index) =>
    item.id === expected[index][0]
    && item.href === expected[index][3]
    && item.pointCount === 4
    && item.points.length > 0
  ), `six-link initialization mismatch: ${JSON.stringify(structure)}`);
  assert(new Set(structure.map(item => item.points)).size === 6, "desk polygons are not distinct");
  console.log("PASS 1: safe unique config initializes six native SVG links in A1-A6 order");
  console.log("PASS 2: six distinct four-point polygons retain expected hrefs");

  for (const [id, module, role] of expected) {
    const [title, english, responsibility, action, color, side] = expectedDetails[id];
    const state = await evaluate(`(() => {
      const link = document.querySelector('[data-desk-id="${id}"]');
      const started = performance.now();
      link.dispatchEvent(new PointerEvent("pointerenter", {pointerType: "mouse"}));
      const elapsed = performance.now() - started;
      const scene = document.querySelector("[data-scene]");
      const card = document.querySelector("[data-card]");
      const highlights = [...document.querySelectorAll("[data-highlight-id]")];
      const activeHighlight = document.querySelector('[data-highlight-id="${id}"]');
      return {
        elapsed,
        active: scene.dataset.activeDesk,
        selected: scene.classList.contains("has-selection"),
        card: card.innerText.replace(/\\s+/g, " ").trim(),
        kicker: card.querySelector("[data-card-kicker]").textContent,
        title: card.querySelector("[data-card-title]").textContent,
        role: card.querySelector("[data-card-role]").textContent,
        responsibility: card.querySelector("[data-card-copy]").textContent,
        action: card.querySelector("[data-card-action]").textContent,
        side: card.dataset.side,
        hidden: card.hidden,
        linkColor: getComputedStyle(link).getPropertyValue("--desk-color").trim(),
        sceneColor: scene.style.getPropertyValue("--desk-color").trim(),
        cardColor: getComputedStyle(card).getPropertyValue("--desk-color").trim(),
        highlightColor: getComputedStyle(activeHighlight).getPropertyValue("--desk-color").trim(),
        videoFilter: getComputedStyle(document.querySelector("[data-video]")).filter,
        expanded: [...document.querySelectorAll("[data-desk-id]")]
          .filter(item => item.getAttribute("aria-expanded") === "true").map(item => item.dataset.deskId),
        highlightDuration: getComputedStyle(activeHighlight).transitionDuration,
        visibleOthers: [...document.querySelectorAll("[data-desk-id]")]
          .filter(item => item !== link)
          .every(item => getComputedStyle(item).display !== "none"
            && item.querySelector("polygon").getBoundingClientRect().width > 0),
      };
    })()`);
    assert(state.elapsed <= 100 && state.active === id && state.selected, `${id} pointer activation failed`);
    assert(
      !state.hidden
      && state.kicker === `${id.toUpperCase()} / ${english}`
      && state.title === title
      && state.role === role
      && state.responsibility === responsibility
      && state.action === action
      && state.card === `${id.toUpperCase()} / ${english} ${title} ${role} ${responsibility} ${action} 点击进入模块 →`,
      `${id} card copy failed: ${JSON.stringify(state)}`,
    );
    assert(
      state.side === side
      && state.linkColor === color
      && state.sceneColor === color
      && state.cardColor === color
      && state.highlightColor === color,
      `${id} exact side/color propagation failed: ${JSON.stringify(state)}`,
    );
    const opacityElapsed = await waitForWithin(
      `[...document.querySelectorAll("[data-highlight-id]")]
        .filter(item => Number.parseFloat(getComputedStyle(item).opacity) > .99)
        .map(item => item.dataset.highlightId).join() === "${id}"`,
      `${id} highlight transition`,
      250,
    );
    const opaque = await evaluate(`[...document.querySelectorAll("[data-highlight-id]")]
      .filter(item => Number.parseFloat(getComputedStyle(item).opacity) > .99)
      .map(item => item.dataset.highlightId)`);
    assert(
      state.expanded.join() === id
      && opaque.join() === id
      && state.highlightDuration === "0.1s"
      && opacityElapsed <= 250,
      `${id} one-active state failed: ${JSON.stringify({state, opaque, opacityElapsed})}`,
    );
    assert(state.visibleOthers, `${id} hid an unselected desk`);
    await waitForWithin(
      `getComputedStyle(document.querySelector("[data-video]")).filter.includes("brightness(0.78)")
        && getComputedStyle(document.querySelector("[data-video]")).filter.includes("saturate(0.72)")`,
      `${id} selected-scene dim transition`,
      350,
    );
    const settledVideoFilter = await evaluate(
      `getComputedStyle(document.querySelector("[data-video]")).filter`,
    );
    assert(
      settledVideoFilter.includes("brightness(0.78)")
      && settledVideoFilter.includes("saturate(0.72)"),
      `${id} did not apply actual selected-scene dimming: ${settledVideoFilter}`,
    );
  }
  console.log("PASS 3: pointer activation updates exact card, side, propagated color, and state within 100 ms");
  console.log("PASS 4: exactly one link expands and one highlight is opaque");
  console.log("PASS 5: non-selected desks remain visible under the measured video dim/filter");

  for (const [id, module] of expected) {
    const keyboard = await evaluate(`(() => {
      const link = document.querySelector('[data-desk-id="${id}"]');
      link.focus();
      const active = document.querySelector("[data-scene]").dataset.activeDesk === "${id}";
      link.dispatchEvent(new KeyboardEvent("keydown", {key: "Escape", bubbles: true, cancelable: true}));
      return {
        active,
        collapsed: document.querySelector("[data-scene]").dataset.activeDesk === ""
          && [...document.querySelectorAll("[data-desk-id]")]
            .every(item => item.getAttribute("aria-expanded") === "false"),
        focused: document.activeElement === link,
        cardHidden: document.querySelector("[data-card]").hidden,
        cardCleared: [...document.querySelectorAll(
          "[data-card-kicker], [data-card-title], [data-card-role], [data-card-copy], [data-card-action]",
        )].every(field => field.textContent === ""),
        status: document.querySelector("[data-status]").textContent,
      };
    })()`);
    assert(
      keyboard.active
      && keyboard.collapsed
      && keyboard.focused
      && keyboard.cardHidden
      && keyboard.cardCleared,
      `${id} focus/Escape collapse failed: ${JSON.stringify(keyboard)}`,
    );
    assert(keyboard.status === `已取消 ${module}。`, `${id} Escape announcement mismatch`);
    await navigateFrom(id, "enter");
  }
  console.log("PASS 6: Escape retains focus while clearing card and collapsing all links; Enter reaches targets");

  await command("Emulation.setTouchEmulationEnabled", {
    enabled: true,
    maxTouchPoints: 1,
  });
  for (const [id] of expected) {
    await touchTap(id);
    const firstTap = await evaluate(`(() => ({
      active: document.querySelector("[data-scene]").dataset.activeDesk,
      href: location.href,
    }))()`);
    assert(firstTap.active === id && firstTap.href === viewerUrl, `${id} first touch tap navigated`);
    await navigateFrom(id, "touch");
  }
  await command("Emulation.setTouchEmulationEnabled", {enabled: false});
  console.log("PASS 7: real CDP touch input selects first and reaches every target on second tap");

  blockVideo = true;
  await loadViewer("?blocked-video=1");
  await waitFor("document.querySelector('[data-scene]').classList.contains('video-failed')", "video fallback");
  const videoFailure = await evaluate(`(() => {
    document.querySelector('[data-desk-id="a2"]').dispatchEvent(
      new PointerEvent("pointerenter", {pointerType: "mouse"})
    );
    return {
      video: getComputedStyle(document.querySelector("[data-video]")).display,
      cover: getComputedStyle(document.querySelector("[data-scene]")).backgroundImage,
      active: document.querySelector("[data-scene]").dataset.activeDesk,
      fallback: document.querySelector("[data-fallback]").textContent,
    };
  })()`);
  assert(blockedVideoRequests > 0 && videoFailure.video === "none", "blocked video did not hide");
  assert(videoFailure.cover.includes("newsroom-cover.png") && videoFailure.active === "a2", "video fallback unusable");
  assert(videoFailure.fallback.includes("动画未加载"), "video fallback was not announced");
  for (const [id] of expected) {
    await navigateFrom(id, "enter");
    await waitFor(
      "document.querySelector('[data-scene]').classList.contains('video-failed')",
      `video fallback after ${id} navigation`,
    );
  }
  blockVideo = false;
  console.log("PASS 8: blocked newsroom.mp4 shows cover and all six native links still navigate");

  blockA3 = true;
  await loadViewer("?blocked-a3=1");
  await waitFor("document.querySelector('[data-scene]').classList.contains('highlight-failed') === false", "A3 initial state");
  const failedHighlight = await evaluate(`new Promise(resolve => {
    setTimeout(() => {
      const link = document.querySelector('[data-desk-id="a3"]');
      link.dispatchEvent(new PointerEvent("pointerenter", {pointerType: "mouse"}));
      const polygon = link.querySelector("polygon");
      resolve({
        failed: document.querySelector("[data-scene]").classList.contains("highlight-failed"),
        stroke: getComputedStyle(polygon).stroke,
        width: getComputedStyle(polygon).strokeWidth,
      });
    }, 150);
  })`);
  assert(blockedA3Requests > 0 && failedHighlight.failed, "A3 highlight failure state missing");
  await waitFor(
    `getComputedStyle(document.querySelector('[data-desk-id="a3"] polygon')).stroke
      !== "rgba(0, 0, 0, 0)"`,
    "A3 fallback ring transition",
  );
  const failedRing = await evaluate(`(() => {
    const style = getComputedStyle(document.querySelector('[data-desk-id="a3"] polygon'));
    return {stroke: style.stroke, width: style.strokeWidth};
  })()`);
  assert(
    Number.parseFloat(failedRing.width) >= 4,
    `A3 ring missing: ${JSON.stringify(failedRing)}`,
  );
  await navigateFrom("a3", "enter");
  blockA3 = false;
  console.log("PASS 9: blocked A3 highlight uses SVG ring and retains navigation");

  await command("Emulation.setEmulatedMedia", {
    media: "screen",
    features: [{ name: "prefers-reduced-motion", value: "reduce" }],
  });
  highlightRequests = 0;
  await loadViewer("?reduced=1");
  const reduced = await evaluate(`(() => {
    const link = document.querySelector('[data-desk-id="a1"]');
    link.dispatchEvent(new PointerEvent("pointerenter", {pointerType: "mouse"}));
    return {
      paused: document.querySelector("[data-video]").paused,
      video: getComputedStyle(document.querySelector("[data-video]")).display,
      cover: getComputedStyle(document.querySelector("[data-scene]")).backgroundImage,
      stack: getComputedStyle(document.querySelector(".highlight-stack")).display,
      transition: getComputedStyle(document.querySelector('[data-highlight-id="a1"]')).transitionDuration,
      sources: [...document.querySelectorAll("[data-highlight-id]")]
        .map(image => image.getAttribute("src")),
      opacity: [...document.querySelectorAll("[data-highlight-id]")]
        .map(image => getComputedStyle(image).opacity),
      active: document.querySelector("[data-scene]").dataset.activeDesk,
    };
  })()`);
  assert(
    reduced.paused
    && reduced.video === "none"
    && reduced.cover.includes("newsroom-cover.png")
    && reduced.stack === "none"
    && reduced.transition === "0s"
    && reduced.sources.every(source => source === null)
    && reduced.opacity.every(opacity => opacity === "0")
    && reduced.active === "a1"
    && highlightRequests === 0,
    `reduced motion loaded or displayed response imagery: ${JSON.stringify({reduced, highlightRequests})}`,
  );
  const reducedStart = Date.now();
  await evaluate(`document.querySelector('[data-desk-id="a1"]').dispatchEvent(
    new MouseEvent("click", {bubbles: true, cancelable: true})
  )`);
  await waitFor(`location.pathname === ${JSON.stringify(expected[0][3])}`, "reduced-motion navigation");
  assert(Date.now() - reducedStart < 350, "reduced-motion navigation used confirmation delay");
  console.log("PASS 10: reduced motion uses cover and SVG/card only, requests no highlights, and navigates immediately");

  await command("Emulation.setEmulatedMedia", { media: "screen", features: [] });
  const lowPerformanceInjection = await command("Page.addScriptToEvaluateOnNewDocument", {
    source: `Object.defineProperty(navigator, "hardwareConcurrency", {get: () => 2, configurable: true});`,
  });
  highlightRequests = 0;
  await loadViewer("?low-performance=1");
  await sleep(250);
  const lowPerformance = await evaluate(`(() => {
    document.querySelector('[data-desk-id="a4"]').dispatchEvent(
      new PointerEvent("pointerenter", {pointerType: "mouse"})
    );
    return {
      cores: navigator.hardwareConcurrency,
      mode: document.querySelector("[data-scene]").classList.contains("low-performance"),
      paused: document.querySelector("[data-video]").paused,
      video: getComputedStyle(document.querySelector("[data-video]")).display,
      cover: getComputedStyle(document.querySelector("[data-scene]")).backgroundImage,
      active: document.querySelector("[data-scene]").dataset.activeDesk,
      color: document.querySelector("[data-scene]").style.getPropertyValue("--desk-color").trim(),
      sources: [...document.querySelectorAll("[data-highlight-id]")].map(image => image.getAttribute("src")),
    };
  })()`);
  assert(lowPerformance.cores === 2 && lowPerformance.mode && lowPerformance.paused, "low-performance mode missing");
  assert(lowPerformance.video === "none" && lowPerformance.cover.includes("newsroom-cover.png"), "low-performance cover missing");
  assert(highlightRequests === 0 && lowPerformance.sources.every(source => source === null), "low-performance fetched highlights");
  await waitForWithin(
    `getComputedStyle(document.querySelector('[data-desk-id="a4"] polygon')).stroke
      !== "rgba(0, 0, 0, 0)"`,
    "low-performance selected ring",
    250,
  );
  const lowPerformanceRing = await evaluate(`(() => {
    const style = getComputedStyle(document.querySelector('[data-desk-id="a4"] polygon'));
    return {stroke: style.stroke, width: style.strokeWidth, fill: style.fill};
  })()`);
  assert(
    lowPerformance.active === "a4"
    && lowPerformance.color === expectedDetails.a4[4]
    && Number.parseFloat(lowPerformanceRing.width) >= 4
    && lowPerformanceRing.fill !== "rgba(0, 0, 0, 0)",
    `low-performance selected ring missing: ${JSON.stringify({lowPerformance, lowPerformanceRing})}`,
  );
  await navigateFrom("a4", "enter");
  await command("Page.removeScriptToEvaluateOnNewDocument", { identifier: lowPerformanceInjection.identifier });
  console.log("PASS 11: low-performance mode shows selected ring, makes zero highlight requests, and navigates");

  await loadViewer("?missing-a6=1");
  const missing = await evaluate(`new Promise(resolve => {
    const link = document.querySelector('[data-desk-id="a6"]');
    link.setAttribute("href", "../../demo/pages/m6-missing.html");
    link.dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}));
    setTimeout(() => resolve({
      href: location.href,
      confirming: document.querySelector("[data-scene]").classList.contains("is-confirming"),
      status: document.querySelector("[data-status]").textContent,
    }), 500);
  })`);
  assert(missing.href.includes("missing-a6=1") && !missing.confirming, "404 destination navigated or stayed confirming");
  assert(missing.status === "目标页面暂不可用，请稍后重试。", "404 announcement mismatch");
  console.log("PASS 12: A6 404 is blocked and announces the exact failure message");

  const autoplayInjection = await command("Page.addScriptToEvaluateOnNewDocument", {
    source: `(() => {
      const nativePlay = HTMLMediaElement.prototype.play;
      window.__playAttempts = 0;
      HTMLMediaElement.prototype.play = function () {
        window.__playAttempts += 1;
        if (window.__playAttempts === 1) {
          return Promise.reject(new DOMException("Blocked by smoke", "NotAllowedError"));
        }
        return nativePlay.call(this);
      };
    })();`,
  });
  await loadViewer("?autoplay=1");
  await waitFor("window.__playAttempts === 1", "autoplay rejection");
  await evaluate(`document.dispatchEvent(new PointerEvent("pointerdown", {pointerType: "mouse", bubbles: true}))`);
  await waitFor("window.__playAttempts >= 2", "autoplay retry");
  const autoplay = await evaluate(`new Promise(resolve => {
    const start = document.querySelector("[data-video]").currentTime;
    setTimeout(() => resolve({
      attempts: window.__playAttempts,
      progressed: document.querySelector("[data-video]").currentTime > start,
    }), 250);
  })`);
  assert(autoplay.attempts >= 2 && autoplay.progressed, "autoplay retry did not recover playback");
  await command("Page.removeScriptToEvaluateOnNewDocument", { identifier: autoplayInjection.identifier });
  console.log("PASS 13: autoplay rejection retries on first pointer interaction");

  await loadViewer("?natural-loop=1");
  await waitFor("document.querySelector('[data-video]').readyState >= 1", "video metadata");
  let maxPlaybackTime = 0;
  let restartTime = null;
  for (let attempt = 0; attempt < 70; attempt += 1) {
    const currentTime = await evaluate("document.querySelector('[data-video]').currentTime");
    maxPlaybackTime = Math.max(maxPlaybackTime, currentTime);
    if (maxPlaybackTime > 4.5 && currentTime >= 20 / 24 && currentTime < 2) {
      restartTime = currentTime;
      break;
    }
    await sleep(100);
  }
  assert(restartTime !== null, `natural playback did not seek to 20/24 (max ${maxPlaybackTime})`);
  const endedInjection = await command("Page.addScriptToEvaluateOnNewDocument", {
    source: `HTMLMediaElement.prototype.play = function () { return Promise.resolve(); };`,
  });
  await loadViewer("?deterministic-ended=1");
  await waitFor("document.querySelector('[data-video]').readyState >= 1", "deterministic video metadata");
  const endedWrites = await evaluate(`(() => {
    const video = document.querySelector("[data-video]");
    video.pause();
    const writes = [];
    Object.defineProperty(video, "currentTime", {
      configurable: true,
      get: () => writes.at(-1) ?? 4.9,
      set: value => writes.push(value),
    });
    video.dispatchEvent(new Event("ended"));
    return writes;
  })()`);
  await command("Page.removeScriptToEvaluateOnNewDocument", {identifier: endedInjection.identifier});
  const exactRestartTime = endedWrites.at(-1);
  assert(
    Math.abs(exactRestartTime - 20 / 24) < .01,
    `ended handler did not synchronously assign 20/24: ${JSON.stringify(endedWrites)}`,
  );
  console.log(`PASS 14: natural playback ended; deterministic handler seek was ${exactRestartTime.toFixed(3)}s`);

  const media = await evaluate(`(() => {
    const video = document.querySelector("[data-video]");
    return {duration: video.duration, width: video.videoWidth, height: video.videoHeight};
  })()`);
  assert(media.width === 1280 && media.height === 720, `media size ${media.width}x${media.height}`);
  assert(Math.abs(media.duration - 5) < .05, `media duration ${media.duration}`);
  console.log(`PASS 15: media is ${media.width}x${media.height} and ${media.duration.toFixed(3)} seconds`);
} finally {
  if (socket) socket.close();
  browser.kill();
  if (browser.exitCode === null) {
    await new Promise(resolve => browser.once("exit", resolve));
  }
  await rm(profile, { recursive: true, force: true });
}
