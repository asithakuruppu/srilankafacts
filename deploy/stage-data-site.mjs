#!/usr/bin/env node
// Stage a public release as the data site (static API and downloads) for Cloudflare Workers
// static assets (docs/ops/deploy.md, D-053). Files are hard-linked, not copied: no extra disk.
//
//   node deploy/stage-data-site.mjs <release dir> [out dir]
//
// Files over 25 MiB (the free plan's per-file limit) are left out and listed in
// large-files.tsv, to be attached to a GitHub release instead.

import fs from "node:fs";
import path from "node:path";

const MAX_FILES = 20000;
const MAX_FILE_BYTES = 25 * 1024 * 1024;

const releaseDir = path.resolve(process.argv[2] ?? "");
const outDir = path.resolve(process.argv[3] ?? "deploy/build/data-site");
const latestFile = path.join(releaseDir, "api/v1/releases/latest.json");
if (!process.argv[2] || !fs.existsSync(latestFile)) {
  console.error("usage: node deploy/stage-data-site.mjs <release dir> [out dir]");
  process.exit(2);
}
const latest = JSON.parse(fs.readFileSync(latestFile, "utf8"));
if (!latest.publishable && process.env.SLF_ALLOW_PREVIEW !== "1") {
  console.error(`${latest.release} is not publishable; a public data site needs a public release`);
  process.exit(1);
}

fs.rmSync(outDir, { recursive: true, force: true });
fs.mkdirSync(outDir, { recursive: true });

const large = [];
let count = 0;
let bytes = 0;
const walk = (dir) => {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith(".")) continue;
    const source = path.join(dir, entry.name);
    const rel = path.relative(releaseDir, source);
    if (entry.isDirectory()) {
      walk(source);
      continue;
    }
    const size = fs.statSync(source).size;
    if (size > MAX_FILE_BYTES) {
      large.push({ rel, size });
      continue;
    }
    const target = path.join(outDir, rel);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.linkSync(source, target);
    count += 1;
    bytes += size;
  }
};
walk(releaseDir);

// Every response may be read by other sites and tools (the API is public and read-only).
fs.writeFileSync(
  path.join(outDir, "_headers"),
  [
    "/*",
    "  Access-Control-Allow-Origin: *",
    "  Cache-Control: public, max-age=3600",
    "  X-Content-Type-Options: nosniff",
    "/boundaries/*",
    "  Content-Type: application/geo+json",
    "",
  ].join("\n"),
);
count += 1;

// The large files' sha256 come from the release's own checksum list.
const sums = new Map(
  fs
    .readFileSync(path.join(releaseDir, "CHECKSUMS.sha256"), "utf8")
    .split("\n")
    .filter(Boolean)
    .map((line) => {
      const [hash, ...name] = line.trim().split(/\s+/);
      return [name.join(" ").replace(/^\*?\.?\//, ""), hash];
    }),
);
const listFile = path.join(path.dirname(outDir), "large-files.tsv");
fs.writeFileSync(
  listFile,
  ["path\tbytes\tsha256", ...large.map((f) => `${f.rel}\t${f.size}\t${sums.get(f.rel) ?? "?"}`)].join(
    "\n",
  ) + "\n",
);

console.log(
  `data site for ${latest.release}: ${count} files, ${(bytes / 1e6).toFixed(1)} MB -> ${outDir}`,
);
console.log(`left out (over 25 MiB), listed in ${listFile}:`);
for (const f of large) console.log(`  ${f.rel} (${(f.size / 1e6).toFixed(0)} MB)`);
if (count > MAX_FILES) {
  console.error(`${count} files: over the free plan's ${MAX_FILES}`);
  process.exit(1);
}
