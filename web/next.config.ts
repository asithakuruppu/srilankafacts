import type { NextConfig } from "next";

// SLF_STATIC_EXPORT=1 builds plain files for free static hosting (docs/ops/deploy.md, D-053).
// A static build reads pages from `.tsx` files only, which leaves out the `.ts` routes that
// need a server: the API route handlers (the static site reads the API from
// NEXT_PUBLIC_DATA_BASE) and robots/sitemap (scripts/finish-export.mjs writes those).
// Cache Components are off: static export cannot use partial prerendering.
const staticExport = process.env.SLF_STATIC_EXPORT === "1";

const nextConfig: NextConfig = {
  pageExtensions: staticExport ? ["tsx"] : ["tsx", "ts"],
  ...(staticExport ? { output: "export", images: { unoptimized: true } } : {}),
};

export default nextConfig;
