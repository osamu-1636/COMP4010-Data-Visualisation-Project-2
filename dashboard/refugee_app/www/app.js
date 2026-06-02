// Production UI helper for the slide-scroll refugee dashboard.
// This file is intentionally client-side only.
// It controls slide-dot navigation and forces moving migration markers
// on Plotly scattergeo route maps.

(function () {
  "use strict";

  function asArray(value) {
    if (!value) return [];
    try {
      return Array.from(value);
    } catch (err) {
      return [];
    }
  }

  function setActiveDot() {
    const sections = Array.from(document.querySelectorAll(".story-slide"));
    const dots = Array.from(document.querySelectorAll(".slide-dots a"));

    if (!sections.length || !dots.length) return;

    let active = 0;
    let best = Infinity;

    sections.forEach((section, index) => {
      const dist = Math.abs(section.getBoundingClientRect().top - 160);
      if (dist < best) {
        best = dist;
        active = index;
      }
    });

    dots.forEach((dot, index) => {
      dot.classList.toggle("active", index === active);
    });
  }

  function getPlotlyGraph(outputId) {
    const host = document.getElementById(outputId);
    if (!host) return null;

    if (host.classList.contains("js-plotly-plot")) return host;

    return host.querySelector(".js-plotly-plot");
  }

  function getRouteLineTraces(gd) {
    if (!gd || !gd.data) return [];

    return gd.data
      .map((trace, index) => ({ trace, index }))
      .filter(({ trace }) => {
        if (!trace) return false;
        if (trace.type !== "scattergeo") return false;
        if (!String(trace.mode || "").includes("lines")) return false;

        const lat = asArray(trace.lat);
        const lon = asArray(trace.lon);

        if (lat.length < 2 || lon.length < 2) return false;

        return true;
      });
  }

  function getMovingTraceIndex(gd) {
    if (!gd || !gd.data) return -1;

    return gd.data.findIndex((trace) => {
      return trace && trace.name === "Moving groups";
    });
  }

  async function ensureMovingTrace(gd) {
    let movingIndex = getMovingTraceIndex(gd);

    if (movingIndex >= 0) return movingIndex;

    const routes = getRouteLineTraces(gd);
    if (!routes.length || !window.Plotly) return -1;

    const initLat = [];
    const initLon = [];
    const initText = [];

    routes.forEach(({ trace }, routeIndex) => {
      const lat = asArray(trace.lat);
      const lon = asArray(trace.lon);
      const n = Math.min(lat.length, lon.length);

      if (n < 2) return;

      const pos = (routeIndex * 7) % n;
      initLat.push(lat[pos]);
      initLon.push(lon[pos]);

      const traceText = asArray(trace.text);
      initText.push(traceText.length ? traceText[0] : "Moving refugee group");
    });

    if (!initLat.length) return -1;

    await Plotly.addTraces(gd, {
      type: "scattergeo",
      mode: "markers",
      lat: initLat,
      lon: initLon,
      text: initText,
      hovertemplate: "Moving group<br>%{text}<extra></extra>",
      marker: {
        size: 14,
        color: "#111827",
        symbol: "circle",
        opacity: 0.96,
        line: {
          width: 2.4,
          color: "#ffffff"
        }
      },
      showlegend: false,
      name: "Moving groups"
    });

    return getMovingTraceIndex(gd);
  }

  async function startMovingPeople(outputId) {
    const gd = getPlotlyGraph(outputId);

    if (!gd || !window.Plotly) return false;

    const routes = getRouteLineTraces(gd);
    if (!routes.length) return false;

    const movingIndex = await ensureMovingTrace(gd);
    if (movingIndex < 0) return false;

    // Remove old Plotly animation buttons if previous figure had them.
    try {
      if (gd.layout && gd.layout.updatemenus && gd.layout.updatemenus.length) {
        Plotly.relayout(gd, { updatemenus: [] });
      }
    } catch (err) {}

    if (gd.__movingPeopleTimer) return true;

    let step = 0;

    gd.__movingPeopleTimer = window.setInterval(() => {
      try {
        const freshMovingIndex = getMovingTraceIndex(gd);
        if (freshMovingIndex < 0) return;

        const freshRoutes = getRouteLineTraces(gd);
        if (!freshRoutes.length) return;

        const nextLat = [];
        const nextLon = [];
        const nextText = [];

        freshRoutes.forEach(({ trace }, routeIndex) => {
          const lat = asArray(trace.lat);
          const lon = asArray(trace.lon);
          const n = Math.min(lat.length, lon.length);

          if (n < 2) return;

          const offset = (routeIndex * 9) % n;
          const position = (step + offset) % n;

          nextLat.push(lat[position]);
          nextLon.push(lon[position]);

          const traceText = asArray(trace.text);
          nextText.push(traceText.length ? traceText[position] || traceText[0] : "Moving refugee group");
        });

        if (!nextLat.length) return;

        Plotly.restyle(
          gd,
          {
            lat: [nextLat],
            lon: [nextLon],
            text: [nextText],
            marker: [{
              size: 14,
              color: "#111827",
              symbol: "circle",
              opacity: 0.96,
              line: {
                width: 2.4,
                color: "#ffffff"
              }
            }]
          },
          [freshMovingIndex]
        );

        step = (step + 1) % 100000;
      } catch (err) {
        console.warn("Moving migration markers paused:", err);
      }
    }, 70);

    gd.classList.add("moving-people-active");
    return true;
  }

  function scanAndAnimate() {
    ["flow_map", "crisis_routes"].forEach((id) => {
      startMovingPeople(id);
    });
  }

  function installObserver() {
    const observer = new MutationObserver(() => {
      window.setTimeout(scanAndAnimate, 250);
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  window.addEventListener("scroll", setActiveDot, { passive: true });

  window.addEventListener("load", () => {
    setActiveDot();
    installObserver();

    [200, 600, 1200, 2200, 3500, 5000].forEach((delay) => {
      window.setTimeout(scanAndAnimate, delay);
    });

    window.setInterval(scanAndAnimate, 1800);
  });

  window.refugeeDashboard = {
    scanAndAnimate,
    startMovingPeople,
    debugMoving: function () {
      ["flow_map", "crisis_routes"].forEach((id) => {
        const gd = getPlotlyGraph(id);
        console.log(id, {
          graphFound: !!gd,
          routeLines: gd ? getRouteLineTraces(gd).length : 0,
          movingTrace: gd ? getMovingTraceIndex(gd) : -1
        });
      });
      scanAndAnimate();
    }
  };
})();
