import { describe, expect, it } from "vitest";

import { estimateArea, type GridFile } from "@/lib/atlas/area";
import { circleRing, distanceKm, inGeometry, inPolygon } from "@/lib/atlas/geo";

const grid: GridFile = {
  resolution: 9,
  gn: ["A", "B"],
  cells: [
    [0, 0, 0],
    [1, 0, 0],
    [2, 0, 1],
    [3, 0, 1],
    [4, 0, 1],
    [5, 0, 1],
  ],
};

describe("area estimate", () => {
  it("returns whole counts when every cell is inside", () => {
    const result = estimateArea([grid], new Map([["A", 100], ["B", 40]]), () => true);
    expect(result.estimate).toBe(140);
    expect(result.wholeGns).toBe(2);
    expect(result.cells).toBe(6);
  });

  it("shares a GN's count by the fraction of its cells inside", () => {
    const result = estimateArea([grid], new Map([["A", 100], ["B", 40]]), ([x]) => x <= 2);
    // All of A (100) and one of B's four cells (10).
    expect(result.estimate).toBeCloseTo(110, 10);
    expect(result.gns.find((g) => g.id === "B")?.inside).toBe(1);
  });

  it("names GNs with no value instead of counting them as zero", () => {
    const result = estimateArea([grid], new Map([["A", 100]]), () => true);
    expect(result.estimate).toBe(100);
    expect(result.missing).toEqual(["B"]);
  });
});

describe("geometry helpers", () => {
  it("respects holes in polygons", () => {
    const outer = [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]];
    const hole = [[4, 4], [6, 4], [6, 6], [4, 6], [4, 4]];
    expect(inPolygon([2, 2], [outer, hole])).toBe(true);
    expect(inPolygon([5, 5], [outer, hole])).toBe(false);
    expect(inGeometry([5, 5], { type: "MultiPolygon", coordinates: [[outer, hole], [hole]] })).toBe(true);
  });

  it("measures distance and draws circles of the right radius", () => {
    const colombo: [number, number] = [79.8612, 6.9271];
    const kandy: [number, number] = [80.6337, 7.2906];
    expect(distanceKm(colombo, kandy)).toBeGreaterThan(90);
    expect(distanceKm(colombo, kandy)).toBeLessThan(100);
    for (const point of circleRing(colombo, 5, 16)) {
      expect(distanceKm(colombo, point as [number, number])).toBeCloseTo(5, 1);
    }
  });
});
