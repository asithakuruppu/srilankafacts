import { levelFiles } from "@/lib/areas";
import {
  availableLevels,
  type ExploreRow,
  type LevelOption,
} from "@/lib/explore-levels";
import {
  geographyLabel,
  getBoundaryLevels,
  getGeographyIndex,
  getIndicatorLevel,
  getIndicators,
} from "@/lib/release";

export function exploreLevels(): LevelOption[] {
  return availableLevels(getBoundaryLevels());
}

/** Rows with a value for one indicator and level, highest first (same order as the explorer). */
export function exploreRows(indicatorId: string, levelName: string): ExploreRow[] {
  const index = getGeographyIndex();
  const rows: ExploreRow[] = [];
  for (const file of levelFiles(levelName)) {
    for (const value of getIndicatorLevel(indicatorId, file)?.values ?? []) {
      if (value.value === null) {
        continue;
      }
      const geo = index.get(value.geography_id);
      rows.push({
        id: value.geography_id,
        name: geographyLabel(geo),
        levelName: geo?.level_name ?? file,
        value: value.value,
        unit: value.unit,
      });
    }
  }
  return rows.sort((a, b) => (b.value ?? 0) - (a.value ?? 0) || a.id.localeCompare(b.id));
}

/** Every indicator and level pair that has a table. */
export function exploreCombos(): { indicator: string; level: string }[] {
  const levels = exploreLevels();
  return getIndicators().flatMap((indicator) =>
    levels
      .filter((level) => levelFiles(level.name).some((file) => indicator.levels.includes(file)))
      .map((level) => ({ indicator: indicator.id, level: level.name })),
  );
}
