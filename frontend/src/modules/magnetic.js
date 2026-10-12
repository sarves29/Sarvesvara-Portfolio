export function initMagnetic() {
  if (window.matchMedia("(pointer: coarse)").matches) return;

  document.querySelectorAll("[data-magnetic]").forEach((el) => {
    const strength = parseFloat(el.dataset.magnetic || "0.35");
    let rafId = 0;
    let tx = 0;
    let ty = 0;

    function onMove(e) {
      const rect = el.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      tx = (e.clientX - cx) * strength;
      ty = (e.clientY - cy) * strength;
      if (!rafId) rafId = requestAnimationFrame(apply);
    }

    function apply() {
      el.style.transform = `translate3d(${tx}px, ${ty}px, 0)`;
      rafId = 0;
    }

    function onLeave() {
      tx = 0;
      ty = 0;
      el.style.transform = "translate3d(0, 0, 0)";
    }

    el.addEventListener("mousemove", onMove);
    el.addEventListener("mouseleave", onLeave);
  });
}
