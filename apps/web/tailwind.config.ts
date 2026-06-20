import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#f4f5f2",
        line: "#dfe2dc",
        ink: "#1a201d",
        muted: "#68716c",
        brand: "#174a38",
      },
      borderRadius: { panel: "6px" },
      boxShadow: { panel: "0 1px 2px rgba(17,24,20,.04)" },
    },
  },
  plugins: [],
};

export default config;

