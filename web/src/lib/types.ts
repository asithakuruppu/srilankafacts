export type ReleaseStatus = "preview" | "public" | string;

export type DatasetRights = {
  dataset_id: string;
  title: string;
  source_id: string;
  source_name: string | null;
  source_homepage: string | null;
  rights_status: string;
  licence: string | null;
  attribution: string | null;
  rights_evidence: string[];
  /** Added in v2026.11.5 releases; absent in older ones. */
  use?: string;
  notice?: string | null;
  publication_decision?: string | null;
};

/** A lead decision (for example D-030) under which a dataset is published. Not a licence. */
export type ReleaseNotice = {
  dataset_id: string;
  use: string;
  attribution: string | null;
  notice: string | null;
  decision: string | null;
};

export type LatestRelease = {
  release: string;
  version: string;
  status: ReleaseStatus;
  publishable: boolean;
  /** "non_commercial" when any dataset may only be used non-commercially. */
  use?: string;
  notices?: ReleaseNotice[];
  citation: string;
  geography_count: number;
  observation_count: number;
  datasets: DatasetRights[];
};

export type IndicatorMeta = {
  id: string;
  name: string;
  short_name: string | null;
  /** Catalogue topic, for example ["housing", "water"]; absent in releases before v2026.11.10-preview.2. */
  topic?: string[];
  definition: string;
  measure_type: string;
  unit: string;
  higher_is: string;
  /**
   * "downloads_only": values are in the observation downloads, not in place or level files.
   * "places_only": in place files only; no level files, indicator pages or rankings (D-033).
   */
  distribution?: "api" | "downloads_only" | "places_only";
  decimals: number;
  levels: string[];
  period: string[];
  value_count: number;
};

export type IndicatorList = {
  citation: string;
  release: string;
  publishable: boolean;
  indicators: IndicatorMeta[];
};

export type IndicatorValue = {
  geography_id: string;
  period: string;
  unit: string;
  value: number | null;
  value_status: string;
};

export type IndicatorLevel = {
  citation: string;
  indicator_id: string;
  level: string;
  publishable: boolean;
  release: string;
  values: IndicatorValue[];
};

export type Geography = {
  geography_id: string;
  level: number;
  level_name: string;
  name_en: string | null;
  name_si: string | null;
  name_ta: string | null;
  parent_id: string | null;
  status: string;
};

export type GeographyList = {
  citation: string;
  scheme: string;
  release: string;
  publishable: boolean;
  geographies: Geography[];
};

export type Observation = {
  claim_id: string;
  dataset_id: string;
  indicator_id: string;
  information_footprint_ref: string | null;
  period: string;
  snapshot_sha256: string;
  source_locator: string;
  support_type: string;
  time_end: string;
  time_start: string;
  unit: string;
  value: number | null;
  value_status: string;
  verification: string;
};

export type Place = {
  citation: string;
  release: string;
  publishable: boolean;
  geography: Geography;
  datasets: DatasetRights[];
  values: Observation[];
  profile?: PlaceProfile;
  source_comparisons?: SourceComparison[];
};

export type DataPackageResource = {
  name: string;
  path: string;
  bytes: number;
  hash: string;
};

export type DataPackage = {
  name: string;
  title: string;
  version: string;
  access: string;
  publishable: boolean;
  licenses: { name: string }[];
  sources: { dataset: string; title: string; path: string }[];
  resources: DataPackageResource[];
};

export type ProfileAxis = {
  axis: number;
  draft_label: string;
  label_status: string;
  score: number;
  variance_explained: number;
};

export type SimilarPlace = {
  geography_id: string;
  name_en: string | null;
  distance: number;
  alike: string[];
  different: string[];
};

/** Profile-space block (D-031). DS places carry `similar`; GN places point to their DS. */
export type PlaceProfile = {
  space_id: string;
  space_version: string;
  period: string;
  level: "ds" | "gn";
  note: string;
  axes: ProfileAxis[];
  distance_from_centre: number;
  percentile: number;
  unusual_indicators: string[];
  similar: SimilarPlace[] | null;
  similar_note?: string;
  similar_via?: string | null;
};

export type Correction = {
  id: string;
  found: string;
  fixed: string | null;
  scope: "private_preview" | "public";
  affected_releases: string[];
  fixed_in: string | null;
  geographies: string[];
  indicators: string | string[];
  values_changed: number;
  what_was_wrong: string;
  what_changed: string;
  cause: string;
  evidence: string[];
  approved_by: string | null;
};

export type CorrectionsLog = { release: string; entries: Correction[] };

export type SourceClaim = {
  source_id: string;
  label: string;
  reference_date: string;
  value: number | null;
  locator: string;
  preferred: boolean;
};

/** One indicator compared across publishable sources for a place (D-019). */
export type SourceComparison = {
  geography_id: string;
  indicator_id: string;
  label: string;
  claims: SourceClaim[];
  n_sources: number;
  spread: number | null;
  relative_spread: number | null;
  agree: boolean;
  preferred_reason: string;
  note: string;
};
