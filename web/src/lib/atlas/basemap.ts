import type { Map as MapLibreMap, StyleSpecification } from "maplibre-gl";

/** The picture drawn under the boundaries. */
export type Basemap = "plain" | "osm";

export const BASEMAPS: { id: Basemap; label: string }[] = [
  { id: "plain", label: "Plain" },
  { id: "osm", label: "OpenStreetMap" },
];

export const OSM_ATTRIBUTION =
  '© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors';

const STORAGE_KEY = "slf-basemap";

/** Multiplier for boundary fills so the street map shows through. */
export const OSM_FILL_OPACITY = 0.5;

/**
 * A style holding the sea background and, always, the OpenStreetMap raster layer (hidden
 * unless chosen). The layer sits right above the background and below every boundary layer,
 * and no tile is requested while it is hidden.
 */
export function basemapStyle(seaColor: string, basemap: Basemap): StyleSpecification {
  return {
    version: 8,
    sources: {
      osm: {
        type: "raster",
        tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
        tileSize: 256,
        maxzoom: 19,
        attribution: OSM_ATTRIBUTION,
      },
    },
    layers: [
      { id: "sea", type: "background", paint: { "background-color": seaColor } },
      {
        id: "osm",
        type: "raster",
        source: "osm",
        layout: { visibility: basemap === "osm" ? "visible" : "none" },
      },
    ],
  };
}

export function setBasemap(map: MapLibreMap, basemap: Basemap): void {
  if (map.getLayer("osm")) {
    map.setLayoutProperty("osm", "visibility", basemap === "osm" ? "visible" : "none");
  }
}

/** The remembered choice, or the page's own default. Storage may be blocked or empty. */
export function readBasemap(fallback: Basemap): Basemap {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    return value === "plain" || value === "osm" ? value : fallback;
  } catch {
    return fallback;
  }
}

export function saveBasemap(basemap: Basemap): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, basemap);
  } catch {
    // Remembering the choice is a convenience only.
  }
}

export function osmLink(lon: number, lat: number, zoom = 17): string {
  return `https://www.openstreetmap.org/?mlat=${lat.toFixed(5)}&mlon=${lon.toFixed(5)}#map=${zoom}/${lat.toFixed(5)}/${lon.toFixed(5)}`;
}
