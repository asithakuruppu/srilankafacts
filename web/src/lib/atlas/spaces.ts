/**
 * Vector spaces v2 in the browser (built by `slf profile spaces`, pipeline/slf/spaces.py).
 *
 * The browser only measures: Euclidean distance over a space's axes. Because a squared distance
 * is a sum over axes, each axis's share is exact. In the composite space, each axis score is a
 * sum of block contributions; the reader's weights scale those contributions, so all weights 1
 * reproduce profile v0.3 exactly. Distances never come from screen positions (rule 13).
 */

export type TypologyFile = {
  space_id: string;
  space_version: string;
  base: { space_id: string; space_version: string; level: string };
  method: string;
  note: string;
  k: number;
  choices: { k: number; silhouette: number; stability_ari: number; inertia: number }[];
  types: {
    type: number;
    draft_name: string;
    label_status: string;
    size: number;
    centre: number[];
    inputs_sd: [string, number][];
    typical: string[];
    mean_agreement: number;
  }[];
  ids: string[];
  type_of: number[];
  agreement: number[];
};

export type CompositeFile = {
  space_id: string;
  space_version: string;
  base: { space_id: string; space_version: string; level: string };
  note: string;
  blocks: { id: string; label: string; inputs: number }[];
  axes: { axis: number; draft_label: string; label_status: string }[];
  ids: string[];
  /** [place][block][axis] */
  contrib: number[][][];
};

export type TrajectoryFile = {
  space_id: string;
  space_version: string;
  status: string;
  note: string;
  axes: { id: string; label: string; mean: number; sd: number }[];
  ids: string[];
  vectors: number[][];
  raw: number[][];
  comparison: string[];
  excluded: { id: string; reason: string }[];
  similar: Record<string, [string, number][]>;
};

/** A space reduced to what distances need: ids and one vector per id. */
export type PointSpace = { ids: string[]; vectors: number[][]; row: Map<string, number> };

export function pointSpace(ids: string[], vectors: number[][]): PointSpace {
  return { ids, vectors, row: new Map(ids.map((id, i) => [id, i])) };
}

/** Axis scores for given block weights: Σ_b w_b × contribution[b][axis]. */
export function compositeVectors(file: CompositeFile, weights: number[]): number[][] {
  return file.contrib.map((blocks) => {
    const axes = blocks[0]?.length ?? 0;
    const out = new Array<number>(axes).fill(0);
    for (let b = 0; b < blocks.length; b += 1) {
      const w = weights[b] ?? 1;
      for (let a = 0; a < axes; a += 1) {
        out[a] += w * blocks[b][a];
      }
    }
    return out;
  });
}

function squared(a: number[], b: number[]): number {
  let sum = 0;
  for (let i = 0; i < a.length; i += 1) {
    const d = a[i] - b[i];
    sum += d * d;
  }
  return sum;
}

/** k nearest by Euclidean distance; ties broken by id (as the pipeline does). */
export function nearestIn(
  space: PointSpace,
  id: string,
  k: number,
): { id: string; distance: number }[] {
  const row = space.row.get(id);
  if (row === undefined) {
    return [];
  }
  const origin = space.vectors[row];
  const all: { id: string; distance: number }[] = [];
  space.ids.forEach((other, i) => {
    if (i !== row) {
      all.push({ id: other, distance: Math.sqrt(squared(origin, space.vectors[i])) });
    }
  });
  all.sort((a, b) => a.distance - b.distance || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
  return all.slice(0, k);
}

/** Distance from one place to every other place. */
export function distancesIn(space: PointSpace, id: string): Map<string, number> {
  const row = space.row.get(id);
  const out = new Map<string, number>();
  if (row === undefined) {
    return out;
  }
  space.ids.forEach((other, i) => {
    if (i !== row) {
      out.set(other, Math.sqrt(squared(space.vectors[row], space.vectors[i])));
    }
  });
  return out;
}

/** Exact share of the squared distance per axis (sums to 1). */
export function axisShares(space: PointSpace, a: string, b: string): number[] | null {
  const ra = space.row.get(a);
  const rb = space.row.get(b);
  if (ra === undefined || rb === undefined) {
    return null;
  }
  const parts = space.vectors[ra].map((v, i) => (v - space.vectors[rb][i]) ** 2);
  const total = parts.reduce((s, v) => s + v, 0);
  return parts.map((v) => (total === 0 ? 0 : v / total));
}

/** Exact share of the squared distance per block, axis by axis, in the composite space. */
export function blockShares(
  file: CompositeFile,
  weights: number[],
  a: string,
  b: string,
): { axis: number[]; block: number[] } | null {
  const ra = file.ids.indexOf(a);
  const rb = file.ids.indexOf(b);
  if (ra < 0 || rb < 0) {
    return null;
  }
  const axes = file.axes.length;
  const blocks = file.blocks.length;
  const axisPart = new Array<number>(axes).fill(0);
  const blockPart = new Array<number>(blocks).fill(0);
  for (let x = 0; x < axes; x += 1) {
    const diffs = file.blocks.map(
      (_, k) => (weights[k] ?? 1) * (file.contrib[ra][k][x] - file.contrib[rb][k][x]),
    );
    const d = diffs.reduce((s, v) => s + v, 0);
    axisPart[x] = d * d;
    // d² = Σ_k diff_k × d: each block's (signed) part of this axis's squared difference.
    diffs.forEach((diff, k) => {
      blockPart[k] += diff * d;
    });
  }
  const total = axisPart.reduce((s, v) => s + v, 0);
  return {
    axis: axisPart.map((v) => (total === 0 ? 0 : v / total)),
    block: blockPart.map((v) => (total === 0 ? 0 : v / total)),
  };
}

/** The four preset questions of the explorer (W08). */
export type Question = "like" | "near_unlike" | "far_like" | "unusual";

/**
 * Bordering places that differ most ("near here, unlike here") or distant places that are alike
 * ("far away, like here"), using the geographic neighbour list and label points.
 */
export function farAlike(
  space: PointSpace,
  id: string,
  points: Map<string, [number, number]>,
  minKm: number,
  k: number,
): { id: string; distance: number; km: number }[] {
  const origin = points.get(id);
  if (!origin) {
    return [];
  }
  return nearestIn(space, id, space.ids.length)
    .map((item) => ({ ...item, km: haversineKm(origin, points.get(item.id) ?? origin) }))
    .filter((item) => item.km >= minKm)
    .slice(0, k);
}

export function haversineKm(a: [number, number], b: [number, number]): number {
  const rad = Math.PI / 180;
  const dLat = (b[1] - a[1]) * rad;
  const dLon = (b[0] - a[0]) * rad;
  const h =
    Math.sin(dLat / 2) ** 2 + Math.cos(a[1] * rad) * Math.cos(b[1] * rad) * Math.sin(dLon / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h));
}
