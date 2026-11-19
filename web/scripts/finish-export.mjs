#!/usr/bin/env node
// After `SLF_STATIC_EXPORT=1 next build`: finish the static site in out/ for a free static host
// (Cloudflare Workers static assets, docs/ops/deploy.md, D-053).
//
// - robots.txt and sitemaps (the `.ts` robots and sitemap routes are not in a static build)
// - _redirects: GN place pages, which are not prebuilt, are served by /place/gn
// - _headers: long caching for hashed build files
// - checks the free plan's limits: at most 20,000 files and 25 MiB per file; fails otherwise

import fs from "node:fs";
import path from "node:path";

const OUT = path.resolve(process.cwd(), "out");
const MAX_FILES = 20000;
const MAX_FILE_BYTES = 25 * 1024 * 1024;
const SITE = (process.env.NEXT_PUBLIC_SITE_URL ?? "").replace(/\/+$/, "");

if (!fs.existsSync(OUT)) {
  throw new Error("out/ not found: run with SLF_STATIC_EXPORT=1 next build first");
}
if (!SITE) {
  throw new Error("NEXT_PUBLIC_SITE_URL must be set for a static deploy (sitemap and canonical URLs)");
}

const meta = JSON.parse(fs.readFileSync(path.resolve("public/release/meta.json"), "utf8"));
const hierarchy = JSON.parse(fs.readFileSync(path.resolve("public/release/hierarchy.json"), "utf8"));

// robots.txt: a private preview is never indexed.
fs.writeFileSync(
  path.join(OUT, "robots.txt"),
  meta.publishable
    ? `User-agent: *\nAllow: /\n\nSitemap: ${SITE}/sitemap.xml\n`
    : "User-agent: *\nDisallow: /\n",
);

// Sitemaps: country to DS places and the indicator pages. GN pages are noindex.
const urls = [
  `${SITE}/`,
  `${SITE}/explore`,
  `${SITE}/indicators`,
  `${SITE}/data`,
  `${SITE}/methods`,
  `${SITE}/elections`,
  ...hierarchy.filter((row) => row[3] <= 3).map((row) => `${SITE}/place/${row[0]}`),
];
const indicatorDir = path.join(OUT, "indicator");
if (fs.existsSync(indicatorDir)) {
  for (const name of fs.readdirSync(indicatorDir).filter((n) => n.endsWith(".html")).sort()) {
    urls.push(`${SITE}/indicator/${name.replace(/\.html$/, "")}`);
  }
}
const xml = (list) =>
  `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${list
    .map((url) => `  <url><loc>${url}</loc></url>`)
    .join("\n")}\n</urlset>\n`;
fs.writeFileSync(path.join(OUT, "sitemap.xml"), xml(urls));

// GN place pages are not prebuilt. On Cloudflare, _redirects rules win over files, so each
// prebuilt place page gets its own rule first (static rules come before dynamic ones; the
// free plan allows 2,000 static and 100 dynamic rules). Anything else under /place/ goes to
// the browser-rendered GN page, which says "not found" for ids that are not in the release.
const prebuilt = fs
  .readdirSync(path.join(OUT, "place"))
  .filter((name) => name.endsWith(".html") && name !== "gn.html")
  .map((name) => name.replace(/\.html$/, ""))
  .sort();
if (prebuilt.length + 1 > 2000) {
  throw new Error(`${prebuilt.length} prebuilt place pages: over the 2,000 static rule limit`);
}
fs.writeFileSync(
  path.join(OUT, "_redirects"),
  [...prebuilt.map((id) => `/place/${id}  /place/${id}  200`), "/place/:id  /place/gn  200", ""].join(
    "\n",
  ),
);
fs.writeFileSync(
  path.join(OUT, "_headers"),
  [
    "/_next/static/*",
    "  Cache-Control: public, max-age=31536000, immutable",
    "/release/*",
    "  Cache-Control: public, max-age=3600",
    "",
  ].join("\n"),
);

// Free-plan limits.
const files = [];
const walk = (dir) => {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full);
    else files.push({ path: path.relative(OUT, full), bytes: fs.statSync(full).size });
  }
};
walk(OUT);
const tooBig = files.filter((file) => file.bytes > MAX_FILE_BYTES);
const total = files.reduce((sum, file) => sum + file.bytes, 0);
console.log(
  `static site: ${files.length} files, ${(total / 1e6).toFixed(1)} MB, largest ${(
    Math.max(...files.map((file) => file.bytes)) / 1e6
  ).toFixed(1)} MB; ${meta.publishable ? "public" : "PRIVATE PREVIEW"} release ${meta.release}`,
);
if (tooBig.length || files.length > MAX_FILES) {
  for (const file of tooBig) console.error(`over 25 MiB: ${file.path} (${file.bytes} bytes)`);
  if (files.length > MAX_FILES) console.error(`${files.length} files: over ${MAX_FILES}`);
  process.exit(1);
}
