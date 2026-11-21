import type { ResolutionEntry } from "@/lib/atlas/types";

export type TierFilter = "all" | "finer" | "gn" | "held";

export const SHOWN_AS_LABEL: Record<string, string> = {
  gn_zonal: "GN totals only (native cells not kept)",
  points: "Points",
  as_catalogued: "As catalogued",
  national: "National figure",
};

/** "30 m", "1 km", "about 1.2 m"; null metres is never guessed, it is "not recorded". */
export function formatMetres(entry: ResolutionEntry): string {
  const m = entry.native_resolution_m;
  if (m === null) {
    return entry.native_resolution_text ?? "not recorded";
  }
  if (m >= 1000) {
    return `${+(m / 1000).toFixed(2)} km`;
  }
  return `${+m.toFixed(1)} m`;
}

export function shownAs(entry: ResolutionEntry): string {
  return SHOWN_AS_LABEL[entry.shown_as] ?? (entry.shown_as.startsWith("area_") ? `Area units (${entry.shown_as.slice(5)})` : entry.shown_as);
}

/**
 * finer: source finer than a GN division. gn: published at GN. held: finer than GN in the
 * source but not published at that fineness (only GN totals, or not yet integrated).
 */
export function filterRows(rows: ResolutionEntry[], filter: TierFilter): ResolutionEntry[] {
  switch (filter) {
    case "finer":
      return rows.filter((row) => row.tier === "finer_than_gn");
    case "gn":
      return rows.filter((row) => row.tier === "gn");
    case "held":
      return rows.filter(
        (row) => row.tier === "finer_than_gn" && (row.shown_as === "gn_zonal" || row.status !== "active"),
      );
    default:
      return rows;
  }
}
