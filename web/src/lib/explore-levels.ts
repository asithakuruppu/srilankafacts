// Shared by the server-rendered explore tables and the interactive explorer. No Node imports.

export type LevelOption = { name: string; boundary: number; label: string; singular: string };

export const LEVEL_DEFINITIONS: LevelOption[] = [
  { name: "province", boundary: 1, label: "Provinces", singular: "province" },
  { name: "district", boundary: 2, label: "Districts", singular: "district" },
  { name: "ds", boundary: 3, label: "DS divisions", singular: "DS division" },
  { name: "gn", boundary: 4, label: "GN divisions", singular: "GN division" },
];

export const MAX_TABLE_ROWS = 500;

export type ExploreRow = {
  id: string;
  name: string;
  levelName: string;
  value: number | null;
  unit: string;
};

export function availableLevels(boundaryLevels: number[]): LevelOption[] {
  return LEVEL_DEFINITIONS.filter((level) => boundaryLevels.includes(level.boundary));
}

export function defaultIndicatorId(ids: string[]): string {
  return ids.includes("population_density") ? "population_density" : (ids[0] ?? "population_total");
}

export function defaultLevelName(levels: LevelOption[]): string {
  return levels.find((level) => level.name === "district")?.name ?? levels[0]?.name ?? "district";
}

export function staticTableHref(indicatorId: string, levelName: string): string {
  return `/explore/table/${indicatorId}/${levelName}`;
}
