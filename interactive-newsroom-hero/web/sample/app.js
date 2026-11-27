(() => {
  const scene = document.querySelector("[data-scene]");
  const desk = document.querySelector("[data-desk]");
  const video = document.querySelector("[data-video]");
  const card = document.querySelector("[data-card]");
  const status = document.querySelector("[data-status]");
  const fallback = document.querySelector("[data-fallback]");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let touchArmed = false;
  let focusDismissed = false;

  const activate = () => {
    scene.classList.add("is-active");
    desk.setAttribute("aria-expanded", "true");
    card.hidden = false;
    status.textContent = "A1 智能选题，策划编辑。聚合热点信号，形成可执行的报道方向。";
  };
  const deactivate = announcement => {
    scene.classList.remove("is-active");
    desk.setAttribute("aria-expanded", "false");
    card.hidden = true;
    status.textContent = announcement || "";
    touchArmed = false;
  };

  desk.addEventListener("pointerenter", activate);
  desk.addEventListener("pointerleave", event => {
    if (event.pointerType !== "touch" && document.activeElement !== desk) deactivate();
  });
  desk.addEventListener("focus", () => {
    if (!focusDismissed) activate();
  });
  desk.addEventListener("blur", () => {
    focusDismissed = false;
    deactivate();
  });
  desk.addEventListener("click", event => {
    if (event.pointerType === "touch" && !touchArmed) {
      event.preventDefault();
      touchArmed = true;
      activate();
    }
  });
  desk.addEventListener("keydown", event => {
    if (event.key === "Escape") {
      event.preventDefault();
      focusDismissed = true;
      deactivate("已取消 A1 智能选题。");
    }
  });

  video.addEventListener("ended", () => {
    video.currentTime = 20 / 24;
    if (!reducedMotion.matches) video.play().catch(() => {});
  });
  let mediaReady = video.readyState >= HTMLMediaElement.HAVE_METADATA;
  let noSourceChecks = 0;
  let mediaWatchInterval;
  let mediaWatchTimeout;
  function stopMediaWatch() {
    window.clearInterval(mediaWatchInterval);
    window.clearTimeout(mediaWatchTimeout);
  }
  const markVideoFailed = () => {
    stopMediaWatch();
    scene.classList.add("video-failed");
    fallback.textContent = "动画未加载，仍可选择工位进入模块。";
  };
  const markMediaReady = () => {
    mediaReady = true;
    stopMediaWatch();
  };
  video.addEventListener("error", markVideoFailed);
  video.querySelector("source").addEventListener("error", markVideoFailed);
  video.addEventListener("loadedmetadata", markMediaReady);
  if (!mediaReady) {
    mediaWatchInterval = window.setInterval(() => {
      if (video.readyState >= HTMLMediaElement.HAVE_METADATA) {
        markMediaReady();
        return;
      }
      if (
        video.readyState === HTMLMediaElement.HAVE_NOTHING
        && video.networkState === HTMLMediaElement.NETWORK_NO_SOURCE
      ) {
        noSourceChecks += 1;
        if (noSourceChecks >= 2) markVideoFailed();
      } else {
        noSourceChecks = 0;
      }
    }, 100);
    mediaWatchTimeout = window.setTimeout(stopMediaWatch, 4000);
  }
  const startVideo = () => video.play().catch(error => {
    if (error.name !== "NotAllowedError") {
      markVideoFailed();
      return;
    }
    document.addEventListener("pointerdown", () => {
      if (!reducedMotion.matches) video.play().catch(markVideoFailed);
    }, {once: true});
  });
  const applyMotionPreference = () => {
    if (reducedMotion.matches) video.pause();
    else startVideo();
  };
  reducedMotion.addEventListener("change", applyMotionPreference);
  applyMotionPreference();
})();
