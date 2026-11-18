"use client";

import type { GeoJSONSource, Map as MapLibreMap, MapMouseEvent } from "maplibre-gl";
import { useEffect, useMemo, useRef, useState } from "react";

import { MAP_TOKENS } from "@/components/atlas/atlas-map";
import { estimateArea, type AreaEstimate, type AreaShape, type GridFile } from "@/lib/atlas/area";
import { loadDetail, loadElectoral, loadJson, loadLevelValues, loadMesh, loadOverview, loadUnits } from "@/lib/atlas/data";
import {
  boxesOverlap,
  boxOf,
  circleBox,
  circleRing,
  distanceKm,
  inGeometry,
  inRing,
  type Box,
  type LonLat,
} from "@/lib/atlas/geo";
import type { Unit } from "@/lib/atlas/types";
import { useTheme } from "@/lib/atlas/use-theme";
import { formatNumber } from "@/lib/format";

export type CountIndicator = { id: string; name: string; unit: string };

type Mode = "circle" | "polygon" | "point";
type Resolved = { point: LonLat; rows: { level: string; id: string; name: string | null }[]; note: string | null };

const EMPTY = { type: "FeatureCollection" as const, features: [] };
const atlas = (file: string) => `/release/atlas/${file}`;

function shapeFeatures(shape: AreaShape | null, draft: LonLat[], point: LonLat | null) {
  const features: object[] = [];
  if (shape?.kind === "circle") {
    features.push({ type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [circleRing(shape.centre, shape.radiusKm)] } });
    features.push({ type: "Feature", properties: { vertex: 1 }, geometry: { type: "Point", coordinates: shape.centre } });
  } else if (shape?.kind === "polygon") {
    features.push({ type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [shape.ring] } });
  }
  if (draft.length) {
    features.push({ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: draft } });
    for (const vertex of draft) {
      features.push({ type: "Feature", properties: { vertex: 1 }, geometry: { type: "Point", coordinates: vertex } });
    }
  }
  if (point) {
    features.push({ type: "Feature", properties: { vertex: 1 }, geometry: { type: "Point", coordinates: point } });
  }
  return { type: "FeatureCollection" as const, features };
}

function readUrl(): { shape: AreaShape | null; indicator: string | null } {
  const params = new URLSearchParams(window.location.search);
  const lon = Number(params.get("lon"));
  const lat = Number(params.get("lat"));
  const r = Number(params.get("r"));
  const shape =
    Number.isFinite(lon) && Number.isFinite(lat) && r > 0 && params.has("lon")
      ? ({ kind: "circle", centre: [lon, lat], radiusKm: Math.min(50, r) } as AreaShape)
      : null;
  return { shape, indicator: params.get("ind") };
}

