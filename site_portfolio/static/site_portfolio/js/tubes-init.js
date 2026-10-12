// Tubes interactive background — teal neon cursor trail behind the hero.
// Loaded only on the index page. Self-contained: pulls three.js from the
// vendored threejs-components build.

const canvas = document.getElementById("tubes-canvas");

if (!canvas) {
  // No-op on pages that don't host the canvas.
} else if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
  canvas.parentElement?.classList.add("tubes-bg--off");
} else {
  const libUrl = canvas.dataset.libSrc;
  import(libUrl)
    .then(({ default: TubesCursor }) => {
      const app = TubesCursor(canvas, {
        tubes: {
          colors: ["#2FE0C8", "#63EADA", "#1CB8A2"],
          lights: {
            intensity: 120,
            colors: ["#A0F2E7", "#2FE0C8", "#63EADA", "#1CB8A2"],
          },
        },
      });

      const wrap = canvas.parentElement;
      wrap?.classList.add("tubes-bg--ready");

      // Fade opacity as the user scrolls past the hero so the tubes don't
      // bleed into the incident theater and sections below. Drive opacity
      // directly — browsers don't always re-run transitions on calc(var())
      // when the var changes.
      const base = 0.6;
      let raf = 0;
      const setOpacity = () => {
        raf = 0;
        const max = window.innerHeight * 0.9;
        const t = Math.min(1, Math.max(0, window.scrollY / max));
        wrap.style.opacity = String(base * (1 - t));
      };
      const onScroll = () => {
        if (!raf) raf = requestAnimationFrame(setOpacity);
      };
      setOpacity();
      window.addEventListener("scroll", onScroll, { passive: true });

      // Pause rendering when tab hidden to save CPU.
      document.addEventListener("visibilitychange", () => {
        if (!app?.three) return;
        if (document.hidden) app.three.clock?.stop?.();
        else app.three.clock?.start?.();
      });
    })
    .catch((err) => {
      console.warn("Tubes background failed to load:", err);
      canvas.parentElement?.classList.add("tubes-bg--off");
    });
}
