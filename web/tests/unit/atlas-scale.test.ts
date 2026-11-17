import { describe, expect, it } from "vitest";

import { DETAIL_ZOOM, LEVEL_MIN_ZOOM, childLevel, levelForZoom, zoomBand } from "@/lib/atlas/scale";

describe("atlas scale rules", () => {
  const all = ["province", "district", "ds", "gn"] as const;

  it("moves to finer levels as the zoom grows", () => {
    expect(levelForZoom(6, [...all])).toBe("province");
    expect(levelForZoom(7.5, [...all])).toBe("district");
    expect(levelForZoom(9, [...all])).toBe("ds");
    expect(levelForZoom(12, [...all])).toBe("gn");
  });

  it("never shows a level the data does not have", () => {
    expect(levelForZoom(13, ["province", "district", "ds"])).toBe("ds");
    expect(levelForZoom(5, ["ds"])).toBe("ds");
  });

  it("gives each level a zoom band that ends where the next begins", () => {
    expect(zoomBand("district")).toEqual([LEVEL_MIN_ZOOM.district, LEVEL_MIN_ZOOM.ds]);
    expect(zoomBand("gn")[0]).toBe(LEVEL_MIN_ZOOM.gn);
  });

  it("loads detailed geometry before GN divisions come into view", () => {
    expect(DETAIL_ZOOM).toBeLessThan(LEVEL_MIN_ZOOM.gn);
  });

  it("walks down the hierarchy and stops at the GN division", () => {
    expect(childLevel("country")).toBe("province");
    expect(childLevel("ds")).toBe("gn");
    expect(childLevel("gn")).toBeNull();
  });
});
