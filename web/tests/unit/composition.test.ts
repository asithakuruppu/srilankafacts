import { describe, expect, it } from "vitest";

import { pieSlices, shareFamilies } from "@/lib/composition";

const share = (id: string, name: string) => ({ id, name, measureType: "share" });

describe("share families", () => {
  const families = shareFamilies([
    share("w_a", "Share of households by main source of drinking water: Spring"),
    share("w_b", "Share of households by main source of drinking water: Rain water"),
    share("lonely", "Share of things by kind: Only one"),
    share("population_age_0_4_share", "Share of population aged 0–4"),
    share("population_age_5_9_share", "Share of population aged 5–9"),
    share("population_age_0_14_share", "Share of population aged 0–14"),
    { id: "x", name: "Total: count", measureType: "count" },
  ]);
  it("groups by the name before the colon and drops single-member groups", () => {
    expect(families.get("households by main source of drinking water")?.members.map((m) => m.label)).toEqual([
      "Spring",
      "Rain water",
    ]);
    expect(families.has("things by kind")).toBe(false);
  });
  it("puts 5-year bands together and leaves out overlapping broad groups", () => {
    expect(families.get("age5")?.members.map((m) => m.id)).toEqual([
      "population_age_0_4_share",
      "population_age_5_9_share",
    ]);
  });
});

describe("pieSlices", () => {
  const parts = Array.from({ length: 12 }, (_, i) => ({ id: `p${i}`, label: `P${i}`, value: 12 - i }));
  it("merges the smallest into one slice and keeps the total", () => {
    const slices = pieSlices(parts, null);
    expect(slices).toHaveLength(8);
    expect(slices.at(-1)).toMatchObject({ id: null, label: "Smaller categories" });
    expect(slices.reduce((s, x) => s + x.value, 0)).toBe(78);
  });
  it("keeps the selected category apart", () => {
    expect(pieSlices(parts, "p11").some((s) => s.id === "p11")).toBe(true);
  });
  it("drops zero values and does not merge small sets", () => {
    expect(pieSlices([{ id: "a", label: "A", value: 0 }, { id: "b", label: "B", value: 5 }], null)).toHaveLength(1);
  });
});
