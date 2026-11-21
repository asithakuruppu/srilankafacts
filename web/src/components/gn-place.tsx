"use client";

import { useEffect, useState } from "react";

import PlaceView, { type PlaceViewData } from "@/components/place-view";
import { dataUrl } from "@/lib/data-base";
import { LEVEL_NAMES, type HierarchyRow } from "@/lib/hierarchy";
import { listIndicators, placeValue } from "@/lib/place-model";
import type { Geography, IndicatorList, Place } from "@/lib/types";

type LevelFile = { values: { geography_id: string; value: number | null }[] };

const GN_ID = /^LK\d{7}$/; // GN p-codes: LK + province, district, DS (2) and GN (3) digits

/** The GN id from `/place/LK1103005` (static-host rewrite) or `/place/gn?id=LK1103005`. */
export function gnIdFrom(pathname: string, search: string): string | null {
  const fromPath = pathname.replace(/\/+$/, "").split("/").pop() ?? "";
  if (GN_ID.test(fromPath)) {
    return fromPath;
  }
  const fromQuery = new URLSearchParams(search).get("id") ?? "";
  return GN_ID.test(fromQuery) ? fromQuery : null;
}

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${response.status} for ${url}`);
  }
  return (await response.json()) as T;
}

function asGeography(row: HierarchyRow): Geography {
  return {
    geography_id: row[0],
    name_en: row[1],
    name_si: null,
    name_ta: null,
    parent_id: row[2],
    level: row[3],
    level_name: LEVEL_NAMES[row[3]] ?? "area",
    status: "current",
  };
}

/** Rank among the GN divisions of the same DS division, as the server page computes it. */
export function siblingRank(
  place: Place,
  rows: HierarchyRow[],
  level: LevelFile,
  indicatorId: string,
): string {
  const value = placeValue(place, indicatorId);
  if (value === null) {
    return "not available";
  }
  const siblings = new Set(
    rows.filter((row) => row[2] === place.geography.parent_id).map((row) => row[0]),
  );
  const values = level.values
    .filter((row) => siblings.has(row.geography_id) && row.value !== null)
    .map((row) => row.value as number)
    .sort((a, b) => b - a);
  if (values.length === 0) {
    return "national total";
  }
  return `${values.indexOf(value) + 1} of ${values.length} in parent`;
}

async function loadGn(id: string): Promise<PlaceViewData> {
  const [place, national, indicatorList, rows, level] = await Promise.all([
    getJson<Place>(dataUrl(`/api/v1/places/${id}.json`)),
    getJson<Place>(dataUrl("/api/v1/places/LK.json")),
    getJson<IndicatorList>(dataUrl("/api/v1/indicators.json")),
    getJson<HierarchyRow[]>("/release/hierarchy.json"),
    getJson<LevelFile>(dataUrl("/api/v1/indicators/population_total/gn.json")),
  ]);
  const parentId = place.geography.parent_id;
  const parent = parentId ? await getJson<Place>(dataUrl(`/api/v1/places/${parentId}.json`)) : null;
  const byId = new Map(rows.map((row) => [row[0], row]));
  const breadcrumb: Geography[] = [place.geography];
  let up = parentId ? byId.get(parentId) : undefined;
  for (let guard = 0; up && guard < 10; guard += 1) {
    breadcrumb.unshift(asGeography(up));
    up = up[2] ? byId.get(up[2]) : undefined;
  }
  const nationalValues: Record<string, number> = {};
  for (const observation of national.values) {
    if (observation.value !== null) {
      nationalValues[observation.indicator_id] = observation.value;
    }
  }
  return {
    place,
    parent,
    indicators: listIndicators(indicatorList),
    breadcrumb,
    childUnits: [],
    national: nationalValues,
    release: place.release,
    publishable: place.publishable,
    populationRank: siblingRank(place, rows, level, "population_total"),
  };
}

/**
 * A GN place page rendered in the browser from the static API. The static site prebuilds
 * country to DS pages only (14,000 GN pages would pass the free host's file limit), so GN
 * pages need JavaScript; the API file itself is linked for readers without it.
 */
export default function GnPlace() {
  const [state, setState] = useState<
    { kind: "loading" } | { kind: "ready"; data: PlaceViewData } | { kind: "error"; id: string | null }
  >({ kind: "loading" });

  useEffect(() => {
    const id = gnIdFrom(window.location.pathname, window.location.search);
    (id ? loadGn(id) : Promise.reject(new Error("not a GN address")))
      .then((data) => {
        document.title = `${data.place.geography.name_en ?? data.place.geography.geography_id} (Grama Niladhari division) · Sri Lanka Facts`;
        setState({ kind: "ready", data });
      })
      .catch(() => setState({ kind: "error", id }));
  }, []);

  if (state.kind === "ready") {
    return <PlaceView {...state.data} />;
  }
  return (
    <div className="shell section">
      {state.kind === "loading" ? (
        <p className="muted" role="status">
          Loading this GN division…
        </p>
      ) : (
        <div className="notice">
          <h1>Place not found</h1>
          <p>
            {state.id
              ? `No record for ${state.id} in this release.`
              : "This address does not name a GN division."}{" "}
            Search for a place from the header, or browse from the <a href="/explore">map</a>.
          </p>
        </div>
      )}
    </div>
  );
}