export default function AreaTool({ indicators }: { indicators: CountIndicator[] }) {
  const theme = useTheme();
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const [ready, setReady] = useState(false);
  const [mode, setMode] = useState<Mode>("circle");
  const [initial] = useState(() => (typeof window === "undefined" ? { shape: null, indicator: null } : readUrl()));
  const [radius, setRadius] = useState(initial.shape?.kind === "circle" ? initial.shape.radiusKm : 5);
  const [shape, setShape] = useState<AreaShape | null>(initial.shape);
  const [draft, setDraft] = useState<LonLat[]>([]);
  const [indicator, setIndicator] = useState(
    indicators.find((item) => item.id === initial.indicator)?.id ?? indicators.find((item) => item.id === "population_total")?.id ?? indicators[0]?.id ?? "",
  );
  const [result, setResult] = useState<{ key: string; value: AreaEstimate } | null>(null);
  const [resolved, setResolved] = useState<Resolved | null>(null);
  const [error, setError] = useState<string | null>(null);
  const modeRef = useRef(mode);
  const radiusRef = useRef(radius);
  useEffect(() => {
    modeRef.current = mode;
    radiusRef.current = radius;
  }, [mode, radius]);

  // Map.
  useEffect(() => {
    let cancelled = false;
    let map: MapLibreMap | null = null;
    (async () => {
      const probe = document.createElement("canvas");
      if (!probe.getContext("webgl2") && !probe.getContext("webgl")) {
        setError("This browser cannot draw WebGL maps.");
        return;
      }
      const { Map: MapLibrary, setWorkerUrl } = await import("maplibre-gl");
      setWorkerUrl("/release/maplibre-gl-worker.mjs");
      if (cancelled || !container.current) {
        return;
      }
      const tokens = MAP_TOKENS[document.documentElement.dataset.theme === "dark" ? "dark" : "light"];
      map = new MapLibrary({
        container: container.current,
        style: { version: 8, sources: {}, layers: [{ id: "sea", type: "background", paint: { "background-color": tokens.sea } }] },
        bounds: [79.4, 5.8, 82.1, 9.95],
        minZoom: 5,
        maxZoom: 15,
        maxBounds: [76.5, 3.5, 85, 12.5],
        attributionControl: false,
        dragRotate: false,
        pitchWithRotate: false,
        doubleClickZoom: false,
      });
      map.touchZoomRotate.disableRotation();
      mapRef.current = map;
      map.on("load", async () => {
        const [overview, mesh] = await Promise.all([loadOverview(), loadMesh()]);
        if (!map) {
          return;
        }
        map.addSource("overview", { type: "geojson", data: overview as never, tolerance: 0 });
        map.addSource("mesh", { type: "geojson", data: mesh as never, tolerance: 0 });
        map.addSource("shape", { type: "geojson", data: EMPTY });
        map.addLayer({ id: "land", type: "fill", source: "overview", paint: { "fill-color": tokens.land, "fill-antialias": false } });
        map.addLayer({
          id: "mesh",
          type: "line",
          source: "mesh",
          layout: { "line-join": "round" },
          paint: { "line-color": ["case", ["==", ["get", "rank"], 0], tokens.coast, tokens.border], "line-width": 0.8 } as never,
        });
        map.addLayer({ id: "shape-fill", type: "fill", source: "shape", filter: ["==", "$type", "Polygon"], paint: { "fill-color": tokens.select, "fill-opacity": 0.22 } });
        map.addLayer({ id: "shape-line", type: "line", source: "shape", filter: ["!=", "$type", "Point"], paint: { "line-color": tokens.highlight, "line-width": 1.6 } });
        map.addLayer({ id: "shape-vertex", type: "circle", source: "shape", filter: ["==", "$type", "Point"], paint: { "circle-radius": 4, "circle-color": tokens.select, "circle-stroke-color": tokens.highlight, "circle-stroke-width": 1.2 } });
        const start = readUrl().shape;
        if (start?.kind === "circle") {
          const box = circleBox(start.centre, start.radiusKm * 2.5);
          map.fitBounds([box[0], box[1], box[2], box[3]], { padding: 24, duration: 0 });
        }
        setReady(true);
      });
      map.on("click", (event: MapMouseEvent) => {
        const point: LonLat = [event.lngLat.lng, event.lngLat.lat];
        if (modeRef.current === "circle") {
          setShape({ kind: "circle", centre: point, radiusKm: radiusRef.current });
        } else if (modeRef.current === "polygon") {
          setDraft((current) => [...current, point]);
        } else {
          setResolved({ point, rows: [], note: "Looking up…" });
        }
      });
      map.on("dblclick", () => {
        if (modeRef.current === "polygon") {
          setDraft((current) => {
            if (current.length >= 3) {
              setShape({ kind: "polygon", ring: [...current, current[0]] });
            }
            return [];
          });
        }
      });
    })().catch(() => setError("The map could not start."));
    return () => {
      cancelled = true;
      map?.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) {
      return;
    }
    const tokens = MAP_TOKENS[theme];
    map.setPaintProperty("sea", "background-color", tokens.sea);
    map.setPaintProperty("land", "fill-color", tokens.land);
  }, [ready, theme]);

  // Draw the shape.
  useEffect(() => {
    const source = mapRef.current?.getSource("shape") as GeoJSONSource | undefined;
    source?.setData(shapeFeatures(shape, draft, mode === "point" ? (resolved?.point ?? null) : null) as never);
  }, [shape, draft, ready, resolved, mode]);

  // Keep the URL shareable for circles.
  useEffect(() => {
    const params = new URLSearchParams();
    if (shape?.kind === "circle") {
      params.set("lon", shape.centre[0].toFixed(5));
      params.set("lat", shape.centre[1].toFixed(5));
      params.set("r", String(shape.radiusKm));
    }
    if (indicator) {
      params.set("ind", indicator);
    }
    window.history.replaceState(null, "", `${window.location.pathname}?${params.toString()}`);
  }, [shape, indicator]);

  // Estimate.
  const shapeKey = shape ? JSON.stringify(shape) : "";
  const key = `${shapeKey}|${indicator}`;
  useEffect(() => {
    if (!shape || !indicator) {
      return;
    }
    let cancelled = false;
    (async () => {
      const units = await loadUnits();
      const box: Box = shape.kind === "circle" ? circleBox(shape.centre, shape.radiusKm) : boxOf(shape.ring as LonLat[]);
      const districts = Object.entries(units)
        .filter(([, unit]) => unit.l === 2 && unit.b && boxesOverlap(unit.b, box))
        .map(([id]) => id);
      const [grids, values] = await Promise.all([
        Promise.all(districts.map((id) => loadJson<GridFile>(atlas(`grid/${id}.json`)))),
        loadLevelValues(indicator, "gn"),
      ]);
      const contains =
        shape.kind === "circle"
          ? (point: [number, number]) => distanceKm(shape.centre, point) <= shape.radiusKm
          : (point: [number, number]) => inRing(point, shape.ring);
      const value = estimateArea(grids, values, contains);
      if (!cancelled) {
        setResult({ key, value });
      }
    })().catch(() => !cancelled && setError("The grid files could not be loaded for this area."));
    return () => {
      cancelled = true;
    };
  }, [key, shape, indicator]);

  // Resolve a point.
  const resolvedPoint = resolved?.point;
  useEffect(() => {
    if (!resolvedPoint) {
      return;
    }
    let cancelled = false;
    (async () => {
      const [overview, units] = await Promise.all([loadOverview(), loadUnits()]);
      const ds = overview.features.find((feature) => inGeometry(resolvedPoint, feature.geometry));
      const rows: Resolved["rows"] = [];
      let note: string | null = null;
      if (!ds) {
        note = "No division contains this point: it is at sea or in a gap of the boundary source.";
      } else {
        const district = ds.properties.district;
        const detail = await loadDetail(district);
        const gn = detail.gn.features.find((feature) => inGeometry(resolvedPoint, feature.geometry));
        if (gn) {
          rows.push({ level: "GN division", id: gn.properties.id, name: detail.units[gn.properties.id]?.n ?? null });
        } else {
          note = "The point is on the edge of a GN division in the simplified map geometry; the exact answer needs the full boundaries.";
        }
        const nameOf = (id: string) => (units[id] as Unit | undefined)?.n ?? null;
        rows.push({ level: "DS division", id: ds.properties.ds, name: nameOf(ds.properties.ds) });
        rows.push({ level: "District", id: district, name: nameOf(district) });
        rows.push({ level: "Province", id: ds.properties.province, name: nameOf(ds.properties.province) });
        const lookup = await loadJson<{ district_to_ed: Record<string, string> }>(atlas("resolver.json")).catch(() => null);
        const ed = lookup?.district_to_ed[district];
        if (ed) {
          const electoral = await loadElectoral().catch(() => null);
          rows.push({ level: "Electoral district", id: ed, name: electoral?.eds.find((item) => item.id === ed)?.name ?? null });
        }
      }
      if (!cancelled) {
        setResolved({ point: resolvedPoint, rows, note });
      }
    })().catch(() => !cancelled && setResolved({ point: resolvedPoint, rows: [], note: "The lookup failed." }));
    return () => {
      cancelled = true;
    };
  }, [resolvedPoint]);

  const chosen = indicators.find((item) => item.id === indicator);
  const estimate = result?.key === key ? result.value : null;
  const areaKm2 = useMemo(() => (shape?.kind === "circle" ? Math.PI * shape.radiusKm ** 2 : null), [shape]);

  return (
    <div className="area-tool">
      <div className="area-map" ref={container} role="img" aria-label="Map for drawing an area" />
      <aside className="area-panel" aria-live="polite">
        <div className="area-modes" role="radiogroup" aria-label="Tool">
          {(
            [
              ["circle", "Radius"],
              ["polygon", "Draw"],
              ["point", "What is here"],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              role="radio"
              aria-checked={mode === id}
              className={mode === id ? "is-active" : undefined}
              onClick={() => {
                setMode(id);
                setDraft([]);
              }}
            >
              {label}
            </button>
          ))}
        </div>
        {error ? <p className="atlas-empty">{error}</p> : null}
        {mode === "point" ? (
          <section>
            <p className="area-help">Click the map to see which places contain that point.</p>
            {resolved ? (
              <>
                <p className="area-coords">
                  {resolved.point[1].toFixed(5)}° N, {resolved.point[0].toFixed(5)}° E
                </p>
                {resolved.rows.length ? (
                  <table className="mini-table" data-testid="resolver-table">
                    <tbody>
                      {resolved.rows.map((row) => (
                        <tr key={row.level}>
                          <th scope="row">{row.level}</th>
                          <td>
                            <a href={row.id.startsWith("LK-ED") ? "/elections" : `/?place=${row.id}`}>{row.name ?? row.id}</a>{" "}
                            <code>{row.id}</code>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : null}
                {resolved.note ? <p className="atlas-note">{resolved.note}</p> : null}
                <p className="atlas-note">
                  Looked up in the map&rsquo;s simplified boundaries (about 30 m). Within a few tens
                  of metres of a border the answer can differ from the full COD-AB boundaries; the
                  pipeline command <code>slf resolve</code> uses those.
                </p>
              </>
            ) : null}
          </section>
        ) : (
          <section>
            <label className="area-field">
              <span>Count</span>
              <select value={indicator} onChange={(event) => setIndicator(event.target.value)}>
                {indicators.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            {mode === "circle" ? (
              <label className="area-field">
                <span>Radius: {radius} km</span>
                <input
                  type="range"
                  min={0.5}
                  max={25}
                  step={0.5}
                  value={radius}
                  onChange={(event) => {
                    const next = Number(event.target.value);
                    setRadius(next);
                    setShape((current) => (current?.kind === "circle" ? { ...current, radiusKm: next } : current));
                  }}
                />
              </label>
            ) : null}
            <p className="area-help">
              {mode === "circle"
                ? "Click the map to place the centre."
                : draft.length
                  ? `${draft.length} points. Double-click to close the shape.`
                  : "Click to add corners; double-click to finish."}
            </p>
            {!shape ? null : !estimate ? (
              <p className="atlas-empty">Estimating…</p>
            ) : (
              <>
                <p className="atlas-kicker">{chosen?.name} inside this area</p>
                <p className="atlas-figure" data-testid="area-estimate">
                  ≈ {formatNumber(Math.round(estimate.estimate))}
                </p>
                <p className="atlas-rank">
                  {estimate.gns.length} GN divisions touched, {estimate.wholeGns} of them wholly
                  inside; {formatNumber(estimate.cells)} grid cells
                  {areaKm2 ? `, about ${formatNumber(Math.round(areaKm2))} km²` : ""}.
                </p>
                <p className="atlas-note">
                  <span className="tag">modelled estimate</span> Census 2024 counts are published
                  for whole GN divisions. Where the area cuts a division, its count is shared
                  equally over its grid cells (H3, about 0.1 km² each), as if people were spread
                  evenly. The true figure for part of a division is not known.
                </p>
                {estimate.missing.length ? (
                  <p className="atlas-note">
                    {estimate.missing.length} GN divisions in the area have no published value and
                    are not counted: {estimate.missing.slice(0, 8).join(", ")}
                    {estimate.missing.length > 8 ? "…" : ""}
                  </p>
                ) : null}
                <details className="atlas-sources">
                  <summary>Divisions in the area</summary>
                  <table className="mini-table">
                    <thead>
                      <tr>
                        <th scope="col">GN division</th>
                        <th scope="col">Share inside</th>
                        <th scope="col">Counted</th>
                      </tr>
                    </thead>
                    <tbody>
                      {estimate.gns.slice(0, 40).map((gn) => (
                        <tr key={gn.id}>
                          <th scope="row">
                            <a href={`/?place=${gn.id}`}>{gn.id}</a>
                          </th>
                          <td>{Math.round((100 * gn.inside) / gn.total)}%</td>
                          <td>{gn.value === null ? "no value" : formatNumber(Math.round((gn.value * gn.inside) / gn.total))}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </details>
              </>
            )}
          </section>
        )}
      </aside>
    </div>
  );
}
