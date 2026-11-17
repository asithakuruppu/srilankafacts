import { describe, expect, it } from "vitest";

import {
  distance,
  distancesFrom,
  explainPair,
  indexProfile,
  nearest,
  percentileAmong,
  pipelineReasons,
} from "@/lib/atlas/profile";
import type { ProfileFile } from "@/lib/atlas/types";

const file: ProfileFile = {
  space_id: "profile",
  space_version: "test",
  level: "ds",
  period: "2024",
  metric: "euclidean",
  note: null,
  axes: [
    { axis: 1, variance_explained: 0.6, draft_label: "axis one", label_status: "draft", loadings: [] },
    { axis: 2, variance_explained: 0.4, draft_label: "axis two", label_status: "draft", loadings: [] },
  ],
  ids: ["A", "B", "C", "D"],
  vectors: [
    [0, 0],
    [3, 4],
    [1, 0],
    [0, 10],
  ],
  norm: [0, 5, 1, 10],
  indicator_ids: [],
  indicator_vectors: [],
  percentile: [0, 50, 25, 100],
  top_indicators: [[], [], [], []],
  similar: {
    k: 2,
    indicators: ["population_density", "sex_ratio"],
    row_format: [],
    places: { A: [["C", 1, [[1, 0.1]], [[0, 0.9]]]] },
  },
  contrasts: [],
};

describe("atlas profile space", () => {
  const index = indexProfile(file);

  it("measures straight-line distance on all axes", () => {
    expect(distance([0, 0], [3, 4])).toBe(5);
    const all = distancesFrom(index, "A");
    expect(all?.get("B")).toBe(5);
    expect(all?.has("A")).toBe(false);
    expect(distancesFrom(index, "missing")).toBeNull();
  });

  it("returns the nearest places in order, never the place itself", () => {
    expect(nearest(index, "A", 2).map((item) => item.id)).toEqual(["C", "B"]);
    expect(nearest(index, "missing", 2)).toEqual([]);
  });

  it("splits a distance into axis shares that sum to one", () => {
    const pair = explainPair(index, "A", "B");
    expect(pair?.distance).toBe(5);
    expect(pair?.axes.map((axis) => axis.share)).toEqual([9 / 25, 16 / 25]);
    expect(pair?.axes.reduce((sum, axis) => sum + axis.share, 0)).toBeCloseTo(1);
    expect(explainPair(index, "A", "missing")).toBeNull();
  });

  it("gives zero shares for two places at the same point", () => {
    expect(explainPair(index, "A", "A")?.axes.every((axis) => axis.share === 0)).toBe(true);
  });

  it("places a distance among the others", () => {
    expect(percentileAmong(5, [1, 5, 10])).toBeCloseTo(33.33, 1);
    expect(percentileAmong(5, [])).toBe(0);
  });

  it("names the pipeline's reasons only for precomputed pairs", () => {
    expect(pipelineReasons(index, "A", "C")).toEqual({
      alike: [{ indicator: "sex_ratio", share: 0.1 }],
      different: [{ indicator: "population_density", share: 0.9 }],
    });
    expect(pipelineReasons(index, "A", "D")).toBeNull();
  });
});
