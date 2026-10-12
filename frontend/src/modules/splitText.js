import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

function splitIntoChars(el) {
  const text = el.textContent;
  el.setAttribute("aria-label", text);
  el.textContent = "";
  const frag = document.createDocumentFragment();
  for (const ch of text) {
    const span = document.createElement("span");
    span.className = "split-char";
    span.setAttribute("aria-hidden", "true");
    span.textContent = ch === " " ? "\u00A0" : ch;
    frag.appendChild(span);
  }
  el.appendChild(frag);
  return el.querySelectorAll(".split-char");
}

export function initSplitText() {
  document.querySelectorAll("[data-split='chars']").forEach((el) => {
    const chars = splitIntoChars(el);
    gsap.from(chars, {
      yPercent: 110,
      opacity: 0,
      duration: 0.9,
      stagger: 0.018,
      ease: "power4.out",
      scrollTrigger: {
        trigger: el,
        start: "top 85%",
        once: true,
      },
    });
  });

  document.querySelectorAll("[data-split='words']").forEach((el) => {
    const words = el.textContent.split(/\s+/);
    el.setAttribute("aria-label", el.textContent);
    el.textContent = "";
    words.forEach((w, i) => {
      const span = document.createElement("span");
      span.className = "inline-block overflow-hidden align-top";
      const inner = document.createElement("span");
      inner.className = "split-char inline-block";
      inner.textContent = w;
      span.appendChild(inner);
      el.appendChild(span);
      if (i < words.length - 1) el.appendChild(document.createTextNode("\u00A0"));
    });
    gsap.from(el.querySelectorAll(".split-char"), {
      yPercent: 110,
      opacity: 0,
      duration: 1,
      stagger: 0.06,
      ease: "power4.out",
      scrollTrigger: { trigger: el, start: "top 85%", once: true },
    });
  });
}
