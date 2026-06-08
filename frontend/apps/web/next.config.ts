import path from "node:path";
import { fileURLToPath } from "node:url";

import type { NextConfig } from "next";

const rootDir = path.join(path.dirname(fileURLToPath(import.meta.url)), "../../..");

const nextConfig: NextConfig = {
  transpilePackages: ["@yurpass/ui", "@yurpass/utils", "@yurpass/types"],
  outputFileTracingRoot: rootDir,
};

export default nextConfig;
