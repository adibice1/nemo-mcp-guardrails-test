import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        "gms-bg": "#eef3ff",
        "gms-blue": "#4775ff",
        "gms-blue-dark": "#2f63f7",
        "gms-blue-soft": "#ebf1ff",
        "gms-text": "#363746",
        "gms-muted": "#8b8fa1",
        "gms-line": "#e8edf7",
        "gms-danger": "#ff263d"
      },
      boxShadow: {
        shell: "0 2px 0 rgba(71, 117, 255, 0.28), 0 16px 42px rgba(64, 91, 156, 0.08)",
        field: "0 4px 0 rgba(71, 117, 255, 0.18)",
        button: "0 4px 8px rgba(47, 99, 247, 0.28)",
        modal: "0 18px 45px rgba(39, 48, 77, 0.16)"
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "Arial", "sans-serif"]
      }
    }
  },
  plugins: []
};

export default config;
