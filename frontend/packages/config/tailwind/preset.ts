import type { Config } from "tailwindcss";

/** Shared Tailwind preset for YurPass apps (foundation). */
const preset: Partial<Config> = {
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#0f172a",
          foreground: "#f8fafc",
        },
      },
    },
  },
};

export default preset;
