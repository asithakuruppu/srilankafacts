import { describe, expect, it } from "vitest";

import { isUnitScheme, parseUnitProfiles } from "./unit-profiles";

describe("unit profiles gate", () => {
  it("never renders an internal file", () => {
    expect(parseUnitProfiles(JSON.stringify({ publishable: false, units: [] }))).toBeNull();
    expect(parseUnitProfiles("not json")).toBeNull();
    expect(parseUnitProfiles(JSON.stringify({ units: [] }))).toBeNull();
  });
  it("accepts a publishable file", () => {
    expect(parseUnitProfiles(JSON.stringify({ publishable: true, units: [] }))).not.toBeNull();
  });
  it("knows its schemes", () => {
    expect(isUnitScheme("la") && isUnitScheme("moh")).toBe(true);
    expect(isUnitScheme("ed")).toBe(false);
  });
});
