"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import type { GeoJSONSource, Map as MapLibreMap } from "maplibre-gl";

import BasemapSwitch from "@/components/atlas/basemap-switch";
import {
  basemapStyle,
  OSM_FILL_OPACITY,
  readBasemap,
  saveBasemap,
  setBasemap,
  type Basemap,
} from "@/lib/atlas/basemap";

import {
  loadDetail,
  loadEdMesh,
  loadEdOutlines,
  loadFine,
  loadMesh,
  loadOutlines,
  loadOverview,
} from "@/lib/atlas/data";
import { DETAIL_ZOOM, LEVEL_MIN_ZOOM, LEVEL_RANK, type MapLevel } from "@/lib/atlas/scale";
import type {
  AreaProps,
  Collection,
  EdOutlines,
  Feature,
  FeaturePoint,
  FineFile,
  GnUnit,
  LevelName,
  MeshProps,
  OutlineProps,
  Unit,
} from "@/lib/atlas/types";

/**
 * Vector strokes and surfaces of the map, per theme. One place for every map colour and
 * stroke width, so borders stay consistent across scales and themes.
 */
export const MAP_TOKENS = {
  light: {
    sea: "#eef0f4",
    land: "#dcdfe7",
    nodata: "#d3d6de",
    coast: "#5b6274",
    border: "#f7f8fa",
    selectCasing: "#0a0e1a",
    select: "#f2b400",
    highlight: "#0a0e1a",
    hover: "#ffffff",
  },
  dark: {
    sea: "#090c14",
    land: "#1c2232",
    nodata: "#232a3b",
    coast: "#8c95ab",
    border: "#090c14",
    selectCasing: "#090c14",
    select: "#f2b400",
    highlight: "#eef0f6",
    hover: "#ffffff",
  },
} as const;

/** Stroke width by border rank (0 coast, 1 province, 2 district, 3 DS, 4 GN) at two zooms. */
const STROKE_LOW = ["match", ["get", "rank"], 0, 0.7, 1, 1.5, 2, 0.8, 3, 0.4, 0.3];
const STROKE_HIGH = ["match", ["get", "rank"], 0, 1.1, 1, 3, 2, 2, 3, 1.2, 0.6];
const STROKE_WIDTH = ["interpolate", ["linear"], ["zoom"], 6, STROKE_LOW, 12, STROKE_HIGH];

export type AtlasMapHandle = {
  fit: (box: [number, number, number, number], band?: [number, number]) => void;
  zoomBy: (delta: number) => void;
  zoomTo: (zoom: number) => void;
};

type Selected = { id: string; level: LevelName } | null;

type Props = {
  theme: "light" | "dark";
  level: MapLevel;
  /** Fill colour per unit id at `level`; null draws neutral land. */
  colors: Map<string, string> | null;
  selected: Selected;
  /** Fade everything outside the selected unit (when looking at its parts). */
  dimOutside: boolean;
  /** DS ids to ring, for example the places most like the selected one. */
  highlight: string[];
  units: Record<string, Unit> | null;
  /** Electoral district label points, when the ED scheme is in the bundle. */
  edLabels: Record<string, [number, number] | null> | null;
  nameOf: (id: string) => string;
  parentOf: (id: string) => string | null;
  tooltip: (id: string) => { title: string; detail: string | null } | null;
  inset: { right: number; bottom: number };
  onReady: () => void;
  onZoom: (zoom: number) => void;
  onSelect: (id: string | null) => void;
  onError: (message: string) => void;
  /** Named public features of the district in view, drawn from zoom 11. */
  points?: FeaturePoint[] | null;
};

const EMPTY = { type: "FeatureCollection" as const, features: [] };

export const POINT_COLORS: Record<string, string> = {
  school: "#1c3fae",
  health: "#c0362c",
  heritage: "#c98a00",
  place: "#5b6274",
};
export const POINT_LABELS: Record<string, string> = {
  school: "School",
  health: "Health facility",
  heritage: "Wikidata place",
  place: "Place name (GeoNames)",
};
const FILL_LAYERS = ["ov-fill", "ov-fill-pending", "gn-fill"] as const;
const MAX_LABELS = 70;

