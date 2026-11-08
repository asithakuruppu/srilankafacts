"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import type { GeoJSONSource, Map as MapLibreMap } from "maplibre-gl";

import {
  fetchAreaDataset,
  type AreaDataset,
  type BoundaryCollection,
  type ValueRow,
} from "@/lib/areas";
import { formatValue } from "@/lib/format";

type MapViewProps = {
  indicatorId: string;
  levelName: string;
  boundaryLevel: number;
  unit: string;
  decimals?: number;
  selectedId?: string;
  nationalValue?: number | null;
  compare?: boolean;
  className?: string;
  preloaded?: AreaDataset | null;
};

const NO_DATA = "#d8d5cc";
const EMPTY_VALUES = new Map<string, ValueRow>();
const SEQUENTIAL = ["#e8f1ec", "#b9d8cd", "#7fb9a9", "#3f8d7b", "#125e50"];
const DIVERGING = ["#8c4a2f", "#d9a17c", "#f2efe9", "#8fc4b5", "#146356"];

function quantile(sorted: number[], fraction: number): number {
  if (sorted.length === 0) {
    return 0;
  }
  const position = (sorted.length - 1) * fraction;
  const base = Math.floor(position);
  const rest = position - base;
  if (sorted[base + 1] !== undefined) {
    return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
  }
  return sorted[base];
}

function classBreaks(values: number[]): number[] {
  const sorted = [...new Set(values)].sort((a, b) => a - b);
  if (sorted.length <= 5) {
    return sorted.slice(1);
  }
  return [0.2, 0.4, 0.6, 0.8].map((fraction) =>
    Number(quantile(sorted, fraction).toPrecision(6)),
  );
}

function colorExpression(compare: boolean, breaks: number[], national: number | null) {
  const palette = compare ? DIVERGING : SEQUENTIAL;
  if (compare && national !== null) {
    const span = Math.max(...breaks.map((value) => Math.abs(value - national)), 1);
    const step = span / 2;
    return {
      expression: [
        "case",
        ["has", "value"],
        [
          "step",
          ["get", "value"],
          palette[0],
          national - step,
          palette[1],
          national - step / 2,
          palette[2],
          national + step / 2,
          palette[3],
          national + step,
          palette[4],
        ],
        NO_DATA,
      ] as unknown as string,
      labels: [
        `< ${(national - step).toFixed(1)}`,
        `${(national - step).toFixed(1)} – ${(national - step / 2).toFixed(1)}`,
        `near national`,
        `${(national + step / 2).toFixed(1)} – ${(national + step).toFixed(1)}`,
        `> ${(national + step).toFixed(1)}`,
      ],
    };
  }
  const steps = breaks.filter((_, index) => index < 4);
  const expression = [
    "case",
    ["has", "value"],
    ["step", ["get", "value"], palette[0], ...steps.flatMap((value, index) => [value, palette[index + 1]])],
    NO_DATA,
  ] as unknown as string;
  return {
    expression,
    labels: [
      steps[0] !== undefined ? `≤ ${steps[0]}` : "lowest",
      steps[0] !== undefined && steps[1] !== undefined ? `${steps[0]} – ${steps[1]}` : "",
      steps[1] !== undefined && steps[2] !== undefined ? `${steps[1]} – ${steps[2]}` : "",
      steps[2] !== undefined && steps[3] !== undefined ? `${steps[2]} – ${steps[3]}` : "",
      steps[3] !== undefined ? `> ${steps[3]}` : "highest",
    ].filter(Boolean),
  };
}

