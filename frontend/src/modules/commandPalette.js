const ACTIONS = [
  { label: "Go to Work", hint: "home", href: "/#work" },
  { label: "Go to About", hint: "home", href: "/#about" },
  { label: "Go to Now", hint: "/now", href: "/now/" },
  { label: "Go to Contact", hint: "/contact", href: "/contact/" },
  { label: "Download Resume", hint: "pdf", href: "/resume/download/" },
  { label: "GitHub", hint: "external", href: "https://github.com/sarves29" },
  { label: "Email Sarvesvara", hint: "mailto", href: "mailto:sarvesvarasar@gmail.com" },
  { label: "Ask the AI about my resume", hint: "ai", href: "#ai-chat" },
];

export function initCommandPalette() {
  const overlay = document.querySelector("[data-cmdk]");
  if (!overlay) return;

  const input = overlay.querySelector("[data-cmdk-input]");
  const list = overlay.querySelector("[data-cmdk-list]");
  if (!input || !list) return;

  let active = 0;
  let filtered = ACTIONS.slice();

  function render() {
    list.innerHTML = filtered
      .map(
        (a, i) => `
      <li data-i="${i}" class="group flex items-center justify-between gap-4 px-4 py-3 rounded-xl cursor-pointer ${
          i === active ? "bg-flame text-ink" : "hover:bg-paper/5 text-paper"
        }">
        <span class="text-sm">${a.label}</span>
        <span class="text-[10px] uppercase tracking-widest font-mono ${
          i === active ? "text-ink/70" : "text-paper/40"
        }">${a.hint}</span>
      </li>`
      )
      .join("");
  }

  function open() {
    overlay.classList.remove("hidden");
    overlay.classList.add("flex");
    input.value = "";
    filtered = ACTIONS.slice();
    active = 0;
    render();
    setTimeout(() => input.focus(), 20);
  }

  function close() {
    overlay.classList.add("hidden");
    overlay.classList.remove("flex");
  }

  function trigger(a) {
    if (!a) return;
    close();
    if (a.href.startsWith("#")) {
      const evt = new CustomEvent("cmdk:action", { detail: a });
      window.dispatchEvent(evt);
    } else {
      window.location.assign(a.href);
    }
  }

  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      overlay.classList.contains("hidden") ? open() : close();
      return;
    }
    if (overlay.classList.contains("hidden")) return;

    if (e.key === "Escape") close();
    if (e.key === "ArrowDown") {
      e.preventDefault();
      active = (active + 1) % filtered.length;
      render();
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      active = (active - 1 + filtered.length) % filtered.length;
      render();
    }
    if (e.key === "Enter") {
      e.preventDefault();
      trigger(filtered[active]);
    }
  });

  input.addEventListener("input", () => {
    const q = input.value.trim().toLowerCase();
    filtered = !q
      ? ACTIONS.slice()
      : ACTIONS.filter((a) => a.label.toLowerCase().includes(q) || a.hint.toLowerCase().includes(q));
    active = 0;
    render();
  });

  list.addEventListener("click", (e) => {
    const li = e.target.closest("li[data-i]");
    if (!li) return;
    trigger(filtered[parseInt(li.dataset.i, 10)]);
  });

  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) close();
  });

  document.querySelectorAll("[data-cmdk-trigger]").forEach((btn) => btn.addEventListener("click", open));
}
