(() => {
  document.addEventListener("DOMContentLoaded", () => {
    const scene = document.querySelector("[data-scene]");
    const video = document.querySelector("[data-video]");
    const card = document.querySelector("[data-card]");
    const status = document.querySelector("[data-status]");
    const fallback = document.querySelector("[data-fallback]");
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const desks = window.NEWSROOM_DESKS;
    if (!Array.isArray(desks) || desks.length !== 6) {
      throw new Error("NEWSROOM_DESKS must contain exactly six records");
    }
    const deskIds = desks.map(desk => desk?.id);
    const safeDeskId = /^a[1-6]$/;
    if (
      deskIds.some(id => typeof id !== "string" || !safeDeskId.test(id))
      || new Set(deskIds).size !== 6
    ) {
      throw new Error("NEWSROOM_DESKS IDs must be six unique safe desk IDs");
    }
    const nativeLinks = [...scene.querySelectorAll(".hit-map a[data-desk-id]")];
    const linksById = new Map(nativeLinks.map(link => [link.dataset.deskId, link]));
    const polygonsById = new Map(nativeLinks.map(link => [
      link.dataset.deskId,
      link.querySelector("polygon[data-hit-id]"),
    ]));
    const highlightsById = new Map(
      [...scene.querySelectorAll("[data-highlight-id]")]
        .map(highlight => [highlight.dataset.highlightId, highlight]),
    );
    if (
      nativeLinks.length !== 6
      || linksById.size !== 6
      || deskIds.some(id =>
        !linksById.has(id)
        || !highlightsById.has(id)
        || polygonsById.get(id)?.dataset.hitId !== id)
    ) {
      throw new Error("NEWSROOM_DESKS IDs must map to exactly six existing desk links");
    }
    const parsePolygonPoints = value => {
      if (typeof value !== "string") return null;
      const tokens = value.trim().split(/\s+/);
      if (tokens.length !== 4) return null;
      const points = tokens.map(token => token.split(",").map(Number));
      if (points.some(point =>
        point.length !== 2
        || point.some(coordinate => !Number.isFinite(coordinate))
        || point[0] < 0 || point[0] > 1280
        || point[1] < 0 || point[1] > 720)) {
        return null;
      }
      return points;
    };
    const polygonArea = points => Math.abs(
      points.reduce((area, [x, y], index) => {
        const [nextX, nextY] = points[(index + 1) % points.length];
        return area + x * nextY - nextX * y;
      }, 0),
    );
    const configuredPoints = new Map(
      desks.map(desk => [desk.id, parsePolygonPoints(desk.points)]),
    );
    const fallbackPoints = new Map(
      deskIds.map(id => [
        id,
        parsePolygonPoints(polygonsById.get(id).getAttribute("points")),
      ]),
    );
    if ([...configuredPoints.values(), ...fallbackPoints.values()].some(
      points => points === null,
    )) {
      throw new Error("NEWSROOM_DESKS points must contain valid four-point polygons");
    }
    if ([...configuredPoints.values()].some(points => polygonArea(points) < 4000)) {
      throw new Error("NEWSROOM_DESKS points must satisfy minimum polygon area");
    }
    const coordinateTolerance = 1e-6;
    const pointsMatch = deskIds.every(id =>
      configuredPoints.get(id).every((point, pointIndex) =>
        point.every((coordinate, coordinateIndex) =>
          Math.abs(
            coordinate - fallbackPoints.get(id)[pointIndex][coordinateIndex],
          ) <= coordinateTolerance)));
    if (!pointsMatch) {
      throw new Error("NEWSROOM_DESKS points must match embedded fallback polygons");
    }
    const destinationsMatch = desks.every(desk => {
      if (typeof desk.destination !== "string") return false;
      const link = linksById.get(desk.id);
      try {
        return new URL(link.getAttribute("href"), location.href).href
          === new URL(desk.destination, location.href).href;
      } catch {
        return false;
      }
    });
    if (!destinationsMatch) {
      throw new Error("Native hrefs must match all configured destinations");
    }

    const cardFields = {
      kicker: card.querySelector("[data-card-kicker]"),
      title: card.querySelector("[data-card-title]"),
      role: card.querySelector("[data-card-role]"),
      copy: card.querySelector("[data-card-copy]"),
      action: card.querySelector("[data-card-action]"),
    };
    const failedHighlights = new Set();
    const loadedHighlights = new Set();
    let touchArmedId = "";
    let focusDismissedId = "";
    let lowPerformance = false;

    const records = desks.map(desk => {
      const link = linksById.get(desk.id);
      const polygon = polygonsById.get(desk.id);
      const highlight = highlightsById.get(desk.id);
      link.style.setProperty("--desk-color", desk.color);
      link.style.setProperty("--desk-wash", `${desk.color}22`);
      link.style.setProperty("--desk-glow", `${desk.color}44`);
      return { ...desk, link, polygon, highlight };
    });

    const applyPerformanceMode = () => {
      lowPerformance = navigator.connection?.saveData === true
        || (Number.isFinite(navigator.deviceMemory) && navigator.deviceMemory <= 4)
        || navigator.hardwareConcurrency <= 4;
      scene.classList.toggle("low-performance", lowPerformance);
      if (lowPerformance) video.pause();
      return lowPerformance;
    };

    const activate = (deskId, source) => {
      const desk = records.find(record => record.id === deskId);
      if (!desk) return;
      scene.dataset.activeDesk = desk.id;
      scene.classList.add("has-selection");
      scene.style.setProperty("--desk-color", desk.color);
      scene.style.setProperty("--desk-wash", `${desk.color}22`);
      scene.style.setProperty("--desk-glow", `${desk.color}44`);
      records.forEach(record => {
        record.link.setAttribute("aria-expanded", String(record.id === desk.id));
      });
      cardFields.kicker.textContent = `${desk.id.toUpperCase()} / ${desk.english}`;
      cardFields.title.textContent = desk.title;
      cardFields.role.textContent = desk.role;
      cardFields.copy.textContent = desk.responsibility;
      cardFields.action.textContent = desk.action;
      card.dataset.side = desk.cardSide;
      card.hidden = false;
      scene.classList.toggle(
        "highlight-failed",
        failedHighlights.has(desk.id) && !loadedHighlights.has(desk.id),
      );
      status.textContent = `${desk.module}，${desk.role}。${desk.responsibility} 操作：${desk.action}。`;
      if (source !== "touch") touchArmedId = "";
    };

    const deactivate = message => {
      scene.dataset.activeDesk = "";
      scene.classList.remove("has-selection", "is-confirming", "highlight-failed");
      scene.style.removeProperty("--desk-color");
      scene.style.removeProperty("--desk-wash");
      scene.style.removeProperty("--desk-glow");
      records.forEach(record => record.link.setAttribute("aria-expanded", "false"));
      Object.values(cardFields).forEach(field => {
        field.textContent = "";
      });
      card.removeAttribute("data-side");
      card.hidden = true;
      touchArmedId = "";
      status.textContent = message || "";
    };

    const requestNavigation = async (desk, event) => {
      event.preventDefault();
      const destination = new URL(desk.link.getAttribute("href"), location.href).href;
      try {
        const response = await fetch(destination, {method: "HEAD", cache: "no-store"});
        if (!response.ok) throw new Error(`Destination returned ${response.status}`);
        if (reducedMotion.matches) {
          location.href = destination;
          return;
        }
        scene.classList.add("is-confirming");
        window.setTimeout(() => {
          location.href = destination;
        }, 350);
      } catch {
        scene.classList.remove("is-confirming");
        touchArmedId = "";
        status.textContent = "目标页面暂不可用，请稍后重试。";
      }
    };

    records.forEach(desk => {
      desk.highlight.addEventListener("load", () => {
        loadedHighlights.add(desk.id);
        failedHighlights.delete(desk.id);
        if (scene.dataset.activeDesk === desk.id) scene.classList.remove("highlight-failed");
      });
      desk.highlight.addEventListener("error", () => {
        failedHighlights.add(desk.id);
        loadedHighlights.delete(desk.id);
        if (scene.dataset.activeDesk === desk.id) scene.classList.add("highlight-failed");
      });
    });

    const applyHighlightMode = () => {
      const staticSelection = lowPerformance || reducedMotion.matches;
      scene.classList.toggle("static-selection", staticSelection);
      records.forEach(desk => {
        if (staticSelection) {
          desk.highlight.removeAttribute("src");
          loadedHighlights.delete(desk.id);
          failedHighlights.delete(desk.id);
        } else if (!desk.highlight.getAttribute("src")) {
          desk.highlight.src = desk.highlight.dataset.src;
        }
      });
    };

    applyPerformanceMode();
    applyHighlightMode();

    records.forEach(desk => {
      desk.link.addEventListener("pointerenter", event => {
        if (event.pointerType !== "touch") activate(desk.id, "pointer");
      });
      desk.link.addEventListener("pointerleave", event => {
        if (event.pointerType !== "touch" && document.activeElement !== desk.link) deactivate();
      });
      desk.link.addEventListener("focus", () => {
        if (focusDismissedId !== desk.id) activate(desk.id, "focus");
      });
      desk.link.addEventListener("blur", () => {
        focusDismissedId = "";
        deactivate();
      });
      desk.link.addEventListener("click", event => {
        if (event.pointerType === "touch" && touchArmedId !== desk.id) {
          event.preventDefault();
          touchArmedId = desk.id;
          activate(desk.id, "touch");
          return;
        }
        void requestNavigation(desk, event);
      });
      desk.link.addEventListener("keydown", event => {
        if (event.key !== "Escape") return;
        event.preventDefault();
        focusDismissedId = desk.id;
        deactivate(`已取消 ${desk.module}。`);
      });
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
        if (!reducedMotion.matches && !lowPerformance) {
          video.play().catch(markVideoFailed);
        }
      }, {once: true});
    });
    const applyMotionPreference = () => {
      applyHighlightMode();
      if (reducedMotion.matches || lowPerformance) video.pause();
      else startVideo();
    };
    video.addEventListener("ended", () => {
      video.currentTime = 20 / 24;
      if (!reducedMotion.matches && !lowPerformance) video.play().catch(() => {});
    });
    reducedMotion.addEventListener("change", applyMotionPreference);
    applyMotionPreference();
  });
})();
