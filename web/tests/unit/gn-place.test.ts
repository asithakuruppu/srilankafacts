import { describe, expect, it } from "vitest";

import { gnIdFrom, siblingRank } from "@/components/gn-place";
import type { HierarchyRow } from "@/lib/hierarchy";
import type { Place } from "@/lib/types";

describe("gnIdFrom", () => {
  it("reads a GN p-code from the path or the id parameter", () => {
    expect(gnIdFrom("/place/LK1103005", "")).toBe("LK1103005");
    expect(gnIdFrom("/place/LK1103005/", "")).toBe("LK1103005");
    expect(gnIdFrom("/place/gn", "?id=LK1103005")).toBe("LK1103005");
  });

  it("refuses ids that are not GN p-codes", () => {
    expect(gnIdFrom("/place/LK1103", "")).toBeNull();
    expect(gnIdFrom("/place/LK99999999999", "")).toBeNull();
    expect(gnIdFrom("/place/gn", "?id=../secret")).toBeNull();
  });
});

describe("siblingRank", () => {
  const place = {
    geography: { geography_id: "LK1103005", parent_id: "LK1103" },
    values: [{ indicator_id: "population_total", value: 50 }],
  } as unknown as Place;
  const rows: HierarchyRow[] = [
    ["LK1103", "DS", "LK11", 3],
    ["LK1103005", "A", "LK1103", 4],
    ["LK1103010", "B", "LK1103", 4],
    ["LK1104001", "C", "LK1104", 4],
  ];

  it("ranks among GN divisions of the same DS division only", () => {
    const level = {
      values: [
        { geography_id: "LK1103005", value: 50 },
        { geography_id: "LK1103010", value: 80 },
        { geography_id: "LK1104001", value: 999 },
      ],
    };
    expect(siblingRank(place, rows, level, "population_total")).toBe("2 of 2 in parent");
  });
});
