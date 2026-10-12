const SEQ = [
  "ArrowUp", "ArrowUp", "ArrowDown", "ArrowDown",
  "ArrowLeft", "ArrowRight", "ArrowLeft", "ArrowRight",
  "b", "a",
];

export function initKonami() {
  let idx = 0;
  document.addEventListener("keydown", (e) => {
    const key = e.key.length === 1 ? e.key.toLowerCase() : e.key;
    if (key === SEQ[idx]) {
      idx += 1;
      if (idx === SEQ.length) {
        idx = 0;
        triggerEgg();
      }
    } else {
      idx = key === SEQ[0] ? 1 : 0;
    }
  });
}

function triggerEgg() {
  document.documentElement.classList.add("konami");
  const root = document.body;
  for (let i = 0; i < 30; i++) {
    const el = document.createElement("span");
    const left = Math.random() * 100;
    const delay = Math.random() * 1.2;
    el.textContent = ["★", "✦", "✺", "◆", "◉"][i % 5];
    el.style.cssText = `
      position: fixed; left: ${left}vw; top: -10vh; z-index: 9999;
      color: #FF4D1C; font-size: ${14 + Math.random() * 22}px;
      animation: konami-fall 2.8s ${delay}s cubic-bezier(.25,.8,.25,1) forwards;
      pointer-events: none;
    `;
    root.appendChild(el);
    setTimeout(() => el.remove(), 4500);
  }
  const style = document.createElement("style");
  style.textContent = `@keyframes konami-fall { to { transform: translateY(120vh) rotate(720deg); opacity: 0; } }`;
  if (!document.getElementById("konami-style")) {
    style.id = "konami-style";
    document.head.appendChild(style);
  }

  const banner = document.createElement("div");
  banner.textContent = "↑↑↓↓←→←→BA — you found it.";
  banner.style.cssText = `
    position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
    background: #0E0E0E; color: #FF4D1C; padding: 10px 18px; border-radius: 999px;
    font-family: "JetBrains Mono", monospace; font-size: 12px; letter-spacing: 0.1em;
    z-index: 9999; animation: konami-fade 3s ease forwards;
  `;
  root.appendChild(banner);
  const fadeStyle = document.createElement("style");
  fadeStyle.textContent = `@keyframes konami-fade { 0%{opacity:0;transform:translate(-50%,10px)} 20%{opacity:1;transform:translate(-50%,0)} 80%{opacity:1} 100%{opacity:0} }`;
  document.head.appendChild(fadeStyle);
  setTimeout(() => banner.remove(), 3200);
}
