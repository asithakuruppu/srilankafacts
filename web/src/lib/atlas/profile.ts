/**
 * Profile-space operations in the browser (vector-space-model.md §5–6, D-016).
 *
 * The space is built by the pipeline (PCA on standardised, block-weighted census inputs).
 * The browser only measures in it: Euclidean distance over the retained axes. Because the
 * squared distance is a sum over axes, each axis's share of a distance is exact, not an
 * approximation. A distance is a similarity statement, never a fact or a ranking (rule 13).
 */

import type { ProfileFile } from "@/lib/atlas/types";

export type ProfileIndex = {
  file: ProfileFile;
  row: Map<string, number>;
};

export function indexProfile(file: ProfileFile): ProfileIndex {
  return { file, row: new Map(file.ids.map((id, i) => [id, i])) };
}

export function distance(a: number[], b: number[]): number {
  let sum = 0;
  for (let i = 0; i < a.length; i += 1) {
    const delta = a[i] - b[i];
    sum += delta * delta;
  }
  return Math.sqrt(sum);
}

/** Distance from one place to every place in the space (brute force; 339 × 5 numbers). */
export function distancesFrom(index: ProfileIndex, id: string): Map<string, number> | null {
  const row = index.row.get(id);
  if (row === undefined) {
    return null;
  }
  const origin = index.file.vectors[row];
  const result = new Map<string, number>();
  index.file.ids.forEach((other, i) => {
    if (i !== row) {
      result.set(other, distance(origin, index.file.vectors[i]));
    }
  });
  return result;
}

export function nearest(
  index: ProfileIndex,
  id: string,
  k: number,
): { id: string; distance: number }[] {
  const all = distancesFrom(index, id);
  if (!all) {
    return [];
  }
  return [...all.entries()]
    .map(([other, d]) => ({ id: other, distance: d }))
    .sort((a, b) => a.distance - b.distance || a.id.localeCompare(b.id))
    .slice(0, k);
}

export type AxisContribution = {
  axis: number;
  label: string;
  labelStatus: string;
  /** Position of each place on this axis. */
  a: number;
  b: number;
  /** Share of the squared distance that this axis accounts for (sums to 1). */
  share: number;
};

/** Exact decomposition of the distance between two places into axis shares. */
export function explainPair(
  index: ProfileIndex,
  a: string,
  b: string,
): { distance: number; axes: AxisContribution[] } | null {
  const rowA = index.row.get(a);
  const rowB = index.row.get(b);
  if (rowA === undefined || rowB === undefined) {
    return null;
  }
  const va = index.file.vectors[rowA];
  const vb = index.file.vectors[rowB];
  const squared = va.map((value, i) => (value - vb[i]) ** 2);
  const total = squared.reduce((sum, value) => sum + value, 0);
  return {
    distance: Math.sqrt(total),
    axes: index.file.axes.map((meta, i) => ({
      axis: meta.axis,
      label: meta.draft_label,
      labelStatus: meta.label_status,
      a: va[i],
      b: vb[i],
      share: total === 0 ? 0 : squared[i] / total,
    })),
  };
}

/** Where a distance sits among all pairwise distances from the same place (0 to 100). */
export function percentileAmong(value: number, all: Iterable<number>): number {
  let below = 0;
  let count = 0;
  for (const other of all) {
    count += 1;
    if (other < value) {
      below += 1;
    }
  }
  return count === 0 ? 0 : (below / count) * 100;
}

/** Pipeline reasons for a precomputed similar pair, as named indicator shares. */
export function pipelineReasons(
  index: ProfileIndex,
  a: string,
  b: string,
): { alike: { indicator: string; share: number }[]; different: { indicator: string; share: number }[] } | null {
  const rows = index.file.similar.places[a];
  const row = rows?.find((entry) => entry[0] === b);
  if (!row) {
    return null;
  }
  const name = (i: number) => index.file.similar.indicators[i] ?? `input ${i}`;
  return {
    alike: row[2].map(([i, share]) => ({ indicator: name(i), share })),
    different: row[3].map(([i, share]) => ({ indicator: name(i), share })),
  };
}
