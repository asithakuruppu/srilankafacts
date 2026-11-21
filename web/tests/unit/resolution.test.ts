import { describe, expect, it } from "vitest";

import { filterRows, formatMetres, shownAs } from "@/lib/atlas/resolution";
import type { ResolutionEntry } from "@/lib/atlas/types";

const base: ResolutionEntry = {
  dataset_id: "x", title: "X", status: "active", support: "grid", level: null,
  native_resolution_text: null, native_resolution_m: null, information_unit: null,
  information_count: null, tier: "unknown", shown_as: "gn_zonal", derived_by: null,
  indicators: 1, reference_period: null, landing_page: null, source_name: null,
  rights_status: "open", use: "any", attribution: null,
};

describe("resolution helpers", () => {
  it("formats metres and never invents a size", () => {
    expect(formatMetres({ ...base, native_resolution_m: 30 })).toBe("30 m");
    expect(formatMetres({ ...base, native_resolution_m: 1000 })).toBe("1 km");
    expect(formatMetres({ ...base, native_resolution_text: "0.05 degree" })).toBe("0.05 degree");
    expect(formatMetres(base)).toBe("not recorded");
  });

  it("filters finer, held and gn", () => {
    const rows = [
      { ...base, dataset_id: "a", tier: "finer_than_gn" as const },
      { ...base, dataset_id: "b", tier: "finer_than_gn" as const, shown_as: "points" },
      { ...base, dataset_id: "c", tier: "gn" as const, shown_as: "area_gn" },
    ];
    expect(filterRows(rows, "finer").map((r) => r.dataset_id)).toEqual(["a", "b"]);
    expect(filterRows(rows, "held").map((r) => r.dataset_id)).toEqual(["a"]);
    expect(filterRows(rows, "gn").map((r) => r.dataset_id)).toEqual(["c"]);
    expect(shownAs(rows[2])).toBe("Area units (gn)");
  });
});
