#!/usr/bin/env node
// Prepare browser-readable files from a release: boundaries and a lazy search index.
// The release itself stays the single source of truth; nothing here is recomputed.

import fs from "node:fs";
import path from "node:path";

function resolveReleaseRoot() {
  const candidates = [];
  if (process.env.SLF_RELEASE_DIR) {
    candidates.push(path.resolve(process.env.SLF_RELEASE_DIR));
  }
  const previews = path.resolve(process.cwd(), "../pipeline/data/build/releases-preview");
  if (fs.existsSync(previews)) {
    const versions = fs
      .readdirSync(previews, { withFileTypes: true })
      .filter((entry) => entry.isDirectory() && entry.name.startsWith("v"))
      .map((entry) => entry.name)
      .sort();
    if (versions.length > 0) {
      candidates.push(path.join(previews, versions.at(-1)));
    }
  }
  candidates.push(path.resolve(process.cwd(), "fixtures/preview"));
  for (const candidate of candidates) {
    if (fs.existsSync(path.join(candidate, "api/v1/releases/latest.json"))) {
      return candidate;
    }
  }
  throw new Error("No release found for the web build.");
}

const root = resolveReleaseRoot();
const out = path.resolve(process.cwd(), "public/release");
const admin = JSON.parse(
  fs.readFileSync(path.join(root, "api/v1/geographies/admin.json"), "utf8"),
);
const latest = JSON.parse(
  fs.readFileSync(path.join(root, "api/v1/releases/latest.json"), "utf8"),
);

fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(path.join(out, "boundaries"), { recursive: true });

const boundaries = fs
  .readdirSync(path.join(root, "boundaries"))
  .filter((name) => /^admin\d\.geojson$/.test(name))
  .sort();
for (const name of boundaries) {
  fs.copyFileSync(path.join(root, "boundaries", name), path.join(out, "boundaries", name));
}

// MapLibre names its worker relative to the bundled module, which does not exist
// in the Next.js chunk directory. Serve the self-contained worker from public.
const worker = path.resolve("node_modules/maplibre-gl/dist/maplibre-gl-worker.mjs");
if (fs.existsSync(worker)) {
  fs.copyFileSync(worker, path.join(out, "maplibre-gl-worker.mjs"));
} else {
  throw new Error("maplibre-gl worker not found; run pnpm install first.");
}

const byId = new Map(admin.geographies.map((geo) => [geo.geography_id, geo]));
const searchIndex = admin.geographies
  .map((geo) => ({
    i: geo.geography_id,
    n: geo.name_en ?? geo.name_si ?? geo.name_ta ?? geo.geography_id,
    s: geo.name_si ?? null,
    t: geo.name_ta ?? null,
    l: geo.level,
    p: geo.parent_id ?? null,
    pn: geo.parent_id ? (byId.get(geo.parent_id)?.name_en ?? null) : null,
  }))
  .sort((a, b) => a.i.localeCompare(b.i));

fs.writeFileSync(
  path.resolve(process.cwd(), "public/search-index.json"),
  JSON.stringify(searchIndex),
);
fs.writeFileSync(
  path.join(out, "meta.json"),
  JSON.stringify(
    {
      release: latest.release,
      status: latest.status,
      publishable: latest.publishable,
      citation: latest.citation,
      boundary_levels: boundaries.map((name) => Number(name.replace(/\D/g, ""))),
      geography_count: latest.geography_count,
      observation_count: latest.observation_count,
      fixture: Boolean(latest.fixture),
    },
    null,
    2,
  ) + "\n",
);

const size = (file) => `${(fs.statSync(file).size / 1024 / 1024).toFixed(2)} MB`;
console.log(`release ${latest.release} from ${root}`);
console.log(`boundaries: ${boundaries.length} files`);
console.log(
  `search index: ${searchIndex.length} places, ${size(path.resolve(process.cwd(), "public/search-index.json"))}`,
);
