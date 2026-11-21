import type { Geography, IndicatorList, IndicatorMeta, Place } from "@/lib/types";

// Pure place helpers shared by server pages and browser components (no file access).

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

export function getValueFor(place: Place, indicatorId: string): number | null {
  return place.values.find((value) => value.indicator_id === indicatorId)?.value ?? null;
}

export function placeValue(place: Place | null, indicatorId: string): number | null {
  return place ? getValueFor(place, indicatorId) : null;
}

export function getObservationFor(place: Place, indicatorId: string) {
  return place.values.find((value) => value.indicator_id === indicatorId) ?? null;
}

/** Indicators shown on place and indicator pages, in reading order. */
export function listIndicators(list: IndicatorList): IndicatorMeta[] {
  return (
    list.indicators
      // downloads_only: no place or level files (LA-004). places_only: place pages only (D-033);
      // no indicator uses it since D-036, but releases up to v2026.11.14 still carry it.
      .filter(
        (indicator) =>
          indicator.levels.length > 0 &&
          indicator.distribution !== "downloads_only" &&
          indicator.distribution !== "places_only",
      )
      // numeric collation: "aged 5–9" sorts before "aged 10–14"
      .sort((a, b) => a.name.localeCompare(b.name, "en", { numeric: true }))
  );
}