function fillExpression(
  key: string,
  colors: Map<string, string> | null,
  nodata: string,
  land: string,
): unknown {
  if (!colors) {
    return land;
  }
  const groups = new Map<string, string[]>();
  for (const [id, color] of colors) {
    const group = groups.get(color);
    if (group) {
      group.push(id);
    } else {
      groups.set(color, [id]);
    }
  }
  if (groups.size === 0) {
    return nodata;
  }
  const expression: unknown[] = ["match", ["get", key]];
  for (const [color, ids] of groups) {
    expression.push(ids, color);
  }
  expression.push(nodata);
  return expression;
}

const AtlasMap = forwardRef<AtlasMapHandle, Props>(function AtlasMap(props, ref) {
  const container = useRef<HTMLDivElement | null>(null);
  const labelLayer = useRef<HTMLDivElement | null>(null);
  const tip = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const latest = useRef(props);
  const internals = useRef<{ ensureDetail: () => Promise<void>; scheduleLabels: () => void } | null>(
    null,
  );
  const [ready, setReady] = useState(false);
  const [basemap, setBasemapState] = useState<Basemap>("plain");
  const basemapRef = useRef<Basemap>("plain");
  /** Bumped whenever more geometry arrives, so selection and labels can use it. */
  const [dataVersion, setDataVersion] = useState(0);

  const store = useRef({
    overview: null as Collection<AreaProps> | null,
    outlines: null as Collection<OutlineProps> | null,
    fine: null as FineFile | null,
    fineRequested: false,
    districts: new Set<string>(),
    requested: new Set<string>(),
    gnFeatures: [] as Feature<AreaProps>[],
    gnById: new Map<string, Feature<AreaProps>>(),
    dsFine: new Map<string, Feature<OutlineProps>>(),
    detailMesh: [] as Feature<MeshProps>[],
    gnUnits: new Map<string, GnUnit>(),
    hover: null as string | null,
    labelFrame: 0,
    edOutlines: null as EdOutlines | null,
    edRequested: false,
  });

  useEffect(() => {
    latest.current = props;
  });

  useImperativeHandle(ref, () => ({
    fit(box, band) {
      const map = mapRef.current;
      if (!map) {
        return;
      }
      const { inset } = latest.current;
      const camera = map.cameraForBounds(
        [
          [box[0], box[1]],
          [box[2], box[3]],
        ],
        { padding: { top: 96, left: 28, right: inset.right + 28, bottom: inset.bottom + 28 } },
      );
      if (!camera) {
        return;
      }
      let zoom = camera.zoom ?? map.getZoom();
      if (band) {
        zoom = Math.min(Math.max(zoom, band[0] + 0.05), band[1] - 0.05);
      }
      const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      map.easeTo({ center: camera.center, zoom, duration: reduce ? 0 : 750 });
    },
    zoomBy(delta) {
      mapRef.current?.easeTo({ zoom: mapRef.current.getZoom() + delta, duration: 250 });
    },
    zoomTo(zoom) {
      mapRef.current?.easeTo({ zoom, duration: 500 });
    },
  }));

  // Create the map once.
  useEffect(() => {
    let cancelled = false;
    const state = store.current;

    function source(id: string): GeoJSONSource | undefined {
      return mapRef.current?.getSource(id) as GeoJSONSource | undefined;
    }

    async function ensureDetail() {
      const map = mapRef.current;
      const { units, selected, parentOf } = latest.current;
      if (!map || !units) {
        return;
      }
      const wanted = new Set<string>();
      if (map.getZoom() >= DETAIL_ZOOM - 1) {
        const bounds = map.getBounds();
        for (const [id, unit] of Object.entries(units)) {
          if (unit.l !== 2 || !unit.b) {
            continue;
          }
          const [west, south, east, north] = unit.b;
          if (
            west <= bounds.getEast() &&
            east >= bounds.getWest() &&
            south <= bounds.getNorth() &&
            north >= bounds.getSouth()
          ) {
            wanted.add(id);
          }
        }
      }
      // A selected GN or DS needs its district's detail for an exact outline.
      if (selected?.level === "gn") {
        const ds = parentOf(selected.id);
        const district = ds ? parentOf(ds) : null;
        if (district) {
          wanted.add(district);
        }
      }
      if (wanted.size === 0) {
        return;
      }
      if (!state.fineRequested) {
        state.fineRequested = true;
        loadFine()
          .then((fine) => {
            if (cancelled) {
              return;
            }
            state.fine = fine;
            source("mesh-fine")?.setData(fine.mesh);
            setDataVersion((value) => value + 1);
          })
          .catch(() => {
            state.fineRequested = false;
          });
      }
      for (const district of wanted) {
        if (state.requested.has(district)) {
          continue;
        }
        state.requested.add(district);
        loadDetail(district)
          .then((detail) => {
            if (cancelled) {
              return;
            }
            state.districts.add(district);
            for (const feature of detail.gn.features) {
              state.gnFeatures.push(feature);
              state.gnById.set(feature.properties.id, feature);
            }
            for (const feature of detail.outlines.features) {
              state.dsFine.set(feature.properties.id, feature);
            }
            state.detailMesh.push(...detail.mesh.features);
            for (const [id, unit] of Object.entries(detail.units)) {
              state.gnUnits.set(id, unit);
            }
            source("detail")?.setData({ type: "FeatureCollection", features: state.gnFeatures });
            source("mesh-detail")?.setData({
              type: "FeatureCollection",
              features: state.detailMesh,
            });
            // Overview polygons stay under districts whose detail has not arrived yet.
            map.setFilter("ov-fill-pending", [
              "!",
              ["in", ["get", "district"], ["literal", [...state.districts]]],
            ]);
            setDataVersion((value) => value + 1);
          })
          .catch(() => {
            state.requested.delete(district);
          });
      }
    }

    function drawLabels() {
      const map = mapRef.current;
      const layer = labelLayer.current;
      const { level, units, nameOf, selected } = latest.current;
      if (!map || !layer || !units) {
        return;
      }
      const bounds = map.getBounds();
      const depth = LEVEL_RANK[level];
      const candidates: { id: string; c: [number, number]; a: number }[] = [];
      if (level === "ed") {
        for (const [id, c] of Object.entries(latest.current.edLabels ?? {})) {
          if (c && bounds.contains(c)) {
            candidates.push({ id, c, a: 0 });
          }
        }
      } else if (level === "gn") {
        for (const [id, unit] of state.gnUnits) {
          if (unit.c && bounds.contains(unit.c)) {
            candidates.push({ id, c: unit.c, a: unit.a ?? 0 });
          }
        }
      } else {
        for (const [id, unit] of Object.entries(units)) {
          if (unit.l === depth && unit.c && bounds.contains(unit.c)) {
            candidates.push({ id, c: unit.c, a: unit.a ?? 0 });
          }
        }
      }
      // A level shown below its natural zoom (DS divisions on the whole island) would
      // clutter the map: label only the selected place and the ringed ones.
      const sparse = map.getZoom() < LEVEL_MIN_ZOOM[level] - 0.4;
      if (sparse) {
        const keep = new Set([selected?.id, ...latest.current.highlight]);
        for (let i = candidates.length - 1; i >= 0; i -= 1) {
          if (!keep.has(candidates[i].id)) {
            candidates.splice(i, 1);
          }
        }
      }
      candidates.sort(
        (a, b) => Number(b.id === selected?.id) - Number(a.id === selected?.id) || b.a - a.a,
      );
      const size = map.getContainer().getBoundingClientRect();
      const charWidth = level === "province" ? 8.6 : 6.3;
      const placed: [number, number, number, number][] = [];
      let used = 0;
      for (const candidate of candidates) {
        if (used >= MAX_LABELS) {
          break;
        }
        const point = map.project(candidate.c);
        const text = nameOf(candidate.id);
        const half = (text.length * charWidth) / 2 + 5;
        const box: [number, number, number, number] = [
          point.x - half,
          point.y - 9,
          point.x + half,
          point.y + 9,
        ];
        if (box[2] < 0 || box[0] > size.width || box[3] < 0 || box[1] > size.height) {
          continue;
        }
        if (placed.some((p) => box[0] < p[2] && box[2] > p[0] && box[1] < p[3] && box[3] > p[1])) {
          continue;
        }
        placed.push(box);
        let node = layer.children[used] as HTMLSpanElement | undefined;
        if (!node) {
          node = document.createElement("span");
          layer.appendChild(node);
        }
        node.textContent = text;
        node.className =
          candidate.id === selected?.id
            ? `atlas-label atlas-label-${level} is-selected`
            : `atlas-label atlas-label-${level}`;
        node.style.transform = `translate(${Math.round(point.x)}px, ${Math.round(point.y)}px) translate(-50%, -50%)`;
        node.hidden = false;
        used += 1;
      }
      for (let i = used; i < layer.children.length; i += 1) {
        (layer.children[i] as HTMLSpanElement).hidden = true;
      }
    }

    function scheduleLabels() {
      if (state.labelFrame) {
        return;
      }
      state.labelFrame = window.requestAnimationFrame(() => {
        state.labelFrame = 0;
        drawLabels();
      });
    }

    function unitAt(point: { x: number; y: number }): string | null {
      const map = mapRef.current;
      if (!map) {
        return null;
      }
      const features = map.queryRenderedFeatures([point.x, point.y], {
        layers: [...FILL_LAYERS],
      });
      const key = latest.current.level;
      for (const feature of features) {
        const id = (feature.properties as Record<string, unknown>)[key];
        if (typeof id === "string") {
          return id;
        }
      }
      return null;
    }

    function setHover(id: string | null) {
      const map = mapRef.current;
      if (!map || state.hover === id) {
        return;
      }
      state.hover = id;
      const filter = ["==", ["get", latest.current.level], id ?? "__none__"];
      map.setFilter("ov-hover", filter as never);
      map.setFilter("gn-hover", filter as never);
      map.getCanvas().style.cursor = id ? "pointer" : "";
    }

    async function start() {
      try {
        const probe = document.createElement("canvas");
        if (!probe.getContext("webgl2") && !probe.getContext("webgl")) {
          latest.current.onError("This browser cannot draw WebGL maps.");
          return;
        }
        // Start fetching geometry now; it is needed as soon as the style is ready.
        void loadOverview().catch(() => undefined);
        void loadMesh().catch(() => undefined);
        void loadOutlines().catch(() => undefined);
        const { Map: MapLibrary, setWorkerUrl } = await import("maplibre-gl");
        setWorkerUrl("/release/maplibre-gl-worker.mjs");
        if (cancelled || !container.current) {
          return;
        }
        const tokens = MAP_TOKENS[latest.current.theme];
        const map = new MapLibrary({
          container: container.current,
          style: basemapStyle(tokens.sea, basemapRef.current),
          bounds: [79.4, 5.8, 82.1, 9.95],
          fitBoundsOptions: {
            padding: {
              top: 96,
              left: 28,
              right: latest.current.inset.right + 28,
              bottom: latest.current.inset.bottom + 28,
            },
          },
          minZoom: 5,
          maxZoom: 15,
          maxBounds: [76.5, 3.5, 85, 12.5],
          attributionControl: { compact: true },
          dragRotate: false,
          pitchWithRotate: false,
          touchPitch: false,
        });
        map.touchZoomRotate.disableRotation();
        map.keyboard.disableRotation();
        // Places are reachable from the panel's lists; the canvas is not a tab stop.
        map.getCanvas().tabIndex = -1;
        mapRef.current = map;

        map.on("load", async () => {
          for (const id of [
            "overview",
            "detail",
            "mesh",
            "mesh-fine",
            "mesh-detail",
            "ed-mesh",
            "points",
            "sel-coarse",
            "sel-fine",
            "hl-coarse",
            "hl-fine",
          ]) {
            // tolerance 0: the tiler must not simplify each polygon on its own, or neighbours
            // that share a border exactly would drift apart and show slivers.
            map.addSource(id, { type: "geojson", data: EMPTY, tolerance: 0 });
          }
          // Fills never antialias their own edge: borders come from the shared mesh, drawn
          // once, so two neighbours cannot leave a seam or a doubled outline between them.
          const fill = { "fill-color": tokens.land, "fill-antialias": false };
          map.addLayer({ id: "ov-fill", type: "fill", source: "overview", maxzoom: DETAIL_ZOOM, paint: fill });
          map.addLayer({
            id: "ov-fill-pending",
            type: "fill",
            source: "overview",
            minzoom: DETAIL_ZOOM,
            paint: fill,
          });
          map.addLayer({ id: "gn-fill", type: "fill", source: "detail", minzoom: DETAIL_ZOOM, paint: fill });
          const hover = { "fill-color": tokens.hover, "fill-opacity": 0.22, "fill-antialias": false };
          const none = ["==", ["get", "ds"], "__none__"] as never;
          map.addLayer({
            id: "ov-hover",
            type: "fill",
            source: "overview",
            maxzoom: DETAIL_ZOOM,
            paint: hover,
            filter: none,
          });
          map.addLayer({
            id: "gn-hover",
            type: "fill",
            source: "detail",
            minzoom: DETAIL_ZOOM,
            paint: hover,
            filter: none,
          });
          const line = { "line-join": "round", "line-cap": "round" } as const;
          const stroke = {
            "line-color": ["case", ["==", ["get", "rank"], 0], tokens.coast, tokens.border],
            "line-width": STROKE_WIDTH,
          } as never;
          map.addLayer({ id: "mesh", type: "line", source: "mesh", maxzoom: DETAIL_ZOOM, layout: line, paint: stroke });
          map.addLayer({
            id: "mesh-detail",
            type: "line",
            source: "mesh-detail",
            minzoom: DETAIL_ZOOM,
            layout: line,
            paint: stroke,
          });
          map.addLayer({
            id: "mesh-fine",
            type: "line",
            source: "mesh-fine",
            minzoom: DETAIL_ZOOM,
            layout: line,
            paint: stroke,
          });
          // Electoral districts: their own border mesh (district borders inside an ED, such as
          // Jaffna and Kilinochchi, are not ED borders), shown only at the ED scale.
          map.addLayer({
            id: "ed-mesh",
            type: "line",
            source: "ed-mesh",
            layout: { ...line, visibility: "none" },
            paint: stroke,
          });
          map.addLayer({
            id: "points",
            type: "circle",
            source: "points",
            minzoom: 11,
            paint: {
              "circle-radius": ["interpolate", ["linear"], ["zoom"], 11, 2.5, 15, 5],
              "circle-color": [
                "match",
                ["get", "k"],
                "school",
                POINT_COLORS.school,
                "health",
                POINT_COLORS.health,
                "heritage",
                POINT_COLORS.heritage,
                POINT_COLORS.place,
              ],
              "circle-stroke-color": tokens.border,
              "circle-stroke-width": 1,
            } as never,
          });
          for (const [id, src, zoom] of [
            ["hl-coarse", "hl-coarse", { maxzoom: DETAIL_ZOOM }],
            ["hl-fine", "hl-fine", { minzoom: DETAIL_ZOOM }],
          ] as const) {
            map.addLayer({
              id,
              type: "line",
              source: src,
              ...zoom,
              layout: line,
              paint: { "line-color": tokens.highlight, "line-width": 1.6 },
            });
          }
          for (const [suffix, src, zoom] of [
            ["coarse", "sel-coarse", { maxzoom: DETAIL_ZOOM }],
            ["fine", "sel-fine", { minzoom: DETAIL_ZOOM }],
          ] as const) {
            map.addLayer({
              id: `sel-casing-${suffix}`,
              type: "line",
              source: src,
              ...zoom,
              layout: line,
              paint: { "line-color": tokens.selectCasing, "line-width": 5 },
            });
            map.addLayer({
              id: `sel-${suffix}`,
              type: "line",
              source: src,
              ...zoom,
              layout: line,
              paint: { "line-color": tokens.select, "line-width": 2.6 },
            });
          }
          try {
            const [overview, mesh, outlines] = await Promise.all([
              loadOverview(),
              loadMesh(),
              loadOutlines(),
            ]);
            if (cancelled) {
              return;
            }
            state.overview = overview;
            state.outlines = outlines;
            source("overview")?.setData(overview);
            source("mesh")?.setData(mesh);
            setReady(true);
            setDataVersion((value) => value + 1);
            latest.current.onReady();
            latest.current.onZoom(map.getZoom());
          } catch (caught) {
            latest.current.onError(
              caught instanceof Error ? caught.message : "Map geometry failed to load.",
            );
          }
        });

        map.on("zoom", () => latest.current.onZoom(map.getZoom()));
        map.on("move", scheduleLabels);
        map.on("moveend", () => {
          void ensureDetail();
          scheduleLabels();
        });
        map.on("mousemove", (event) => {
          const point = map.getLayer("points")
            ? map.queryRenderedFeatures(event.point, { layers: ["points"] })[0]
            : undefined;
          if (point && tip.current) {
            const node = tip.current;
            (node.firstChild as HTMLElement).textContent = String(point.properties?.n ?? "");
            (node.lastChild as HTMLElement).textContent = POINT_LABELS[String(point.properties?.k)] ?? "";
            node.style.transform = `translate(${event.point.x + 14}px, ${event.point.y + 14}px)`;
            node.hidden = false;
            return;
          }
          const id = unitAt(event.point);
          setHover(id);
          const node = tip.current;
          if (!node) {
            return;
          }
          const content = id ? latest.current.tooltip(id) : null;
          if (!content) {
            node.hidden = true;
            return;
          }
          (node.firstChild as HTMLElement).textContent = content.title;
          (node.lastChild as HTMLElement).textContent = content.detail ?? "";
          node.style.transform = `translate(${event.point.x + 14}px, ${event.point.y + 14}px)`;
          node.hidden = false;
        });
        map.on("mouseout", () => {
          setHover(null);
          if (tip.current) {
            tip.current.hidden = true;
          }
        });
        map.on("click", (event) => latest.current.onSelect(unitAt(event.point)));
        map.on("error", (event) => {
          if (event.error) {
            console.error(event.error);
          }
        });
        map.on("data", scheduleLabels);
        internals.current = { ensureDetail, scheduleLabels };
      } catch (caught) {
        latest.current.onError(caught instanceof Error ? caught.message : "Map failed to load.");
      }
    }

    void start();
    const observer = new ResizeObserver(() => mapRef.current?.resize());
    if (container.current) {
      observer.observe(container.current);
    }
    return () => {
      cancelled = true;
      observer.disconnect();
      window.cancelAnimationFrame(state.labelFrame);
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  const { theme, level, colors, selected, dimOutside, highlight, units, points } = props;

  // Named public features of the district in view.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) {
      return;
    }
    const target = map.getSource("points") as GeoJSONSource | undefined;
    target?.setData({
      type: "FeatureCollection",
      features: (points ?? []).map(([lon, lat, k, n]) => ({
        type: "Feature",
        properties: { k, n },
        geometry: { type: "Point", coordinates: [lon, lat] },
      })),
    });
  }, [points, ready]);

  // Theme: surfaces and strokes.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) {
      return;
    }
    const tokens = MAP_TOKENS[theme];
    map.setPaintProperty("sea", "background-color", tokens.sea);
    for (const id of ["mesh", "mesh-detail", "mesh-fine", "ed-mesh"]) {
      map.setPaintProperty(id, "line-color", [
        "case",
        ["==", ["get", "rank"], 0],
        tokens.coast,
        tokens.border,
      ]);
    }
    for (const id of ["hl-coarse", "hl-fine"]) {
      map.setPaintProperty(id, "line-color", tokens.highlight);
    }
    for (const suffix of ["coarse", "fine"]) {
      map.setPaintProperty(`sel-casing-${suffix}`, "line-color", tokens.selectCasing);
    }
  }, [ready, theme]);

  // Fill colours, the borders in view, and the focus on the selected unit.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) {
      return;
    }
    const tokens = MAP_TOKENS[theme];
    const expression = fillExpression(level, colors, tokens.nodata, tokens.land);
    const focus =
      dimOutside && selected && selected.level !== "country"
        ? ["case", ["==", ["get", selected.level], selected.id], 1, 0.32]
        : 1;
    const opacity = basemap === "osm" ? ["*", focus, OSM_FILL_OPACITY] : focus;
    for (const id of FILL_LAYERS) {
      map.setPaintProperty(id, "fill-color", expression as never);
      map.setPaintProperty(id, "fill-opacity", opacity as never);
    }
    const borders =
      level === "ed"
        ? ["==", ["get", "rank"], 0]
        : ["any", ["==", ["get", "rank"], 0], ["<=", ["get", "rank"], LEVEL_RANK[level]]];
    for (const id of ["mesh", "mesh-detail", "mesh-fine"]) {
      map.setFilter(id, borders as never);
    }
    map.setLayoutProperty("ed-mesh", "visibility", level === "ed" ? "visible" : "none");
    const state = store.current;
    if (level === "ed" && !state.edRequested) {
      state.edRequested = true;
      Promise.all([loadEdMesh(), loadEdOutlines()])
        .then(([mesh, outlines]) => {
          (map.getSource("ed-mesh") as GeoJSONSource | undefined)?.setData(mesh);
          state.edOutlines = outlines;
          setDataVersion((value) => value + 1);
        })
        .catch(() => {
          state.edRequested = false;
        });
    }
    internals.current?.scheduleLabels();
  }, [basemap, colors, dimOutside, level, ready, selected, theme]);

  // Basemap: plain by default; the viewer's remembered choice applies after the first render.
  useEffect(() => {
    const stored = readBasemap("plain");
    basemapRef.current = stored;
    setBasemapState(stored);
  }, []);
  useEffect(() => {
    basemapRef.current = basemap;
    if (mapRef.current && ready) {
      setBasemap(mapRef.current, basemap);
    }
  }, [basemap, ready]);

  // Selection and highlight outlines, at the geometry tier in view.
  useEffect(() => {
    const map = mapRef.current;
    const state = store.current;
    if (!map || !ready) {
      return;
    }
    function geometry(id: string, unitLevel: LevelName): { coarse: unknown[]; fine: unknown[] } {
      if (unitLevel === "ed") {
        const coarse = state.edOutlines?.coarse.features.find((f) => f.properties.id === id);
        const fine = state.edOutlines?.fine.features.find((f) => f.properties.id === id) ?? coarse;
        return { coarse: coarse ? [coarse] : [], fine: fine ? [fine] : [] };
      }
      if (unitLevel === "gn") {
        const feature = state.gnById.get(id);
        return { coarse: feature ? [feature] : [], fine: feature ? [feature] : [] };
      }
      if (unitLevel === "ds") {
        const coarse = state.overview?.features.find((f) => f.properties.id === id);
        const fine = state.dsFine.get(id) ?? coarse;
        return { coarse: coarse ? [coarse] : [], fine: fine ? [fine] : [] };
      }
      const coarse = state.outlines?.features.find((f) => f.properties.id === id);
      const fine = state.fine?.outlines.features.find((f) => f.properties.id === id) ?? coarse;
      return { coarse: coarse ? [coarse] : [], fine: fine ? [fine] : [] };
    }
    const set = (id: string, features: unknown[]) =>
      (map.getSource(id) as GeoJSONSource | undefined)?.setData({
        type: "FeatureCollection",
        features,
      } as never);
    const chosen = selected && selected.level !== "country" ? geometry(selected.id, selected.level) : null;
    set("sel-coarse", chosen?.coarse ?? []);
    set("sel-fine", chosen?.fine ?? []);
    const rings = highlight.map((id) => geometry(id, "ds"));
    set("hl-coarse", rings.flatMap((ring) => ring.coarse));
    set("hl-fine", rings.flatMap((ring) => ring.fine));
    void internals.current?.ensureDetail();
  }, [dataVersion, highlight, ready, selected]);

  useEffect(() => {
    if (ready && units) {
      void internals.current?.ensureDetail();
      internals.current?.scheduleLabels();
    }
  }, [dataVersion, ready, units, level]);

  return (
    <div className="atlas-map">
      <div className="atlas-canvas" ref={container} aria-hidden="true" />
      <div className="atlas-labels" ref={labelLayer} aria-hidden="true" />
      <BasemapSwitch
        value={basemap}
        onChange={(next) => {
          saveBasemap(next);
          setBasemapState(next);
        }}
      />
      <div className="atlas-tip" ref={tip} hidden aria-hidden="true">
        <strong />
        <span />
      </div>
      {!ready ? (
        <p className="atlas-loading" role="status">
          Loading the map…
        </p>
      ) : null}
    </div>
  );
});

export default AtlasMap;
