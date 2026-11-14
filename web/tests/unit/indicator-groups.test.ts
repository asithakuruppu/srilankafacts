import { describe, expect, it } from "vitest";

import { groupIndicators } from "@/lib/indicator-groups";
import type { IndicatorMeta } from "@/lib/types";

function meta(id: string, topic?: string[]): IndicatorMeta {
  return {
    id,
    name: id,
    short_name: null,
    topic,
    definition: "",
    measure_type: "share",
    unit: "percent",
    higher_is: "neutral",
    decimals: 1,
    levels: ["district"],
    period: ["2024"],
    value_count: 1,
  };
}

describe("groupIndicators", () => {
  it("groups by catalogue topic in reading order and drops empty groups", () => {
    const groups = groupIndicators([
      meta("housing_roof_tile_share", ["housing", "roof"]),
      meta("population_total", ["population"]),
      meta("households_water_pipe_share", ["housing", "water"]),
      meta("housing_wall_brick_share", ["housing", "wall"]),
    ]);
    expect(groups.map((g) => [g.label, g.indicators.map((i) => i.id)])).toEqual([
      ["Population, sex and density", ["population_total"]],
      ["Drinking water", ["households_water_pipe_share"]],
      [
        "Housing structure and materials (DS divisions and larger)",
        ["housing_roof_tile_share", "housing_wall_brick_share"],
      ],
    ]);
  });

  it("puts indicators without a known topic under Other (older releases have no topic)", () => {
    const groups = groupIndicators([meta("a"), meta("b", ["transport"])]);
    expect(groups).toEqual([{ label: "Other", indicators: [meta("a"), meta("b", ["transport"])] }]);
  });
});
