import type { Config } from "tailwindcss";

import preset from "@yurpass/config/tailwind/preset";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "../../packages/ui/src/**/*.{js,ts,jsx,tsx}",
  ],
  presets: [preset],
};

export default config;
