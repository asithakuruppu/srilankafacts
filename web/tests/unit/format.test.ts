import { describe, expect, it } from "vitest";

import {
  decimalsFor,
  formatBytes,
  formatDelta,
  formatNumber,
  formatValue,
} from "@/lib/format";

describe("formatValue", () => {
  it("formats counts with thousands separators and no decimals", () => {
    expect(formatValue(21781800, "persons")).toBe("21,781,800");
    expect(formatValue(6030541, "housing_units")).toBe("6,030,541 units");
  });

  it("formats rates with the unit's precision and suffix", () => {
    expect(formatValue(341.25, "persons per km2")).toBe("341.3 per km²");
    expect(formatValue(12.34, "percent")).toBe("12.3%");
    expect(formatValue(3.61, "persons per housing unit")).toBe("3.61 per occupied unit");
    expect(formatValue(94.5, "males per 100 females")).toBe(
      "94.5 males per 100 females",
    );
  });

  it("never prints a missing value as zero", () => {
    expect(formatValue(null, "percent")).toBe("Not available");
    expect(formatValue(undefined, "persons")).toBe("Not available");
    expect(formatValue(Number.NaN, "persons")).toBe("Not available");
  });

  it("uses the indicator's own precision when given", () => {
    expect(formatValue(12.345, "percent", 2)).toBe("12.35%");
    expect(decimalsFor("persons")).toBe(0);
  });
});

describe("formatDelta", () => {
  it("uses percentage points for shares and percent for counts", () => {
    expect(formatDelta(12.5, "percent", 10)).toBe("+2.5 pp vs national");
    expect(formatDelta(8, "percent", 10)).toBe("−2.0 pp vs national");
    expect(formatDelta(110, "persons", 100)).toBe("+10.0% vs national");
    expect(formatDelta(100, "persons", 0)).toBe("no national base");
  });
});

describe("other formatters", () => {
  it("formats numbers and file sizes", () => {
    expect(formatNumber(14008)).toBe("14,008");
    expect(formatBytes(1024)).toBe("1 KB");
    expect(formatBytes(1822216)).toBe("1.7 MB");
  });
});
