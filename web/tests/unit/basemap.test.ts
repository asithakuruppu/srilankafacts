import { afterEach, describe, expect, it, vi } from "vitest";

import { basemapStyle, osmLink, readBasemap, saveBasemap } from "@/lib/atlas/basemap";

describe("basemap", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("falls back to the page default when storage is empty or blocked", () => {
    const store = new Map<string, string>();
    vi.stubGlobal("window", {
      localStorage: { getItem: (k: string) => store.get(k) ?? null, setItem: (k: string, v: string) => void store.set(k, v) },
    });
    expect(readBasemap("osm")).toBe("osm");
    expect(readBasemap("plain")).toBe("plain");
    saveBasemap("plain");
    expect(readBasemap("osm")).toBe("plain");
    vi.stubGlobal("window", {
      localStorage: {
        getItem: () => {
          throw new Error("blocked");
        },
        setItem: () => {
          throw new Error("blocked");
        },
      },
    });
    expect(readBasemap("osm")).toBe("osm");
    expect(() => saveBasemap("plain")).not.toThrow();
  });

  it("hides the OSM layer unless chosen, under every boundary layer", () => {
    const plain = basemapStyle("#fff", "plain");
    const osm = basemapStyle("#fff", "osm");
    expect(plain.layers.map((l) => l.id)).toEqual(["sea", "osm"]);
    expect(plain.layers[1].layout?.visibility).toBe("none");
    expect(osm.layers[1].layout?.visibility).toBe("visible");
  });

  it("links to the exact spot on openstreetmap.org", () => {
    expect(osmLink(79.86123, 6.93456)).toBe(
      "https://www.openstreetmap.org/?mlat=6.93456&mlon=79.86123#map=17/6.93456/79.86123",
    );
  });
});
