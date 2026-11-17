import { describe, expect, it } from "vitest";

import {
  classIndex,
  describeDifference,
  divergingBreaks,
  histogram,
  median,
  quantileBreaks,
  rankOf,
  shareOf,
  summariseGroup,
} from "@/lib/atlas/context";

describe("atlas context: compared to where", () => {
  const values = new Map([
    ["a", 10],
    ["b", 20],
    ["c", 30],
    ["d", 40],
  ]);

  it("takes the median of an even and an odd group, and of none", () => {
    expect(median([1, 3, 2])).toBe(2);
    expect(median([1, 2, 3, 4])).toBe(2.5);
    expect(median([])).toBeNull();
  });

  it("summarises neighbours and counts those above and below, skipping missing values", () => {
    const summary = summariseGroup(["a", "c", "d", "missing"], values, 20);
    expect(summary.count).toBe(4);
    expect(summary.withValue).toBe(3);
    expect(summary.median).toBe(30);
    expect(summary.min).toBe(10);
    expect(summary.max).toBe(40);
    expect(summary.lower).toBe(1);
    expect(summary.higher).toBe(2);
  });

  it("ranks from the highest value and returns null for a unit without a value", () => {
    expect(rankOf("d", values)).toEqual({ rank: 1, total: 4 });
    expect(rankOf("a", values)).toEqual({ rank: 4, total: 4 });
    expect(rankOf("z", values)).toBeNull();
  });

  it("states differences in points for shares and as a ratio otherwise", () => {
    expect(describeDifference(18.2, 9.4, "percent")).toEqual({
      text: "8.8 points above",
      direction: "above",
    });
    expect(describeDifference(90, 100, "persons per km2").text).toBe("10% below");
    expect(describeDifference(300, 100, "persons per km2").text).toBe("3.0× as high");
    expect(describeDifference(5, 5, "percent").direction).toBe("equal");
  });

  it("gives a share of a total only when the total is positive", () => {
    expect(shareOf(25, 100)).toBe(25);
    expect(shareOf(25, 0)).toBeNull();
    expect(shareOf(25, null)).toBeNull();
  });

  it("builds ascending class breaks and assigns classes", () => {
    const breaks = quantileBreaks([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5);
    expect(breaks).toHaveLength(4);
    expect([...breaks].sort((x, y) => x - y)).toEqual(breaks);
    expect(classIndex(1, breaks)).toBe(0);
    expect(classIndex(10, breaks)).toBe(4);
    expect(quantileBreaks([7, 7, 7])).toEqual([]);
    expect(quantileBreaks([1, 2, 3])).toEqual([2, 3]);
  });

  it("builds diverging breaks that are symmetric around zero", () => {
    const breaks = divergingBreaks([-20, -5, 0, 4, 9, 15, 30]);
    expect(breaks).toHaveLength(4);
    expect(breaks[0]).toBe(-breaks[3]);
    expect(breaks[1]).toBe(-breaks[2]);
    expect(divergingBreaks([])).toEqual([]);
  });

  it("counts every value once in the histogram", () => {
    const result = histogram([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 5);
    expect(result.counts.reduce((sum, n) => sum + n, 0)).toBe(10);
    expect(result.min).toBe(0);
    expect(result.max).toBe(9);
  });
});
