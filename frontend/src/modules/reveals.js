import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

export function initReveals() {
  document.querySelectorAll("[data-reveal]").forEach((el) => {
    const variant = el.dataset.reveal || "up";
    const delay = parseFloat(el.dataset.revealDelay || "0");
    const from = {
      up: { y: 40, opacity: 0 },
      left: { x: -40, opacity: 0 },
      right: { x: 40, opacity: 0 },
      fade: { opacity: 0 },
      scale: { scale: 0.94, opacity: 0 },
    }[variant] || { y: 40, opacity: 0 };

    gsap.from(el, {
      ...from,
      duration: 1,
      delay,
      ease: "power3.out",
      scrollTrigger: { trigger: el, start: "top 88%", once: true },
    });
  });

  document.querySelectorAll("[data-reveal-stagger]").forEach((container) => {
    const children = Array.from(container.children);
    gsap.from(children, {
      y: 30,
      opacity: 0,
      duration: 0.8,
      stagger: 0.08,
      ease: "power3.out",
      scrollTrigger: { trigger: container, start: "top 85%", once: true },
    });
  });
}
