export type BoundaryFeature = {
  type: "Feature";
  properties: {
    geography_id: string;
    name_en: string | null;
    level_name: string;
    parent_id: string | null;
  };
  geometry: unknown;
};

export type BoundaryCollection = {
  type: "FeatureCollection";
  features: BoundaryFeature[];
};

export type ValueRow = {
  geography_id: string;
  value: number | null;
  unit: string;
  value_status?: string;
};

export type AreaRow = {
  id: string;
  name: string;
  levelName: string;
  parentId: string | null;
  value: number | null;
  unit: string;
  status: string;
};

export type AreaDataset = {
  boundary: BoundaryCollection;
  values: Map<string, ValueRow>;
  rows: AreaRow[];
};

export function levelFiles(levelName: string): string[] {
  return levelName === "ds" ? ["ds", "ds-provisional"] : [levelName];
}

export async function fetchAreaDataset(
  indicatorId: string,
  levelName: string,
  boundaryLevel: number,
  signal?: AbortSignal,
): Promise<AreaDataset> {
  const [boundaryResponse, ...valueResponses] = await Promise.all([
    fetch(`/release/boundaries/admin${boundaryLevel}.geojson`, { signal }),
    ...levelFiles(levelName).map((level) =>
      fetch(`/api/v1/indicators/${indicatorId}/${level}.json`, { signal }),
    ),
  ]);
  if (!boundaryResponse.ok) {
    throw new Error(`Boundary request failed (${boundaryResponse.status}).`);
  }
  const boundary = (await boundaryResponse.json()) as BoundaryCollection;
  const values = new Map<string, ValueRow>();
  for (const response of valueResponses) {
    if (!response.ok) {
      continue;
    }
    const payload = (await response.json()) as { values: ValueRow[] };
    for (const row of payload.values) {
      values.set(row.geography_id, row);
    }
  }
  const rows: AreaRow[] = boundary.features.map((feature) => {
    const row = values.get(feature.properties.geography_id);
    return {
      id: feature.properties.geography_id,
      name: feature.properties.name_en ?? feature.properties.geography_id,
      levelName: feature.properties.level_name,
      parentId: feature.properties.parent_id,
      value: row?.value ?? null,
      unit: row?.unit ?? "",
      status: row?.value_status ?? "no_data",
    };
  });
  return { boundary, values, rows };
}
