/**
 * "Compared to where?" for one value: neighbours, parent, similar places and the country.
 *
 * Pure functions over published values. Nothing here changes a value; every statistic is a
 * plain summary (median, rank, share) that a reader can redo from the level file.
 */

export type ValueMap = Map<string, number>;

export function median(values: number[]): number | null {
  if (values.length === 0) {
    return null;
  }
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 1 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

export function quantile(sorted: number[], fraction: number): number {
  if (sorted.length === 0) {
    return Number.NaN;
  }
  const position = (sorted.length - 1) * fraction;
  const base = Math.floor(position);
  const rest = position - base;
  const next = sorted[base + 1];
  return next === undefined ? sorted[base] : sorted[base] + rest * (next - sorted[base]);
}

export type GroupSummary = {
  /** Units in the group. */
  count: number;
  /** Units in the group that have a value. */
  withValue: number;
  median: number | null;
  min: number | null;
  max: number | null;
  /** How many group members have a lower / higher value than the place. */
  lower: number;
  higher: number;
};

export function summariseGroup(
  ids: string[],
  values: ValueMap,
  own: number | null,
): GroupSummary {
  const present = ids.map((id) => values.get(id)).filter((v): v is number => v !== undefined);
  return {
    count: ids.length,
    withValue: present.length,
    median: median(present),
    min: present.length ? Math.min(...present) : null,
    max: present.length ? Math.max(...present) : null,
    lower: own === null ? 0 : present.filter((v) => v < own).length,
    higher: own === null ? 0 : present.filter((v) => v > own).length,
  };
}

/** Rank by value, 1 = highest, among units with a value (ties share the better rank). */
export function rankOf(id: string, values: ValueMap): { rank: number; total: number } | null {
  const own = values.get(id);
  if (own === undefined) {
    return null;
  }
  let higher = 0;
  for (const value of values.values()) {
    if (value > own) {
      higher += 1;
    }
  }
  return { rank: higher + 1, total: values.size };
}

export type Difference = { text: string; direction: "above" | "below" | "equal" };

/**
 * Difference between a value and a reference, in the unit that is honest for it:
 * percentage points for shares, a ratio for everything else.
 */
export function describeDifference(
  value: number,
  reference: number,
  unit: string,
): Difference {
  const delta = value - reference;
  const direction = delta > 0 ? "above" : delta < 0 ? "below" : "equal";
  if (unit === "percent") {
    const points = Math.abs(delta);
    return {
      text: direction === "equal" ? "the same" : `${points.toFixed(1)} points ${direction}`,
      direction,
    };
  }
  if (reference === 0) {
    return { text: direction === "equal" ? "the same" : direction, direction };
  }
  const ratio = Math.abs(delta / reference) * 100;
  if (ratio >= 100 && delta > 0) {
    return { text: `${(value / reference).toFixed(1)}× as high`, direction };
  }
  return {
    text: direction === "equal" ? "the same" : `${ratio.toFixed(ratio < 10 ? 1 : 0)}% ${direction}`,
    direction,
  };
}

/** Share of a total, for counts ("12.3% of Western Province"). */
export function shareOf(value: number, total: number | null | undefined): number | null {
  if (total === null || total === undefined || total <= 0) {
    return null;
  }
  return (value / total) * 100;
}

/** Class breaks for a sequential map: quantiles of the distinct values, at most `classes`. */
export function quantileBreaks(values: number[], classes = 5): number[] {
  const distinct = [...new Set(values.filter((v) => Number.isFinite(v)))].sort((a, b) => a - b);
  if (distinct.length <= 1) {
    return [];
  }
  if (distinct.length <= classes) {
    return distinct.slice(1);
  }
  const breaks: number[] = [];
  for (let i = 1; i < classes; i += 1) {
    const value = Number(quantile(distinct, i / classes).toPrecision(6));
    if (breaks[breaks.length - 1] !== value) {
      breaks.push(value);
    }
  }
  return breaks;
}

/** Index of the class a value falls in, given ascending breaks (value >= break moves up). */
export function classIndex(value: number, breaks: number[]): number {
  let index = 0;
  while (index < breaks.length && value >= breaks[index]) {
    index += 1;
  }
  return index;
}

/** Symmetric breaks around zero for a diverging map (change, difference). */
export function divergingBreaks(values: number[]): number[] {
  const magnitudes = values
    .filter((v) => Number.isFinite(v))
    .map((v) => Math.abs(v))
    .sort((a, b) => a - b);
  if (magnitudes.length === 0) {
    return [];
  }
  const outer = Number(quantile(magnitudes, 0.8).toPrecision(2));
  const inner = Number((outer / 3).toPrecision(2));
  if (outer === 0 || inner === 0 || inner === outer) {
    return [];
  }
  return [-outer, -inner, inner, outer];
}

/** Histogram counts over equal-width bins between min and max. */
export function histogram(values: number[], bins = 24): { counts: number[]; min: number; max: number } {
  const finite = values.filter((v) => Number.isFinite(v));
  if (finite.length === 0) {
    return { counts: [], min: 0, max: 0 };
  }
  const min = Math.min(...finite);
  const max = Math.max(...finite);
  const counts = new Array<number>(bins).fill(0);
  if (max === min) {
    counts[0] = finite.length;
    return { counts, min, max };
  }
  for (const value of finite) {
    const index = Math.min(bins - 1, Math.floor(((value - min) / (max - min)) * bins));
    counts[index] += 1;
  }
  return { counts, min, max };
}
