/** Compact geography hierarchy used by the indicator drill-down dropdowns. */

/** [geography_id, display name, parent_id, level] as written by scripts/prepare-release.mjs. */
export type HierarchyRow = [string, string, string | null, number];

export type HierarchyNode = {
  id: string;
  name: string;
  parentId: string | null;
  level: number;
};

export const LEVEL_NAMES = ["country", "province", "district", "ds", "gn"] as const;

/** Singular reader-facing label for a spine level (0 to 4). */
export const LEVEL_SINGULAR = [
  "Country",
  "Province",
  "District",
  "DS division",
  "GN division",
];

export type Hierarchy = {
  nodes: Map<string, HierarchyNode>;
  childrenOf: Map<string, HierarchyNode[]>;
};

export function buildHierarchy(rows: HierarchyRow[]): Hierarchy {
  const nodes = new Map<string, HierarchyNode>();
  const childrenOf = new Map<string, HierarchyNode[]>();
  for (const [id, name, parentId, level] of rows) {
    const node = { id, name, parentId, level };
    nodes.set(id, node);
    if (parentId) {
      const siblings = childrenOf.get(parentId);
      if (siblings) {
        siblings.push(node);
      } else {
        childrenOf.set(parentId, [node]);
      }
    }
  }
  for (const list of childrenOf.values()) {
    list.sort((a, b) => a.name.localeCompare(b.name) || a.id.localeCompare(b.id));
  }
  return { nodes, childrenOf };
}

/** Ancestors from the country down to and including `id`. */
export function pathTo(hierarchy: Hierarchy, id: string): HierarchyNode[] {
  const path: HierarchyNode[] = [];
  let current = hierarchy.nodes.get(id);
  while (current) {
    path.unshift(current);
    current = current.parentId ? hierarchy.nodes.get(current.parentId) : undefined;
  }
  return path;
}

export function childrenOf(hierarchy: Hierarchy, id: string): HierarchyNode[] {
  return hierarchy.childrenOf.get(id) ?? [];
}

/** Level-file name for the children of a node at `level`, or null below GN. */
export function childLevelName(level: number): (typeof LEVEL_NAMES)[number] | null {
  return LEVEL_NAMES[level + 1] ?? null;
}

/** Rank (1 = highest value) of `id` among `values`, ties share the lower rank. */
export function rankOf(values: { id: string; value: number }[], id: string): number | null {
  const own = values.find((row) => row.id === id);
  if (!own) {
    return null;
  }
  return values.filter((row) => row.value > own.value).length + 1;
}

/** Equal-width histogram bins over the values. */
export function histogramBins(
  values: number[],
  binCount = 10,
): { from: number; to: number; count: number }[] {
  if (values.length === 0) {
    return [];
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) {
    return [{ from: min, to: max, count: values.length }];
  }
  const width = (max - min) / binCount;
  const bins = Array.from({ length: binCount }, (_, i) => ({
    from: min + i * width,
    to: min + (i + 1) * width,
    count: 0,
  }));
  for (const value of values) {
    const index = Math.min(binCount - 1, Math.floor((value - min) / width));
    bins[index].count += 1;
  }
  return bins;
}
