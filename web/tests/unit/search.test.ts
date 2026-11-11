import { describe, expect, it } from "vitest";

import { normalise, searchPlaces, type SearchEntry } from "@/lib/search";

const entries: SearchEntry[] = [
  { i: "LK", n: "Sri Lanka", s: "ශ්‍රී ලංකා", t: "இலங்கை", l: 0 },
  { i: "LK11", n: "Colombo", s: "කොළඹ", t: "கொழும்பு", l: 2, p: "LK1", pn: "Western" },
  { i: "LK1103", n: "Colombo", s: "කොළඹ", t: "கொழும்பு", l: 3, p: "LK11", pn: "Colombo" },
  { i: "LK1103005", n: "Fort", s: "කොටුව", t: null, l: 4, p: "LK1103", pn: "Colombo" },
  { i: "LK-ADM3-P0001", n: "Kalmunai North Sub", l: 3, p: "LK52", pn: "Ampara" },
];

describe("normalise", () => {
  it("folds common romanisation variants", () => {
    expect(normalise("Colombo")).toBe("colombo");
    expect(normalise("  JAFFNA ")).toBe("jafna");
    expect(normalise("Anuradhapura")).toBe("anuradapura");
    expect(normalise("Nuwara-Eliya")).toBe("nuvara eliya");
  });

  it("keeps Sinhala and Tamil script", () => {
    expect(normalise("කොළඹ")).toBe("කොළඹ");
    expect(normalise("கொழும்பு")).toBe("கொழும்பு");
  });
});

describe("searchPlaces", () => {
  it("ranks an exact district above its DS division", () => {
    const results = searchPlaces(entries, "colombo");
    expect(results[0].i).toBe("LK11");
    expect(results.map((result) => result.i)).toContain("LK1103");
  });

  it("matches a Sinhala name", () => {
    const results = searchPlaces(entries, "කොළඹ");
    expect(results.map((result) => result.i)).toEqual(
      expect.arrayContaining(["LK11", "LK1103"]),
    );
  });

  it("matches a Tamil name and a partial English word", () => {
    expect(searchPlaces(entries, "கொழும்பு")[0].i).toBe("LK11");
    expect(searchPlaces(entries, "kalmunai")[0].i).toBe("LK-ADM3-P0001");
    expect(searchPlaces(entries, "fort")[0].i).toBe("LK1103005");
  });

  it("returns nothing for an empty or unknown query", () => {
    expect(searchPlaces(entries, "   ")).toEqual([]);
    expect(searchPlaces(entries, "zzzz")).toEqual([]);
  });
});
