"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import type { GeoJSONSource, Map as MapLibreMap } from "maplibre-gl";
import { useEffect, useRef, useState } from "react";

import { MAP_TOKENS } from "@/components/atlas/atlas-map";
import type { GridFile } from "@/lib/atlas/area";
import { loadDetail, loadFeatures, loadJson, loadUnits } from "@/lib/atlas/data";
import { useTheme } from "@/lib/atlas/use-theme";

const EMPTY = { type: "FeatureCollection" as const, features: [] };

type Layers = { gn: boolean; grid: boolean; features: boolean };

/**
 * One district at the finest detail the bundle holds: GN outlines (the baseline), H3 r9 cells
 * (modelled from GN totals, so they add no information inside a GN) and named features
 * (local preview only). Layers whose files are missing are shown as unavailable.
 */
export default function FinestMap({ hasGrid, hasFeatures }: { hasGrid: boolean; hasFeatures: boolean }) {
  const theme = useTheme();
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const [ready, setReady] = useState(false);
  const [districts, setDistricts] = useState<{ id: string; name: string }[]>([]);
  const [district, setDistrict] = useState("LK11");
  const [layers, setLayers] = useState<Layers>({ gn: true, grid: hasGrid, features: hasFeatures });
  const [counts, setCounts] = useState<{ gn: number; cells: number; features: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadUnits()
      .then((units) => {
        const list = Object.entries(units)
          .filter(([, unit]) => unit.l === 2)
          .map(([id, unit]) => ({ id, name: unit.n ?? id }))
          .sort((a, b) => a.name.localeCompare(b.name));
        setDistricts(list);
        setDistrict((current) => (list.some((d) => d.id === current) ? current : (list[0]?.id ?? current)));
      })
      .catch(() => setError("The atlas bundle could not be loaded."));
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const probe = document.createElement("canvas");
      if (!probe.getContext("webgl2") && !probe.getContext("webgl")) {
        setError("This browser cannot draw WebGL maps. The table above has the same facts.");
        return;
      }
      const { Map: MapLibrary, setWorkerUrl } = await import("maplibre-gl");
      setWorkerUrl("/release/maplibre-gl-worker.mjs");
      if (cancelled || !container.current) {
        return;
      }
      const tokens = MAP_TOKENS[theme];
      const map = new MapLibrary({
        container: container.current,
        style: { version: 8, sources: {}, layers: [{ id: "sea", type: "background", paint: { "background-color": tokens.sea } }] },
        bounds: [79.4, 5.8, 82.1, 9.95],
        attributionControl: false,
        dragRotate: false,
      });
      mapRef.current = map;
      map.on("load", () => {
        for (const id of ["gn", "grid", "features"]) {
          map.addSource(id, { type: "geojson", data: EMPTY });
        }
        map.addLayer({ id: "gn-fill", type: "fill", source: "gn", paint: { "fill-color": tokens.land } });
        map.addLayer({ id: "gn-line", type: "line", source: "gn", paint: { "line-color": tokens.coast, "line-width": 0.6 } });
        map.addLayer({
          id: "grid-dots",
          type: "circle",
          source: "grid",
          paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 0.6, 14, 4], "circle-color": "#3d7be0", "circle-opacity": 0.55 },
        });
        map.addLayer({
          id: "feature-dots",
          type: "circle",
          source: "features",
          paint: { "circle-radius": 3, "circle-color": "#d4572a", "circle-stroke-color": tokens.border, "circle-stroke-width": 0.8 },
        });
        setReady(true);
      });
    })().catch(() => setError("The map could not start."));
    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
      setReady(false);
    };
    // The map is created once; the theme only sets its first colours.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) {
      return;
    }
    let cancelled = false;
    (async () => {
      const set = (id: string, data: object) => (map.getSource(id) as GeoJSONSource | undefined)?.setData(data as never);
      const detail = await loadDetail(district);
      const grid = hasGrid ? await loadJson<GridFile>(`/release/atlas/grid/${district}.json`).catch(() => null) : null;
      const feats = hasFeatures ? await loadFeatures(district) : { points: [] };
      if (cancelled) {
        return;
      }
      set("gn", layers.gn ? detail.gn : EMPTY);
      set("grid", {
        type: "FeatureCollection",
        features: layers.grid && grid ? grid.cells.map(([lon, lat]) => ({ type: "Feature", properties: {}, geometry: { type: "Point", coordinates: [lon, lat] } })) : [],
      });
      set("features", {
        type: "FeatureCollection",
        features: layers.features
          ? feats.points.map(([lon, lat, kind, name, category]) => ({ type: "Feature", properties: { kind, name, category }, geometry: { type: "Point", coordinates: [lon, lat] } }))
          : [],
      });
      setCounts({ gn: detail.gn.features.length, cells: grid?.cells.length ?? 0, features: feats.points.length });
      const coords = detail.gn.features.flatMap((f) => JSON.stringify(f.geometry).match(/-?\d+\.\d+/g) ?? []).map(Number);
      const lons = coords.filter((_, i) => i % 2 === 0);
      const lats = coords.filter((_, i) => i % 2 === 1);
      if (lons.length) {
        map.fitBounds([Math.min(...lons), Math.min(...lats), Math.max(...lons), Math.max(...lats)], { padding: 30, duration: 0 });
      }
    })().catch(() => !cancelled && setError("This district's files are missing from the bundle."));
    return () => {
      cancelled = true;
    };
  }, [ready, district, layers, hasGrid, hasFeatures]);

  const toggle = (key: keyof Layers) => setLayers((current) => ({ ...current, [key]: !current[key] }));
  return (
    <div className="finest-map">
      <div className="finest-controls">
        <label>
          District{" "}
          <select value={district} onChange={(event) => setDistrict(event.target.value)}>
            {districts.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          <input type="checkbox" checked={layers.gn} onChange={() => toggle("gn")} /> GN divisions (baseline)
        </label>
        <label>
          <input type="checkbox" checked={layers.grid} disabled={!hasGrid} onChange={() => toggle("grid")} /> H3 r9 cells
          {hasGrid ? "" : " (not in this bundle)"}
        </label>
        <label>
          <input type="checkbox" checked={layers.features} disabled={!hasFeatures} onChange={() => toggle("features")} /> Named features
          {hasFeatures ? "" : " (not in this bundle)"}
        </label>
      </div>
      {layers.grid && hasGrid ? (
        <p className="finest-badge" role="note">
          Modelled: each cell is an equal share of its GN division&apos;s total. The information floor is the GN, not the cell.
        </p>
      ) : null}
      {error ? <p role="alert">{error}</p> : null}
      <div ref={container} className="finest-canvas" aria-label="Map of one district at the finest resolution held" />
      {counts ? (
        <p className="muted">
          {counts.gn} GN divisions · {counts.cells.toLocaleString("en")} grid cells · {counts.features.toLocaleString("en")} named features (local preview only).
        </p>
      ) : null}
    </div>
  );
}
