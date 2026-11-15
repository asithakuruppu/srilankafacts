import { describe, expect, it } from "vitest";

import {
  type HierarchyRow,
  buildHierarchy,
  childLevelName,
  childrenOf,
  histogramBins,
  pathTo,
  rankOf,
} from "@/lib/hierarchy";

const rows: HierarchyRow[] = [
  ["LK", "Sri Lanka", null, 0],
  ["LK1", "Western", "LK", 1],
  ["LK11", "Colombo", "LK1", 2],
  ["LK1103", "Thimbirigasyaya", "LK11", 3],
  ["LK1103005", "Alpha", "LK1103", 4],
  ["LK1103001", "Beta", "LK1103", 4],
];

describe("hierarchy", () => {
  const h = buildHierarchy(rows);
  it("lists children sorted by name", () => {
    expect(childrenOf(h, "LK1103").map((n) => n.name)).toEqual(["Alpha", "Beta"]);
  });
  it("builds the path from the country down", () => {
    expect(pathTo(h, "LK1103005").map((n) => n.id)).toEqual(["LK", "LK1", "LK11", "LK1103", "LK1103005"]);
  });
  it("maps a level to its child level", () => {
    expect(childLevelName(0)).toBe("province");
    expect(childLevelName(3)).toBe("gn");
    expect(childLevelName(4)).toBeNull();
  });
  it("ranks with ties sharing a rank", () => {
    const values = [
      { id: "a", value: 5 },
      { id: "b", value: 9 },
      { id: "c", value: 5 },
    ];
    expect(rankOf(values, "b")).toBe(1);
    expect(rankOf(values, "c")).toBe(2);
    expect(rankOf(values, "zz")).toBeNull();
  });
  it("bins values and keeps every value", () => {
    const bins = histogramBins([1, 2, 3, 4, 10], 3);
    expect(bins.reduce((sum, b) => sum + b.count, 0)).toBe(5);
    expect(histogramBins([])).toEqual([]);
  });
});
