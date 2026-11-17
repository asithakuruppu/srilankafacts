/** Types for the atlas bundle written by `slf atlas export` (pipeline/slf/atlas.py). */

export type LevelName = "country" | "province" | "district" | "ds" | "gn";

export const LEVELS: LevelName[] = ["country", "province", "district", "ds", "gn"];

export const LEVEL_SHORT: Record<LevelName, string> = {
  country: "Country",
  province: "Province",
  district: "District",
  ds: "DS division",
  gn: "GN division",
};

export const LEVEL_PLURAL: Record<LevelName, string> = {
  country: "Country",
  province: "Provinces",
  district: "Districts",
  ds: "DS divisions",
  gn: "GN divisions",
};

/** Plural level names for running text ("of 339 DS divisions"). */
export const LEVEL_PLURAL_TEXT: Record<LevelName, string> = {
  country: "country",
  province: "provinces",
  district: "districts",
  ds: "DS divisions",
  gn: "GN divisions",
};

export type Lens = "geography" | "profile" | "change" | "landscape";

export const LENSES: { id: Lens; label: string; hint: string }[] = [
  { id: "geography", label: "Geography", hint: "Where it is, and one number in context" },
  { id: "profile", label: "Profile", hint: "What a place is like, and places like it" },
  { id: "change", label: "Change", hint: "How places changed between censuses" },
  { id: "landscape", label: "Landscape", hint: "Terrain, land cover and physical features" },
];

/** Province, district or DS unit from units.json. */
export type Unit = {
  /** English name; null when the spine has none. */
  n: string | null;
  /** Level 0 to 3. */
  l: number;
  /** Parent id. */
  p: string | null;
  /** Label point [lon, lat]; null when the unit has no geometry in the spine. */
  c: [number, number] | null;
  /** Bounding box [west, south, east, north]. */
  b: [number, number, number, number] | null;
  /** Area in km² from the spine. */
  a: number | null;
};

export type GnUnit = { n: string | null; c: [number, number] | null; a: number | null };

export type Geometry =
  | { type: "Polygon"; coordinates: number[][][] }
  | { type: "MultiPolygon"; coordinates: number[][][][] }
  | { type: "LineString"; coordinates: number[][] }
  | { type: "MultiLineString"; coordinates: number[][][] };

export type Feature<P> = { type: "Feature"; properties: P; geometry: Geometry };
export type Collection<P> = { type: "FeatureCollection"; features: Feature<P>[] };

export type AreaProps = {
  id: string;
  gn?: string;
  ds: string;
  district: string;
  province: string;
  country: string;
};
export type OutlineProps = { id: string; level: number };
export type MeshProps = { rank: number };

export type DetailFile = {
  district: string;
  gn: Collection<AreaProps>;
  outlines: Collection<OutlineProps>;
  mesh: Collection<MeshProps>;
  units: Record<string, GnUnit>;
};

export type FineFile = { mesh: Collection<MeshProps>; outlines: Collection<OutlineProps> };

/** Neighbour pair: [id, 0 = shares a border | 1 = nearest unit without a shared border]. */
export type NeighbourRef = [string, 0 | 1];
export type AdjacencyLevel = Record<string, NeighbourRef[]>;
export type Adjacency = Partial<Record<"province" | "district" | "ds", AdjacencyLevel>>;

export type ProfileAxisMeta = {
  axis: number;
  variance_explained: number;
  draft_label: string;
  label_status: string;
  loadings: [string, number][];
};

/** [neighbour id, distance, alike [[indicator index, share]], different [[indicator index, share]]]. */
export type SimilarRow = [string, number, [number, number][], [number, number][]];

export type ProfileFile = {
  space_id: string;
  space_version: string;
  level: "ds";
  period: string;
  metric: "euclidean";
  note: string | null;
  axes: ProfileAxisMeta[];
  ids: string[];
  vectors: number[][];
  norm: number[];
  indicator_ids: string[];
  indicator_vectors: number[][];
  percentile: (number | null)[];
  top_indicators: string[][];
  similar: {
    k: number;
    indicators: string[];
    row_format: string[];
    places: Record<string, SimilarRow[]>;
  };
  /** [a, b, distance, percentile among bordering pairs, flagged]. */
  contrasts: [string, string, number, number, boolean][];
};

export type ChangeRow = {
  id: string;
  pop_2012: number | null;
  pop_2024: number | null;
  growth_pct: number | null;
  annual_rate_pct: number | null;
  change_type: string;
  comparison: "exact" | "approximate" | string;
  method: string;
  reason: string | null;
};

export type ChangeFile = {
  status: string;
  note: string;
  ds: ChangeRow[];
  /** Totals for districts, provinces and the country: sums of DS rows. Absent in older bundles. */
  areas?: {
    id: string;
    pop_2012: number;
    pop_2024: number;
    growth_pct: number;
    ds_rows: number;
    approximate: number;
  }[];
  areas_note?: string;
  /** DS rows that have no map unit (named, with their figures only in the totals). */
  not_mapped?: string[];
  national: {
    year: number;
    population: number | null;
    unit: string;
    source: string;
    page: string | null;
    comparison_to_2024: string;
  }[];
  sources: {
    id: string;
    url: string | null;
    sha256: string | null;
    retrieved_at: string | null;
    licence_note: string | null;
  }[];
};

export type ClusterClass = "high_high" | "low_low" | "high_low" | "low_high";
/** `small`: id → [denominator, empirical Bayes smoothed value] for units under the D-026 threshold. */
export type ClusterFile = Partial<
  Record<
    "district" | "ds" | "gn",
    Partial<Record<ClusterClass, string[]>> & { small?: Record<string, [number | null, number | null]> }
  >
>;

export type AtlasMeta = {
  profile: boolean;
  change: boolean;
  clusters: number;
  detail_tolerance_m: number | null;
  overview_tolerance_m: number | null;
};

export type AtlasIndicator = {
  id: string;
  name: string;
  short: string;
  unit: string;
  decimals: number;
  measureType: string;
  higherIs: string;
  definition: string;
  levels: string[];
  group: string;
};

export function levelOfId(id: string, units: Record<string, Unit>): LevelName {
  const unit = units[id];
  if (unit) {
    return LEVELS[unit.l] ?? "gn";
  }
  return "gn";
}
