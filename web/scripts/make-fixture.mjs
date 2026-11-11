#!/usr/bin/env node
// Build a small, committed fixture from a real release so CI can build the site
// without the full preview data. Scope: all country/province/district units, one
// DS (Colombo, LK1103) and its GN divisions. Never invents a value: every copied
// value is filtered from the release.

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
  for (const candidate of candidates) {
    if (fs.existsSync(path.join(candidate, "api/v1/releases/latest.json"))) {
      return candidate;
    }
  }
  throw new Error("No release found to make a fixture from.");
}

const root = resolveReleaseRoot();
const out = path.resolve(process.cwd(), "fixtures/preview");
const read = (relative) => JSON.parse(fs.readFileSync(path.join(root, relative), "utf8"));
const write = (relative, value) => {
  const file = path.join(out, relative);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(value) + "\n");
};

const admin = read("api/v1/geographies/admin.json");
const latest = read("api/v1/releases/latest.json");
const indicators = read("api/v1/indicators.json");

const FOCUS_DS = "LK1103";
const selected = new Set(
  admin.geographies
    .filter((geo) => geo.level <= 2 || geo.geography_id === FOCUS_DS || geo.parent_id === FOCUS_DS)
    .map((geo) => geo.geography_id),
);
const geographies = admin.geographies
  .filter((geo) => selected.has(geo.geography_id))
  .sort((a, b) => a.geography_id.localeCompare(b.geography_id));

fs.rmSync(out, { recursive: true, force: true });
write("api/v1/geographies/admin.json", {
  ...admin,
  geographies,
  fixture: true,
});

let observationCount = 0;
for (const geo of geographies) {
  const place = read(`api/v1/places/${geo.geography_id}.json`);
  observationCount += place.values.length;
  write(`api/v1/places/${geo.geography_id}.json`, place);
}

for (const level of ["country", "province", "district", "ds", "gn"]) {
  for (const indicator of indicators.indicators) {
    let data;
    try {
      data = read(`api/v1/indicators/${indicator.id}/${level}.json`);
    } catch {
      continue;
    }
    const values = data.values.filter((value) => selected.has(value.geography_id));
    if (values.length === 0) {
      continue;
    }
    write(`api/v1/indicators/${indicator.id}/${level}.json`, { ...data, values, fixture: true });
  }
}

write("api/v1/indicators.json", { ...indicators, fixture: true });
for (const indicator of indicators.indicators) {
  const file = `api/v1/indicators/${indicator.id}.json`;
  try {
    write(file, read(file));
  } catch {
    // A metadata file is optional; indicator pages use indicators.json.
  }
}

const versions = read(`api/v1/releases/${latest.version}.json`);
const release = {
  ...latest,
  ...versions,
  geography_count: geographies.length,
  observation_count: observationCount,
  fixture: true,
};
write("api/v1/releases/latest.json", release);
write(`api/v1/releases/${latest.version}.json`, release);

for (const name of fs.readdirSync(path.join(root, "boundaries"))) {
  if (!/^admin[0-4]\.geojson$/.test(name)) {
    continue;
  }
  const collection = JSON.parse(fs.readFileSync(path.join(root, "boundaries", name), "utf8"));
  const filtered =
    name === "admin3.geojson" || name === "admin4.geojson"
      ? {
          ...collection,
          features: collection.features.filter((feature) =>
            selected.has(String(feature.properties.geography_id)),
          ),
        }
      : collection;
  write(`boundaries/${name}`, filtered);
}

const bytes = (dir) => {
  let total = 0;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const file = path.join(dir, entry.name);
    total += entry.isDirectory() ? bytes(file) : fs.statSync(file).size;
  }
  return total;
};
console.log(
  `fixture ${release.release}: ${geographies.length} geographies, ${observationCount} observations, ` +
    `${(bytes(out) / 1024 / 1024).toFixed(2)} MB`,
);
