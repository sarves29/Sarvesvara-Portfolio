import Lenis from "lenis";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

import { initSplitText } from "./modules/splitText.js";
import { initMagnetic } from "./modules/magnetic.js";
import { initReveals } from "./modules/reveals.js";
import { initCommandPalette } from "./modules/commandPalette.js";
import { initKonami } from "./modules/konami.js";
import { initAiChat } from "./modules/aiChat.js";
import { initIncidentTimeline } from "./modules/incidentTimeline.js";

gsap.registerPlugin(ScrollTrigger);

function initSmoothScroll() {
  const lenis = new Lenis({
    duration: 1.2,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    smoothWheel: true,
    wheelMultiplier: 1,
    touchMultiplier: 1.5,
  });

  lenis.on("scroll", ScrollTrigger.update);
  gsap.ticker.add((time) => lenis.raf(time * 1000));
  gsap.ticker.lagSmoothing(0);

  window.__lenis = lenis;
  return lenis;
}

function logConsoleEgg() {
  const title = "background: #0E0E0E; color: #FF4D1C; padding: 8px 14px; border-radius: 6px; font: 600 14px system-ui;";
  const body = "color: #0E0E0E; font: 400 12px/1.6 system-ui;";
  console.log("%cSarvesvara Ramar — /portfolio", title);
  console.log(
    "%cHi, dev. Thanks for looking under the hood.\n• Stack: Django · Tailwind · GSAP · Three.js · Lenis · Lottie\n• Reach out: sarvesvarasar@gmail.com\n• Try the Konami code. ↑↑↓↓←→←→BA",
    body
  );
}

function boot() {
  initSmoothScroll();
  initSplitText();
  initReveals();
  initMagnetic();
  initCommandPalette();
  initKonami();
  initAiChat();
  initIncidentTimeline();

  document.documentElement.classList.add("js-ready");
  logConsoleEgg();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
