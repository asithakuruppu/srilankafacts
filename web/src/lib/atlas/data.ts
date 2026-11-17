/** Browser loaders for the atlas bundle and release API files. Each file is fetched once. */

import type {
  Adjacency,
  AdjacencyLevel,
  AreaProps,
  ChangeFile,
  ClusterFile,
  Collection,
  DetailFile,
  FineFile,
  LevelName,
  MeshProps,
  OutlineProps,
  ProfileFile,
  Unit,
} from "@/lib/atlas/types";
import type { ValueMap } from "@/lib/atlas/context";
import type { Place } from "@/lib/types";

const cache = new Map<string, Promise<unknown>>();

export function loadJson<T>(url: string): Promise<T> {
  const cached = cache.get(url);
  if (cached) {
    return cached as Promise<T>;
  }
  const request = fetch(url).then((response) => {
    if (!response.ok) {
      throw new Error(`${url}: ${response.status}`);
    }
    return response.json() as Promise<T>;
  });
  cache.set(url, request);
  request.catch(() => cache.delete(url));
  return request;
}

const atlas = (file: string) => `/release/atlas/${file}`;

export const loadUnits = () => loadJson<Record<string, Unit>>(atlas("units.json"));
export const loadOverview = () => loadJson<Collection<AreaProps>>(atlas("overview.geojson"));
export const loadMesh = () => loadJson<Collection<MeshProps>>(atlas("mesh.geojson"));
export const loadOutlines = () => loadJson<Collection<OutlineProps>>(atlas("outlines.geojson"));
export const loadFine = () => loadJson<FineFile>(atlas("fine.json"));
export const loadDetail = (district: string) =>
  loadJson<DetailFile>(atlas(`detail/${district}.json`));
export const loadAdjacency = () => loadJson<Adjacency>(atlas("adjacency.json"));
export const loadGnAdjacency = (district: string) =>
  loadJson<AdjacencyLevel>(atlas(`adjacency-gn/${district}.json`));
export const loadProfile = () => loadJson<ProfileFile>(atlas("profile.json"));
export const loadChange = () => loadJson<ChangeFile>(atlas("change.json"));
export const loadClusters = (indicator: string) =>
  loadJson<ClusterFile>(atlas(`clusters/${indicator}.json`)).catch(() => ({}) as ClusterFile);

export const loadPlace = (id: string) => loadJson<Place>(`/api/v1/places/${id}.json`);

type LevelFile = { values: { geography_id: string; value: number | null }[] };

/** Published values of one indicator at one level, as id → value (units without a value are absent). */
export async function loadLevelValues(indicator: string, level: LevelName): Promise<ValueMap> {
  const files = level === "ds" ? ["ds", "ds-provisional"] : [level];
  const values: ValueMap = new Map();
  const payloads = await Promise.all(
    files.map((file) =>
      loadJson<LevelFile>(`/api/v1/indicators/${indicator}/${file}.json`).catch(() => null),
    ),
  );
  for (const payload of payloads) {
    for (const row of payload?.values ?? []) {
      if (row.value !== null && Number.isFinite(row.value)) {
        values.set(row.geography_id, row.value);
      }
    }
  }
  return values;
}
