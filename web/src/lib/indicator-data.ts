import { dataUrl } from "@/lib/data-base";
import { levelFiles } from "@/lib/areas";
import type { Hierarchy, HierarchyRow } from "@/lib/hierarchy";
import { buildHierarchy } from "@/lib/hierarchy";

export type LevelValue = { value: number | null; status: string; unit: string };

const valueCache = new Map<string, Promise<Map<string, LevelValue>>>();
let hierarchyPromise: Promise<Hierarchy> | null = null;

/** Hierarchy file written at build time from the release spine. */
export function loadHierarchy(): Promise<Hierarchy> {
  hierarchyPromise ??= fetch("/release/hierarchy.json")
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Hierarchy request failed (${response.status}).`);
      }
      return response.json() as Promise<HierarchyRow[]>;
    })
    .then(buildHierarchy)
    .catch((error) => {
      hierarchyPromise = null;
      throw error;
    });
  return hierarchyPromise;
}

/**
 * All values of one indicator at one level (GN files are about 1.4 MB, fetched once and kept).
 * A missing level file is an empty map, not an error: not every indicator exists at every level.
 */
export function loadLevelValues(
  indicatorId: string,
  levelName: string,
): Promise<Map<string, LevelValue>> {
  const key = `${indicatorId}|${levelName}`;
  const cached = valueCache.get(key);
  if (cached) {
    return cached;
  }
  const request = Promise.all(
    levelFiles(levelName).map(async (file) => {
      const response = await fetch(dataUrl(`/api/v1/indicators/${indicatorId}/${file}.json`));
      if (response.status === 404) {
        return [];
      }
      if (!response.ok) {
        throw new Error(`Data request failed (${response.status}).`);
      }
      const payload = (await response.json()) as {
        values: { geography_id: string; value: number | null; value_status?: string; unit: string }[];
      };
      return payload.values;
    }),
  )
    .then((files) => {
      const map = new Map<string, LevelValue>();
      for (const rows of files) {
        for (const row of rows) {
          map.set(row.geography_id, {
            value: row.value,
            status: row.value_status ?? "reported",
            unit: row.unit,
          });
        }
      }
      return map;
    })
    .catch((error) => {
      valueCache.delete(key);
      throw error;
    });
  valueCache.set(key, request);
  return request;
}

const placeCache = new Map<string, Promise<Map<string, number>>>();

/** Every published value of one place as indicator id to value (one request, about 50-90 KB). */
export function loadPlaceValues(geoId: string): Promise<Map<string, number>> {
  const cached = placeCache.get(geoId);
  if (cached) {
    return cached;
  }
  const request = fetch(dataUrl(`/api/v1/places/${geoId}.json`))
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Place request failed (${response.status}).`);
      }
      return response.json() as Promise<{
        values: { indicator_id: string; value: number | null }[];
      }>;
    })
    .then((place) => {
      const map = new Map<string, number>();
      for (const row of place.values) {
        if (row.value !== null) {
          map.set(row.indicator_id, row.value);
        }
      }
      return map;
    })
    .catch((error) => {
      placeCache.delete(geoId);
      throw error;
    });
  placeCache.set(geoId, request);
  return request;
}
