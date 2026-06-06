// Hybrid final dashboard JavaScript.
// - slide-dot navigation
// - moving dots for Plotly route maps
// - no Plotly frames and no Shiny rerender
(function () {
  "use strict";

  const movingState = new WeakMap();

  function setActiveDot() {
    const sections = Array.from(document.querySelectorAll(".story-slide"));
    const dots = Array.from(document.querySelectorAll(".slide-dots a"));
    if (!sections.length || !dots.length) return;
    let active = 0;
    let best = Infinity;
    sections.forEach((section, index) => {
      const dist = Math.abs(section.getBoundingClientRect().top - 150);
      if (dist < best) {
        best = dist;
        active = index;
      }
    });
    dots.forEach((dot, index) => dot.classList.toggle("active", index === active));
  }

  function asArray(x) {
    if (Array.isArray(x)) return x;
    if (x == null) return [];
    return [x];
  }

  function getAt(value, index, fallback) {
    if (Array.isArray(value)) {
      if (!value.length) return fallback;
      return value[Math.min(index, value.length - 1)];
    }
    if (value == null) return fallback;
    return value;
  }

  function isRouteTrace(trace) {
    if (!trace) return false;
    if (trace.type && String(trace.type).toLowerCase() !== "scattergeo") return false;
    const lat = asArray(trace.lat);
    const lon = asArray(trace.lon);
    if (lat.length < 4 || lon.length < 4) return false;
    const mode = String(trace.mode || "");
    if (!mode.includes("lines")) return false;
    const name = String(trace.name || "").toLowerCase();
    if (name.includes("shock") || name.includes("ring") || name.includes("origin markers") || name.includes("host markers")) return false;
    if (name.includes("route")) return true;
    const ht = String(trace.hovertemplate || "").toLowerCase();
    return ht.includes("people") || !!trace.customdata || !!trace.text;
  }

  function getRouteTraces(gd) {
    if (!gd || !Array.isArray(gd.data)) return [];
    const out = [];
    gd.data.forEach((trace, traceIndex) => {
      if (isRouteTrace(trace)) out.push({ trace, traceIndex });
    });
    return out;
  }

  function findMovingTraceIndex(gd) {
    if (!gd || !Array.isArray(gd.data)) return -1;
    return gd.data.findIndex((trace) => String(trace && trace.name ? trace.name : "").toLowerCase() === "moving groups");
  }

  function ensureMovingTrace(gd, routes) {
    let idx = findMovingTraceIndex(gd);
    if (idx >= 0) return idx;
    if (!routes.length || gd.__addingMovingGroups) return -1;
    gd.__addingMovingGroups = true;
    const movingTrace = {
      type: "scattergeo",
      mode: "markers",
      name: "Moving groups",
      lat: [],
      lon: [],
      text: [],
      customdata: [],
      marker: { size: 9, color: "#111827", opacity: 0.96, line: { width: 1.6, color: "#ffffff" } },
      hovertemplate: "Moving group<br>%{text}<br><b>%{customdata:,.0f}</b> people<extra></extra>",
      showlegend: false
    };
    if (window.Plotly && typeof window.Plotly.addTraces === "function") {
      window.Plotly.addTraces(gd, movingTrace).catch(() => {}).finally(() => { gd.__addingMovingGroups = false; });
    } else {
      gd.__addingMovingGroups = false;
    }
    return -1;
  }

  function animateOneGraph(gd) {
    if (!window.Plotly || !gd || !Array.isArray(gd.data)) return;
    const routes = getRouteTraces(gd);
    if (!routes.length) return;
    const movingIndex = ensureMovingTrace(gd, routes);
    if (movingIndex < 0) return;
    let state = movingState.get(gd);
    if (!state) {
      state = { tick: 0 };
      movingState.set(gd, state);
    }
    state.tick += 1;
    const latOut = [], lonOut = [], textOut = [], dataOut = [];
    routes.forEach((item, routeIndex) => {
      const trace = item.trace;
      const lat = asArray(trace.lat), lon = asArray(trace.lon);
      if (lat.length < 2 || lon.length < 2) return;
      const step = (state.tick + routeIndex * 7) % Math.min(lat.length, lon.length);
      latOut.push(lat[step]);
      lonOut.push(lon[step]);
      textOut.push(getAt(trace.text, step, String(trace.name || "Route")));
      dataOut.push(getAt(trace.customdata, step, null));
    });
    if (!latOut.length) return;
    try {
      window.Plotly.restyle(gd, { lat: [latOut], lon: [lonOut], text: [textOut], customdata: [dataOut] }, [movingIndex]);
    } catch (err) {
      // Keep demo safe even if a browser-side widget is mid-render.
      console.warn("Moving-dot restyle skipped", err);
    }
  }

  function animateMovingDots() {
    if (document.hidden) return;
    Array.from(document.querySelectorAll(".js-plotly-plot")).forEach((gd) => {
      try { animateOneGraph(gd); } catch (err) { console.warn("Moving-dot graph skipped", err); }
    });
  }

  function startAnimationLoop() {
    if (window.__refugeeMovingDotsStarted) return;
    window.__refugeeMovingDotsStarted = true;
    setInterval(animateMovingDots, 170);
  }

  window.addEventListener("scroll", setActiveDot, { passive: true });
  window.addEventListener("load", function () { setActiveDot(); startAnimationLoop(); });
  setTimeout(startAnimationLoop, 700);
})();