export default function MapView({
  indicatorId,
  levelName,
  boundaryLevel,
  unit,
  decimals,
  selectedId,
  nationalValue = null,
  compare = false,
  className,
  preloaded = null,
}: MapViewProps) {
  const container = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const fitted = useRef(false);
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [fetched, setFetched] = useState<AreaDataset | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [legend, setLegend] = useState<{ color: string; label: string }[]>([]);

  useEffect(() => {
    let cancelled = false;
    let map: MapLibreMap | null = null;
    async function start() {
      try {
        const { Map: MapLibrary, setWorkerUrl } = await import("maplibre-gl");
        setWorkerUrl("/release/maplibre-gl-worker.mjs");
        if (cancelled || !container.current) {
          return;
        }
        const probe = document.createElement("canvas");
        if (!probe.getContext("webgl2") && !probe.getContext("webgl")) {
          setError("This browser cannot render WebGL maps. The table below has the same values.");
          return;
        }
        map = new MapLibrary({
          container: container.current,
          style: {
            version: 8,
            sources: {},
            layers: [
              {
                id: "background",
                type: "background",
                paint: { "background-color": "#f4f1e8" },
              },
            ],
          },
          center: [80.7, 7.6],
          zoom: 6.4,
          attributionControl: false,
          dragRotate: false,
        });
        mapRef.current = map;
        map.on("load", () => {
          if (!cancelled) {
            setReady(true);
          }
        });
        map.on("error", (event) => {
          if (!cancelled && event.error) {
            setError(`Map error: ${event.error.message}`);
          }
        });
      } catch (caught) {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Map failed to load.");
        }
      }
    }
    void start();
    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (preloaded) {
      return;
    }
    const controller = new AbortController();
    async function load() {
      try {
        const dataset = await fetchAreaDataset(
          indicatorId,
          levelName,
          boundaryLevel,
          controller.signal,
        );
        setFetched(dataset);
        setError(null);
      } catch (caught) {
        if (!controller.signal.aborted) {
          setError(caught instanceof Error ? caught.message : "Data failed to load.");
        }
      }
    }
    void load();
    return () => controller.abort();
  }, [boundaryLevel, indicatorId, levelName, preloaded]);

  const data: BoundaryCollection | null = preloaded?.boundary ?? fetched?.boundary ?? null;
  const values: Map<string, ValueRow> = preloaded?.values ?? fetched?.values ?? EMPTY_VALUES;

  const merged = useMemo(() => {
    if (!data) {
      return null;
    }
    return {
      type: "FeatureCollection" as const,
      features: data.features.map((feature) => {
        const row = values.get(feature.properties.geography_id);
        return {
          ...feature,
          properties: {
            ...feature.properties,
            ...(row && row.value !== null ? { value: row.value } : {}),
            unit: row?.unit ?? unit,
          },
        };
      }),
    };
  }, [data, values, unit]);

  const breaks = useMemo(
    () =>
      classBreaks(
        [...values.values()]
          .map((row) => row.value)
          .filter((value): value is number => value !== null && Number.isFinite(value)),
      ),
    [values],
  );

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !merged) {
      return;
    }
    const source = map.getSource("areas") as GeoJSONSource | undefined;
    if (!source) {
      map.addSource("areas", { type: "geojson", data: merged });
    } else {
      source.setData(merged);
    }
    const colors = colorExpression(compare, breaks, nationalValue);
    if (!map.getLayer("areas-fill")) {
      map.addLayer({
        id: "areas-fill",
        type: "fill",
        source: "areas",
        paint: { "fill-color": colors.expression, "fill-opacity": 0.9 },
      });
      map.addLayer({
        id: "areas-line",
        type: "line",
        source: "areas",
        paint: { "line-color": "#6b746f", "line-width": 0.4, "line-opacity": 0.55 },
      });
      map.addLayer({
        id: "areas-selected",
        type: "line",
        source: "areas",
        paint: { "line-color": "#a5641c", "line-width": 2.4 },
        filter: ["==", ["get", "geography_id"], selectedId ?? "__none__"],
      });
    } else {
      map.setPaintProperty("areas-fill", "fill-color", colors.expression);
      map.setFilter("areas-selected", [
        "==",
        ["get", "geography_id"],
        selectedId ?? "__none__",
      ]);
    }

    const maxLevel = boundaryLevel;
    map.setPaintProperty("areas-line", "line-width", maxLevel >= 4 ? 0.2 : 0.6);

    if (!fitted.current) {
      const coordinates: [number, number][] = [];
      for (const feature of merged.features) {
        const geometry = feature.geometry as {
          type: string;
          coordinates?: unknown;
        };
        const collect = (value: unknown): void => {
          if (!Array.isArray(value)) {
            return;
          }
          if (typeof value[0] === "number" && typeof value[1] === "number") {
            coordinates.push([value[0], value[1]]);
            return;
          }
          for (const child of value) {
            collect(child);
          }
        };
        collect(geometry.coordinates);
      }
      if (coordinates.length > 0) {
        const bounds = coordinates.reduce(
          (box, point) => [
            [Math.min(box[0][0], point[0]), Math.min(box[0][1], point[1])],
            [Math.max(box[1][0], point[0]), Math.max(box[1][1], point[1])],
          ],
          [
            [180, 90],
            [-180, -90],
          ],
        ) as [[number, number], [number, number]];
        map.fitBounds(bounds, { padding: 24, duration: 0 });
        fitted.current = true;
      }
    }
    setLegend(
      colors.labels.map((label, index) => ({
        color: (compare ? DIVERGING : SEQUENTIAL)[index] ?? NO_DATA,
        label,
      })),
    );
  }, [boundaryLevel, breaks, compare, merged, nationalValue, ready, selectedId]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) {
      return;
    }
    const source = map.getSource("areas") as GeoJSONSource | undefined;
    if (!source) {
      return;
    }
    const handleMove = async (event: { features?: unknown[]; lngLat: { lng: number; lat: number } }) => {
      const feature = event.features?.[0] as
        | { properties?: { geography_id?: string; name_en?: string; value?: number } }
        | undefined;
      if (!feature?.properties) {
        return;
      }
      const { Popup } = await import("maplibre-gl");
      const value = feature.properties.value;
      new Popup({ closeButton: false, offset: 8 })
        .setLngLat([event.lngLat.lng, event.lngLat.lat])
        .setHTML(
          `<strong>${escapeHtml(feature.properties.name_en ?? feature.properties.geography_id ?? "")}</strong><br/>${escapeHtml(
            formatValue(value ?? null, unit, decimals),
          )}`,
        )
        .addTo(map);
    };
    const handleLeave = () => {
      document.querySelectorAll(".maplibregl-popup").forEach((node) => node.remove());
    };
    const handleClick = (event: { features?: unknown[] }) => {
      const feature = event.features?.[0] as
        | { properties?: { geography_id?: string } }
        | undefined;
      if (feature?.properties?.geography_id) {
        router.push(`/place/${feature.properties.geography_id}`);
      }
    };
    map.on("mousemove", "areas-fill", handleMove);
    map.on("mouseleave", "areas-fill", handleLeave);
    map.on("click", "areas-fill", handleClick);
    map.getCanvas().style.cursor = "pointer";
    return () => {
      map.off("mousemove", "areas-fill", handleMove);
      map.off("mouseleave", "areas-fill", handleLeave);
      map.off("click", "areas-fill", handleClick);
    };
  }, [decimals, ready, router, unit]);

  return (
    <div className={`map ${className ?? ""}`}>
      <div className="map-canvas" ref={container} aria-hidden="true" />
      {error ? (
        <p className="map-status" role="status">
          {error}
        </p>
      ) : null}
      {!error && (!ready || !data) ? (
        <p className="map-status" role="status">
          Loading map…
        </p>
      ) : null}
      <div className="map-legend" aria-label="Map legend">
        {legend.map((entry) => (
          <span key={entry.label} className="legend-item">
            <span className="legend-swatch" style={{ background: entry.color }} />
            {entry.label}
          </span>
        ))}
        <span className="legend-item">
          <span className="legend-swatch" style={{ background: NO_DATA }} />
          no data
        </span>
      </div>
      <p className="map-note">
        Colours are quantile classes of the selected indicator. Areas are drawn from the
        COD-AB v03 boundaries; no basemap is used.
      </p>
    </div>
  );
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
