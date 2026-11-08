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
};

export type LatestRelease = {
  release: string;
  version: string;
  status: ReleaseStatus;
  publishable: boolean;
  citation: string;
  geography_count: number;
  observation_count: number;
  datasets: DatasetRights[];
};

export type IndicatorMeta = {
  id: string;
  name: string;
  short_name: string | null;
  definition: string;
  measure_type: string;
  unit: string;
  higher_is: string;
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
