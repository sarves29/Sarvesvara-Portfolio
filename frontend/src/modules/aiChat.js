const ENDPOINT = "/api/ai/ask/";

function getCookie(name) {
  const match = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[1]) : "";
}

function typeInto(el, text, { perChar = 12 } = {}) {
  el.textContent = "";
  let i = 0;
  return new Promise((resolve) => {
    const step = () => {
      if (i >= text.length) return resolve();
      const chunk = text.length - i > 40 ? 4 : 1;
      el.textContent += text.slice(i, i + chunk);
      i += chunk;
      setTimeout(step, perChar);
    };
    step();
  });
}

export function initAiChat() {
  const form = document.querySelector("[data-ai-form]");
  if (!form) return;
  const input = form.querySelector("[data-ai-input]");
  const submit = form.querySelector("[data-ai-submit]");
  const output = document.querySelector("[data-ai-output]");
  const statusEl = document.querySelector("[data-ai-status]");
  const dot = document.querySelector("[data-ai-dot]");
  const meta = document.querySelector("[data-ai-meta]");
  if (!input || !output || !submit) return;

  const setStatus = (label, busy = false) => {
    if (statusEl) statusEl.textContent = label;
    if (dot) dot.classList.toggle("animate-blink", !busy);
  };

  let busy = false;

  async function ask(question) {
    if (busy) return;
    const q = (question ?? input.value ?? "").trim();
    if (!q) return;
    busy = true;
    submit.disabled = true;
    setStatus("Thinking…", true);
    if (meta) meta.textContent = "";
    output.textContent = "";

    try {
      const res = await fetch(ENDPOINT, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
          Accept: "application/json",
        },
        body: JSON.stringify({ question: q }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = data.error || `Request failed (${res.status}).`;
        output.textContent = msg;
        setStatus(res.status === 429 ? "Rate-limited" : "Error");
        return;
      }
      setStatus("Live · Gemini");
      if (meta && typeof data.elapsed_ms === "number") meta.textContent = `${data.elapsed_ms}ms`;
      await typeInto(output, data.answer || "No answer.");
    } catch (err) {
      output.textContent = "Network hiccup. Try again.";
      setStatus("Offline");
    } finally {
      busy = false;
      submit.disabled = false;
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    ask();
  });

  document.querySelectorAll("[data-ai-suggestion]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const q = btn.getAttribute("data-ai-suggestion") || "";
      input.value = q;
      ask(q);
      const section = document.getElementById("ai-chat");
      if (section) section.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}
