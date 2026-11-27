import { spawn } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const edge = process.env.EDGE_EXECUTABLE
  || "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const debugPort = Number.parseInt(process.env.EDGE_DEBUG_PORT || "9222", 10);
if (!Number.isInteger(debugPort) || debugPort < 1 || debugPort > 65535) {
  throw new Error("EDGE_DEBUG_PORT must be an integer from 1 to 65535");
}
const devtoolsUrl = `http://127.0.0.1:${debugPort}`;
const viewerUrl = "http://localhost:4173/interactive-newsroom-hero/web/sample/";
const targetUrl = "http://localhost:4173/demo/pages/m1-topics.html";
const profile = await mkdtemp(join(tmpdir(), "task4-edge-"));
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
let blockedMp4Requests = 0;
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
  if (response.exceptionDetails) {
    throw new Error(JSON.stringify(response.exceptionDetails));
  }
  return response.result.value;
}

async function waitFor(expression, description) {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    if (await evaluate(expression)) return;
    await sleep(100);
  }
  throw new Error(`Timed out waiting for ${description}`);
}

try {
  const target = await waitForTarget();
  socket = new WebSocket(target.webSocketDebuggerUrl);
  socket.addEventListener("message", event => {
    const message = JSON.parse(event.data);
    if (message.method === "Fetch.requestPaused") {
      if (message.params.request.url.includes("sample.mp4")) {
        blockedMp4Requests += 1;
        void command("Fetch.failRequest", {
          requestId: message.params.requestId,
          errorReason: "BlockedByClient",
        });
      } else {
        void command("Fetch.continueRequest", { requestId: message.params.requestId });
      }
      return;
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
  await command("Accessibility.enable");
  await waitFor(
    `location.href === ${JSON.stringify(viewerUrl)} && document.readyState === "complete" && !!document.querySelector("[data-video]")`,
    "viewer load",
  );
  await waitFor("document.querySelector('[data-video]')?.readyState >= 1", "video metadata");

  const semantics = await evaluate(`(() => {
    const desk = document.querySelector("[data-desk]");
    const card = document.querySelector("[data-card]");
    const status = document.querySelector("[data-status]");
    const fallback = document.querySelector("[data-fallback]");
    return {
      tagName: desk.tagName,
      destination: desk.href,
      expanded: desk.getAttribute("aria-expanded"),
      controls: desk.getAttribute("aria-controls"),
      cardHidden: card.hidden,
      statusEmpty: status?.textContent === "",
      fallbackRole: fallback.getAttribute("role"),
      fallbackEmpty: fallback.textContent === "",
    };
  })()`);
  assert(semantics.tagName === "A" && semantics.destination === targetUrl, "desk is not a native destination link");
  assert(semantics.expanded === "false" && semantics.controls === "role-card", "link disclosure semantics missing");
  assert(semantics.cardHidden && semantics.statusEmpty, "inactive role content is exposed");
  assert(semantics.fallbackRole === "status" && semantics.fallbackEmpty, "fallback live region is not initially empty");
  const initialAxTree = await command("Accessibility.getFullAXTree");
  const initialAxText = initialAxTree.nodes.map(node => node.name?.value || "").join("\n");
  assert(!initialAxText.includes("聚合热点信号"), "inactive role-card copy is present in the accessibility tree");
  assert(!initialAxText.includes("动画未加载"), "inactive fallback copy is present in the accessibility tree");

  const media = await evaluate(`(() => {
    const video = document.querySelector("[data-video]");
    return { duration: video.duration, width: video.videoWidth, height: video.videoHeight };
  })()`);
  assert(Math.abs(media.duration - 5) < 0.05, `unexpected video duration ${media.duration}`);
  assert(media.width === 1280 && media.height === 720, `unexpected video size ${media.width}x${media.height}`);

  let maxPlaybackTime = 0;
  let naturalRestartTime = null;
  for (let attempt = 0; attempt < 70; attempt += 1) {
    const currentTime = await evaluate("document.querySelector('[data-video]').currentTime");
    maxPlaybackTime = Math.max(maxPlaybackTime, currentTime);
    if (maxPlaybackTime > 4.5 && currentTime >= 20 / 24 && currentTime < 2) {
      naturalRestartTime = currentTime;
      break;
    }
    await sleep(100);
  }
  assert(naturalRestartTime !== null, `video did not naturally restart from idle (max ${maxPlaybackTime})`);
  assert(
    !(await evaluate(`document.querySelector("[data-scene]").classList.contains("video-failed")`)),
    "successful media readiness was falsely marked as failed",
  );

  const redPixelCount = await evaluate(`new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = image.naturalWidth;
      canvas.height = image.naturalHeight;
      const context = canvas.getContext("2d");
      context.drawImage(image, 0, 0);
      const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
      let count = 0;
      for (let offset = 0; offset < pixels.length; offset += 64) {
        if (pixels[offset] > 180 && pixels[offset + 1] < 150 && pixels[offset + 2] < 170) count += 1;
      }
      resolve(count);
    };
    image.onerror = reject;
    image.src = "assets/sample-cover.png";
  })`);
  assert(redPixelCount > 100, `red clothing pixels not detected (${redPixelCount})`);

  const hover = await evaluate(`(() => {
    const desk = document.querySelector("[data-desk]");
    desk.dispatchEvent(new PointerEvent("pointerenter", { pointerType: "mouse" }));
    const highlight = getComputedStyle(document.querySelector("[data-highlight]"));
    const card = getComputedStyle(document.querySelector("[data-card]"));
    return {
      active: document.querySelector("[data-scene]").classList.contains("is-active"),
      highlightOpacity: highlight.opacity,
      highlightDuration: highlight.transitionDuration,
      cardOpacity: card.opacity,
      cardText: document.querySelector("[data-card]").innerText,
      cardHidden: document.querySelector("[data-card]").hidden,
      expanded: desk.getAttribute("aria-expanded"),
      statusText: document.querySelector("[data-status]").textContent,
    };
  })()`);
  assert(hover.active, "hover did not activate scene");
  assert(hover.highlightDuration === "0.1s", `unexpected highlight duration ${hover.highlightDuration}`);
  assert(!hover.cardHidden && hover.expanded === "true", "active disclosure semantics missing");
  assert(hover.statusText.includes("A1 智能选题"), "selection was not announced");
  const activeAxTree = await command("Accessibility.getFullAXTree");
  const activeAxText = activeAxTree.nodes.map(node => node.name?.value || "").join("\n");
  assert(activeAxText.includes("聚合热点信号"), "selected role-card copy is absent from the accessibility tree");
  assert(hover.cardText.includes("A1 / TOPIC PLANNING"), "card missing A1");
  assert(hover.cardText.includes("智能选题"), "card missing topic title");
  assert(hover.cardText.includes("策划编辑"), "card missing role");
  assert(hover.cardText.includes("聚合热点信号，形成可执行的报道方向。"), "card missing responsibility");
  assert(hover.cardText.includes("点击进入模块 →"), "card missing entry prompt");

  const keyboard = await evaluate(`(() => {
    const desk = document.querySelector("[data-desk]");
    desk.dispatchEvent(new PointerEvent("pointerleave", { pointerType: "mouse" }));
    desk.focus();
    const focusedActive = document.querySelector("[data-scene]").classList.contains("is-active");
    desk.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    return {
      focusedActive,
      escapedInactive: !document.querySelector("[data-scene]").classList.contains("is-active"),
      focusRetained: document.activeElement === desk,
      cardHidden: document.querySelector("[data-card]").hidden,
      expanded: desk.getAttribute("aria-expanded"),
      statusText: document.querySelector("[data-status]").textContent,
    };
  })()`);
  assert(keyboard.focusedActive && keyboard.escapedInactive && keyboard.focusRetained, "keyboard focus/Escape contract failed");
  assert(keyboard.cardHidden && keyboard.expanded === "false", "Escape did not collapse role content");
  assert(keyboard.statusText.includes("已取消"), "Escape cancellation was not announced");
  await sleep(100);
  assert(
    await evaluate(`document.activeElement === document.querySelector("[data-desk]") &&
      !document.querySelector("[data-scene]").classList.contains("is-active")`),
    "focused link immediately reactivated after Escape",
  );

  const firstTap = await evaluate(`(() => {
    const desk = document.querySelector("[data-desk]");
    desk.dispatchEvent(new PointerEvent("click", { pointerType: "touch", bubbles: true, cancelable: true }));
    return {
      active: document.querySelector("[data-scene]").classList.contains("is-active"),
      url: location.href,
    };
  })()`);
  assert(firstTap.active && firstTap.url === viewerUrl, "first touch did not reveal without navigation");
  await evaluate(`document.querySelector("[data-desk]").dispatchEvent(
    new PointerEvent("click", { pointerType: "touch", bubbles: true, cancelable: true })
  )`);
  await waitFor(`location.href === ${JSON.stringify(targetUrl)}`, "second-touch navigation");
  assert(await evaluate("document.title"), "target page did not render");

  await command("Network.enable");
  await command("Network.setCacheDisabled", { cacheDisabled: true });
  await command("Fetch.enable", { patterns: [{ urlPattern: "*sample.mp4*" }] });
  await command("Page.navigate", { url: `${viewerUrl}?blocked-media=1` });
  for (let attempt = 0; attempt < 50; attempt += 1) {
    if (await evaluate(`document.querySelector("[data-scene]")?.classList.contains("video-failed")`)) break;
    await sleep(100);
  }
  const failureDiagnostic = await evaluate(`(() => {
    const video = document.querySelector("[data-video]");
    return {
      url: location.href,
      failed: document.querySelector("[data-scene]")?.classList.contains("video-failed"),
      videoError: video?.error?.code || null,
      readyState: video?.readyState,
      networkState: video?.networkState,
      currentSrc: video?.currentSrc,
      sourceExists: !!video?.querySelector("source"),
    };
  })()`);
  assert(
    blockedMp4Requests > 0 && failureDiagnostic.networkState === 3,
    `MP4 was not deterministically blocked: ${JSON.stringify({ blockedMp4Requests, failureDiagnostic })}`,
  );
  assert(failureDiagnostic.failed, "blocked MP4 did not activate fallback end-to-end");
  const fallback = await evaluate(`(() => {
    const video = document.querySelector("[data-video]");
    document.querySelector("[data-desk]").dispatchEvent(
      new PointerEvent("pointerenter", { pointerType: "mouse" })
    );
    return {
      failed: document.querySelector("[data-scene]").classList.contains("video-failed"),
      videoDisplay: getComputedStyle(video).display,
      fallbackDisplay: getComputedStyle(document.querySelector("[data-fallback]")).display,
      fallbackText: document.querySelector("[data-fallback]").textContent,
      fallbackRole: document.querySelector("[data-fallback]").getAttribute("role"),
      cover: getComputedStyle(document.querySelector("[data-scene]")).backgroundImage,
      interactive: document.querySelector("[data-scene]").classList.contains("is-active"),
    };
  })()`);
  assert(fallback.failed && fallback.videoDisplay === "none", "video failure state not applied");
  assert(fallback.fallbackDisplay !== "none" && fallback.cover.includes("sample-cover.png"), "fallback UI not visible");
  assert(fallback.fallbackRole === "status" && fallback.fallbackText.includes("动画未加载"), "fallback was not announced");
  assert(fallback.interactive, "desk unusable after video failure");
  await command("Fetch.disable");
  await command("Network.setCacheDisabled", { cacheDisabled: false });

  await command("Emulation.setEmulatedMedia", {
    media: "screen",
    features: [{ name: "prefers-reduced-motion", value: "reduce" }],
  });
  await command("Page.navigate", { url: viewerUrl });
  await waitFor("document.readyState === 'complete' && !!document.querySelector('[data-desk]')", "reduced-motion reload");
  const reduced = await evaluate(`(() => {
    const desk = document.querySelector("[data-desk]");
    desk.dispatchEvent(new PointerEvent("pointerenter", { pointerType: "mouse" }));
    return {
      matches: matchMedia("(prefers-reduced-motion: reduce)").matches,
      videoDisplay: getComputedStyle(document.querySelector("[data-video]")).display,
      videoPaused: document.querySelector("[data-video]").paused,
      cover: getComputedStyle(document.querySelector("[data-scene]")).backgroundImage,
      transition: getComputedStyle(document.querySelector("[data-highlight]")).transitionDuration,
      active: document.querySelector("[data-scene]").classList.contains("is-active"),
    };
  })()`);
  assert(
    reduced.matches && reduced.videoDisplay === "none" && reduced.videoPaused,
    "reduced-motion static mode failed",
  );
  assert(reduced.cover.includes("sample-cover.png") && reduced.transition === "0s" && reduced.active, "reduced-motion interaction failed");

  const autoplayInjection = await command("Page.addScriptToEvaluateOnNewDocument", {
    source: `(() => {
      const nativePlay = HTMLMediaElement.prototype.play;
      window.__playAttempts = 0;
      HTMLMediaElement.prototype.play = function () {
        window.__playAttempts += 1;
        if (window.__playAttempts === 1) {
          return Promise.reject(new DOMException("Autoplay blocked by smoke test", "NotAllowedError"));
        }
        return nativePlay.call(this);
      };
    })();`,
  });
  await command("Emulation.setEmulatedMedia", { media: "screen", features: [] });
  await command("Page.navigate", { url: `${viewerUrl}?autoplay-rejection=1` });
  await waitFor("document.readyState === 'complete' && window.__playAttempts === 1", "autoplay rejection");
  await evaluate(`document.dispatchEvent(new PointerEvent("pointerdown", { pointerType: "mouse", bubbles: true }))`);
  await waitFor("window.__playAttempts >= 2", "pointer autoplay recovery");
  const autoplayRecovery = await evaluate(`new Promise(resolve => {
    const start = document.querySelector("[data-video]").currentTime;
    setTimeout(() => resolve({
      attempts: window.__playAttempts,
      progressed: document.querySelector("[data-video]").currentTime > start,
    }), 250);
  })`);
  assert(autoplayRecovery.attempts >= 2 && autoplayRecovery.progressed, "pointer retry did not recover autoplay");
  await command("Page.removeScriptToEvaluateOnNewDocument", { identifier: autoplayInjection.identifier });

  await command("Page.navigate", { url: viewerUrl });
  await waitFor("document.readyState === 'complete' && document.querySelector('[data-video]').readyState >= 1", "final viewer reload");
  const loopTime = await evaluate(`(() => {
    const video = document.querySelector("[data-video]");
    video.pause();
    video.dispatchEvent(new Event("ended"));
    video.pause();
    return video.currentTime;
  })()`);
  assert(Math.abs(loopTime - 20 / 24) < 0.05, `idle restart was ${loopTime}`);

  console.log(`PASS media: ${media.width}x${media.height}, ${media.duration.toFixed(3)}s`);
  console.log("PASS semantics: native link, collapsed disclosure, inactive content hidden");
  console.log(`PASS natural loop: reached ${maxPlaybackTime.toFixed(3)}s, restarted at ${naturalRestartTime.toFixed(3)}s`);
  console.log(`PASS red clothing evidence: ${redPixelCount} sampled red pixels`);
  console.log(`PASS hover: active immediately, highlight transition ${hover.highlightDuration}`);
  console.log("PASS card copy: A1 title, role, responsibility, and prompt");
  console.log("PASS keyboard: focus activates; Escape deactivates while retaining focus");
  console.log(`PASS touch/navigation: first tap revealed; second resolved ${targetUrl}`);
  console.log("PASS video failure: real blocked MP4 triggered bounded no-source fallback");
  console.log("PASS reduced motion: video paused, static cover, zero transition, immediate activation");
  console.log(`PASS autoplay recovery: rejected once, recovered after pointerdown (${autoplayRecovery.attempts} play attempts)`);
  console.log(`PASS idle restart: ended event sought to ${loopTime.toFixed(3)}s`);
} finally {
  if (socket) socket.close();
  browser.kill();
  if (browser.exitCode === null) {
    await new Promise(resolve => browser.once("exit", resolve));
  }
  await rm(profile, { recursive: true, force: true });
}
