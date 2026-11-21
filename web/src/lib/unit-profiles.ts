import fs from "node:fs";
import path from "node:path";

/** Composed (non-nesting) schemes with GN-based profiles, and the file name each build writes. */
export const UNIT_SCHEMES = {
  la: { title: "Local authorities", file: "units-la.json" },
  moh: { title: "MOH areas", file: "units-health.json" },
} as const;
export type UnitScheme = keyof typeof UNIT_SCHEMES;

export type UnitProfile = {
  id: string;
  name: string | null;
  gn_members: number;
  gn_with_census: number;
  counts: Record<string, number | null>;
  rates: Record<string, number | null>;
  iou_shape_vs_gn_union: number | null;
  share_in_own_dcs_la_type: number | null;
  flags: string[];
};
export type UnitProfileFile = {
  scheme: string;
  publishable: boolean;
  source: string;
  support: string;
  attribution?: string | null;
  notice?: string | null;
  spine_gns_without_unit?: number | null;
  units: UnitProfile[];
};

export const UNAVAILABLE_REASON =
  "This build has no publishable membership list for this scheme: no official GN list per area is held, " +
  "and a community list is shown only in builds that carry its preview notice (D-057).";

export function isUnitScheme(value: string): value is UnitScheme {
  return value in UNIT_SCHEMES;
}

/** Only a parsed file that says `publishable: true` is ever shown; anything else is "unavailable". */
export function parseUnitProfiles(text: string): UnitProfileFile | null {
  let doc: UnitProfileFile;
  try {
    doc = JSON.parse(text) as UnitProfileFile;
  } catch {
    return null;
  }
  if (doc.publishable !== true || !Array.isArray(doc.units)) {
    return null;
  }
  return doc;
}

export function getUnitProfiles(scheme: UnitScheme): UnitProfileFile | null {
  const file = path.resolve(process.cwd(), "public/release/atlas", UNIT_SCHEMES[scheme].file);
  if (!fs.existsSync(file)) {
    return null;
  }
  return parseUnitProfiles(fs.readFileSync(file, "utf8"));
}

export const FLAG_TEXT: Record<string, string> = {
  no_census_gn: "no census data for any of its GN divisions",
  some_gn_without_census: "some GN divisions have no census value",
  shape_disagrees_with_gn_union: "its own boundary differs from the union of its GN divisions",
  dcs_local_authority_type_mismatch:
    "the census places much of its population under a different local authority type",
};
