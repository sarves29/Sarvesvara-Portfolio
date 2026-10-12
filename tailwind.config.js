/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./site_portfolio/**/*.py",
    "./frontend/src/**/*.{js,ts}",
    "./site_portfolio/static/site_portfolio/js/**/*.js",
  ],
  safelist: [
    "tubes-bg--ready",
    "tubes-bg--off",
  ],
  theme: {
    extend: {
      colors: {
        // "paper" = warm off-white (now used as text/surface color on dark canvas)
        paper: {
          DEFAULT: "#EDE8DF",
          warm: "#DEDAD0",
          deep: "#C8C2B5",
        },
        // "ink" = graphite canvas (now the dominant background)
        ink: {
          DEFAULT: "#0F1115",
          soft: "#181A21",
          muted: "#6B7280",
          steel: "#3A4049",
        },
        // accent — teal replaces flame (class name kept for stability)
        flame: {
          DEFAULT: "#2FE0C8",
          dark: "#1CB8A2",
          light: "#63EADA",
          glow: "#A0F2E7",
        },
      },
      fontFamily: {
        display: ['"Inter"', "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ['"Inter"', "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      fontSize: {
        mega: ["clamp(4rem, 14vw, 12rem)", { lineHeight: "0.9", letterSpacing: "-0.04em" }],
        huge: ["clamp(2.5rem, 7vw, 5.5rem)", { lineHeight: "0.95", letterSpacing: "-0.03em" }],
        display: ["clamp(1.75rem, 3vw, 3rem)", { lineHeight: "1.05", letterSpacing: "-0.02em" }],
      },
      letterSpacing: {
        tightest: "-0.05em",
      },
      animation: {
        "marquee": "marquee 40s linear infinite",
        "marquee-reverse": "marquee 40s linear infinite reverse",
        "float-slow": "float 9s ease-in-out infinite",
        "blink": "blink 1.2s steps(2) infinite",
      },
      keyframes: {
        marquee: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0" },
        },
      },
      backgroundImage: {
        "noise": "url('/static/site_portfolio/dist/noise.png')",
        "grain": "radial-gradient(transparent 1px, #F5F1EA 1px)",
      },
    },
  },
  plugins: [],
};
