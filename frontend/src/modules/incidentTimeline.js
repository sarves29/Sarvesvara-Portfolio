// Incident scroll-theater: pins a stage, advances steps with scroll,
// renders inline SVG line charts from server-side data.

const MIN_DESKTOP = 768;

function renderCharts(root, steps) {
  const charts = root.querySelectorAll("[data-chart-step]");
  charts.forEach((el) => {
    const idx = Number(el.getAttribute("data-chart-step"));
    const step = steps[idx];
    if (!step || !step.artifact || step.artifact.type !== "metric") return;
    const series = step.artifact.series || [];
    if (!series.length) return;

    // Normalize across all series
    let max = -Infinity;
    let min = Infinity;
    series.forEach((s) => {
      s.values.forEach((v) => {
        if (v > max) max = v;
        if (v < min) min = v;
      });
    });
    const span = Math.max(1, max - min);
    const N = series[0].values.length;

    const W = 100;
    const H = 42;
    const pad = 1;

    const toY = (v) => H - pad - ((v - min) / span) * (H - pad * 2);
    const toX = (i) => (i / (N - 1)) * W;

    const svg = el.querySelector("svg[data-svg]");
    if (!svg) return;

    // baseline grid lines
    const grid = [0.25, 0.5, 0.75]
      .map((g) => {
        const y = H - pad - g * (H - pad * 2);
        return `<line x1="0" y1="${y}" x2="${W}" y2="${y}" stroke="rgba(245,241,234,0.06)" stroke-width="0.25" />`;
      })
      .join("");

    const paths = series
      .map((s) => {
        const pts = s.values.map((v, i) => `${toX(i).toFixed(2)},${toY(v).toFixed(2)}`).join(" ");
        return `<polyline fill="none" stroke="${s.color}" stroke-width="0.6" stroke-linecap="round" stroke-linejoin="round" points="${pts}" vector-effect="non-scaling-stroke" />`;
      })
      .join("");

    // accent dots on the last point of flame-colored series
    const dots = series
      .filter((s) => s.color.toLowerCase() === "#ff4d1c")
      .map((s) => {
        const i = s.values.length - 1;
        return `<circle cx="${toX(i).toFixed(2)}" cy="${toY(s.values[i]).toFixed(2)}" r="0.8" fill="${s.color}" />`;
      })
      .join("");

    svg.innerHTML = `${grid}${paths}${dots}`;
  });
}

export function initIncidentTimeline() {
  const section = document.querySelector("[data-incident]");
  if (!section) return;
  const dataNode = document.getElementById("incident-data");
  if (!dataNode) return;

  let steps;
  try {
    steps = JSON.parse(dataNode.textContent);
  } catch (e) {
    return;
  }

  // Attach per-chart markers so the renderer knows which step to pull from
  section.querySelectorAll(".incident-frame").forEach((frame) => {
    const idx = Number(frame.getAttribute("data-frame"));
    const chart = frame.querySelector(".metric-chart");
    if (chart) chart.setAttribute("data-chart-step", String(idx));
  });

  renderCharts(section, steps);

  const frames = Array.from(section.querySelectorAll(".incident-frame"));
  const rails = Array.from(section.querySelectorAll(".incident-rail li"));
  const progressBar = section.querySelector(".incident-progress-bar");
  const total = frames.length;
  if (!total) return;

  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isDesktop = () => window.innerWidth >= MIN_DESKTOP;

  let activeIdx = -1;
  const setActive = (i) => {
    if (i === activeIdx) return;
    activeIdx = i;
    frames.forEach((f, fi) => {
      if (fi === i) f.setAttribute("data-active", "");
      else f.removeAttribute("data-active");
    });
    rails.forEach((r, ri) => r.classList.toggle("is-active", ri === i));
  };

  const update = () => {
    const rect = section.getBoundingClientRect();
    const vh = window.innerHeight;
    // how much of the section has scrolled past the top of the viewport
    const scrolled = Math.min(Math.max(-rect.top, 0), section.offsetHeight - vh);
    const travel = Math.max(1, section.offsetHeight - vh);
    const progress = scrolled / travel;

    const idx = Math.min(total - 1, Math.max(0, Math.floor(progress * total + 0.0001)));
    setActive(idx);

    if (progressBar) {
      progressBar.style.transform = `scaleX(${Math.min(1, progress)})`;
    }
  };

  // On mobile, just activate each frame as it enters via IntersectionObserver
  const mobileMode = () => {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            const i = Number(e.target.getAttribute("data-frame"));
            setActive(i);
          }
        });
      },
      { threshold: 0.5 }
    );
    frames.forEach((f) => io.observe(f));
    if (progressBar) progressBar.style.transform = "scaleX(1)";
  };

  if (!isDesktop() || prefersReduced) {
    mobileMode();
    return;
  }

  let ticking = false;
  const onScroll = () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      update();
      ticking = false;
    });
  };

  update();
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", () => {
    if (!isDesktop()) mobileMode();
    else update();
  });
}
