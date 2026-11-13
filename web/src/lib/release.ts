import fs from "node:fs";
import path from "node:path";

import type {
  CorrectionsLog,
  DataPackage,
  Geography,
  GeographyList,
  IndicatorLevel,
  IndicatorList,
  IndicatorMeta,
  LatestRelease,
  Place,
} from "@/lib/types";

/**
 * Resolve the release the website reads from.
 *
 * Order: explicit `SLF_RELEASE_DIR`, the newest local preview build under `pipeline/`,
 * then the committed fixture used by CI. The website never fetches data from a live
 * service: every page is built from release files.
 */
export function resolveReleaseRoot(): string {
  const candidates: string[] = [];
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
    const newest = versions.at(-1);
    if (newest) {
      candidates.push(path.join(previews, newest));
    }
  }
  candidates.push(path.resolve(process.cwd(), "fixtures/preview"));
  for (const candidate of candidates) {
    if (fs.existsSync(path.join(candidate, "api/v1/releases/latest.json"))) {
      return candidate;
    }
  }
  throw new Error(
    "No release found. Set SLF_RELEASE_DIR to a release directory or keep fixtures/preview.",
  );
}

const ROOT = resolveReleaseRoot();
const cache = new Map<string, unknown>();

function readJson<T>(relative: string): T {
  const cached = cache.get(relative);
  if (cached !== undefined) {
    return cached as T;
  }
  const file = path.join(ROOT, relative);
  const parsed = JSON.parse(fs.readFileSync(file, "utf8")) as T;
  cache.set(relative, parsed);
  return parsed;
}

function readOptionalJson<T>(relative: string): T | null {
  const file = path.join(ROOT, relative);
  if (!fs.existsSync(file)) {
    return null;
  }
  return readJson<T>(relative);
}

function safeId(value: string): string {
  if (!/^[A-Za-z0-9_-]+$/.test(value)) {
    throw new Error(`Invalid identifier: ${value}`);
  }
  return value;
}

export function releaseRoot(): string {
  return ROOT;
}

export function releaseName(): string {
  return path.basename(ROOT);
}

export function getLatest(): LatestRelease {
  return readJson<LatestRelease>("api/v1/releases/latest.json");
}

/** Corrections log published with the release; null for releases built before it existed. */
export function getCorrections(): CorrectionsLog | null {
  return readOptionalJson<CorrectionsLog>("api/v1/corrections.json");
}

export function getIndicators(): IndicatorMeta[] {
  const list = readJson<IndicatorList>("api/v1/indicators.json");
  return list.indicators
    .filter((indicator) => indicator.levels.length > 0 && indicator.distribution !== "downloads_only")
    .sort((a, b) => a.name.localeCompare(b.name));
}

export function getIndicator(id: string): IndicatorMeta | null {
  return getIndicators().find((indicator) => indicator.id === id) ?? null;
}

export function getGeographies(): Geography[] {
  return readJson<GeographyList>("api/v1/geographies/admin.json").geographies;
}

export function getGeographyIndex(): Map<string, Geography> {
  const cached = cache.get("geography-index");
  if (cached) {
    return cached as Map<string, Geography>;
  }
  const index = new Map(getGeographies().map((geo) => [geo.geography_id, geo]));
  cache.set("geography-index", index);
  return index;
}

export function getGeography(id: string): Geography | null {
  return getGeographyIndex().get(safeId(id)) ?? null;
}

export function geographyLabel(geo: Geography | null | undefined): string {
  if (!geo) {
    return "Unknown place";
  }
  const english = geo.name_en?.trim();
  if (english) {
    return english;
  }
  const script = geo.name_si?.trim() || geo.name_ta?.trim();
  if (script) {
    return script;
  }
  const level = LEVEL_LABEL[geo.level_name] ?? "area";
  return `${level} ${geo.geography_id}`;
}

export function getChildren(id: string): Geography[] {
  return getGeographies()
    .filter((geo) => geo.parent_id === id)
    .sort((a, b) => geographyLabel(a).localeCompare(geographyLabel(b)));
}

export function getBreadcrumb(id: string): Geography[] {
  const index = getGeographyIndex();
  const trail: Geography[] = [];
  let current = index.get(id);
  let guard = 0;
  while (current && guard < 10) {
    trail.unshift(current);
    current = current.parent_id ? index.get(current.parent_id) : undefined;
    guard += 1;
  }
  return trail;
}

export function getPlace(id: string): Place | null {
  return readOptionalJson<Place>(`api/v1/places/${safeId(id)}.json`);
}

export function getIndicatorLevel(indicatorId: string, level: string): IndicatorLevel | null {
  const safeLevel = safeId(level);
  return readOptionalJson<IndicatorLevel>(
    `api/v1/indicators/${safeId(indicatorId)}/${safeLevel}.json`,
  );
}

export function getIndicatorLevels(indicatorId: string): string[] {
  const dir = path.join(ROOT, "api/v1/indicators", safeId(indicatorId));
  if (!fs.existsSync(dir)) {
    return [];
  }
  return fs
    .readdirSync(dir)
    .filter((name) => name.endsWith(".json"))
    .map((name) => name.replace(/\.json$/, ""))
    .sort();
}

export function getBoundaryLevels(): number[] {
  const dir = path.join(ROOT, "boundaries");
  if (!fs.existsSync(dir)) {
    return [];
  }
  return fs
    .readdirSync(dir)
    .map((name) => /^admin(\d)\.geojson$/.exec(name)?.[1])
    .filter((value): value is string => value !== undefined)
    .map(Number)
    .sort((a, b) => a - b);
}

export function getDatapackage(): DataPackage | null {
  return readOptionalJson<DataPackage>("datapackage.json");
}

export function getNationalValues(): Map<string, number> {
  const place = getPlace("LK");
  const values = new Map<string, number>();
  for (const observation of place?.values ?? []) {
    if (observation.value !== null) {
      values.set(observation.indicator_id, observation.value);
    }
  }
  return values;
}

export function getValueFor(place: Place, indicatorId: string): number | null {
  return place.values.find((value) => value.indicator_id === indicatorId)?.value ?? null;
}

export function placeValue(place: Place | null, indicatorId: string): number | null {
  return place ? getValueFor(place, indicatorId) : null;
}

export function getObservationFor(place: Place, indicatorId: string) {
  return place.values.find((value) => value.indicator_id === indicatorId) ?? null;
}

export const LEVEL_LABEL: Record<string, string> = {
  country: "Country",
  province: "Province",
  district: "District",
  ds: "Divisional Secretariat",
  "ds-provisional": "Divisional Secretariat (provisional)",
  gn: "Grama Niladhari division",
};

export const LEVEL_BOUNDARY: Record<string, number> = {
  country: 0,
  province: 1,
  district: 2,
  ds: 3,
  "ds-provisional": 3,
  gn: 4,
};
