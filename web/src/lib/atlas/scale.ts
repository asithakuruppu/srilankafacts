/** Scale rules: which level a zoom shows, and the colour ramps. No DOM or map imports. */

import type { LevelName } from "@/lib/atlas/types";

/** Zoom at which each level becomes the one in view (multi-scale-features.md §8). */
export const LEVEL_MIN_ZOOM: Record<Exclude<LevelName, "country">, number> = {
  province: 0,
  district: 6.9,
  ds: 8.4,
  gn: 10.4,
};

/** Zoom from which the detailed (30 m) geometry replaces the overview (150 m) geometry. */
export const DETAIL_ZOOM = 9.6;

export type MapLevel = Exclude<LevelName, "country">;

export const MAP_LEVELS: MapLevel[] = ["province", "district", "ds", "gn"];

/** The level in view at a zoom, limited to the levels that have data. */
export function levelForZoom(zoom: number, available: MapLevel[]): MapLevel {
  let chosen: MapLevel = available[0] ?? "district";
  for (const level of MAP_LEVELS) {
    if (zoom >= LEVEL_MIN_ZOOM[level] && available.includes(level)) {
      chosen = level;
    }
  }
  return chosen;
}

/** Zoom band [min, max) in which a level is the one in view. */
export function zoomBand(level: MapLevel): [number, number] {
  const index = MAP_LEVELS.indexOf(level);
  const next = MAP_LEVELS[index + 1];
  return [LEVEL_MIN_ZOOM[level], next ? LEVEL_MIN_ZOOM[next] : 24];
}

export function childLevel(level: LevelName): MapLevel | null {
  const order: LevelName[] = ["country", "province", "district", "ds", "gn"];
  const next = order[order.indexOf(level) + 1];
  return next && next !== "country" ? (next as MapLevel) : null;
}

/** Border rank drawn for a level: 1 province, 2 district, 3 DS, 4 GN. */
export const LEVEL_RANK: Record<MapLevel, number> = { province: 1, district: 2, ds: 3, gn: 4 };

export type Ramp = { light: string[]; dark: string[] };

/** Sequential sapphire ramp, five classes, low to high. */
export const SEQUENTIAL: Ramp = {
  light: ["#e6ebfa", "#b7c4f1", "#7f93e0", "#3f5cc6", "#152c85"],
  dark: ["#1b2444", "#2b3c7c", "#4560b8", "#7b93e6", "#c3d0ff"],
};

/** Diverging ramp, five classes: burnt orange (below) to sapphire (above). */
export const DIVERGING: Ramp = {
  light: ["#a8430f", "#e5a877", "#ecedf0", "#8fa3e6", "#1c3fae"],
  dark: ["#d9743a", "#8a4a25", "#2a3042", "#4560b8", "#a9bcff"],
};

/** Distance ramp for the profile lens: near (gamboge) to far (neutral). */
export const PROXIMITY: Ramp = {
  light: ["#c98a00", "#e9bf52", "#f0deab", "#e3e5ea", "#d2d5dc"],
  dark: ["#f2b400", "#a88212", "#5e4f1e", "#2a3042", "#1f2433"],
};

export function rampFor(ramp: Ramp, theme: "light" | "dark"): string[] {
  return theme === "dark" ? ramp.dark : ramp.light;
}
