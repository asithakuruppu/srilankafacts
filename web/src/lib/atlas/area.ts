/**
 * Estimates for a drawn or radius area from GN counts, through the analytic grid (G07).
 *
 * Each GN count is shared equally among the H3 cells whose centres fall in that GN; an area's
 * estimate is the sum over the cells whose centres fall inside the area. GNs wholly inside
 * contribute their exact count. Everything else is a modelled estimate whose information
 * floor is the GN division: the census does not say where inside a GN people live.
 */

export type GridFile = { resolution: number; gn: string[]; cells: [number, number, number][] };

export type AreaShape =
  | { kind: "circle"; centre: [number, number]; radiusKm: number }
  | { kind: "polygon"; ring: number[][] };

export type GnShare = { id: string; inside: number; total: number; value: number | null };

export type AreaEstimate = {
  estimate: number;
  cells: number;
  /** GN divisions with at least one cell inside, with the share of their cells inside. */
  gns: GnShare[];
  /** GNs touched by the area whose value is missing: their share is not counted. */
  missing: string[];
  wholeGns: number;
};

export function estimateArea(
  grids: GridFile[],
  values: Map<string, number>,
  contains: (point: [number, number]) => boolean,
): AreaEstimate {
  const shares = new Map<string, GnShare>();
  let cells = 0;
  for (const grid of grids) {
    const totals = new Array<number>(grid.gn.length).fill(0);
    for (const cell of grid.cells) {
      totals[cell[2]] += 1;
    }
    for (const [lon, lat, index] of grid.cells) {
      if (!contains([lon, lat])) {
        continue;
      }
      cells += 1;
      const id = grid.gn[index];
      const share = shares.get(id) ?? {
        id,
        inside: 0,
        total: totals[index],
        value: values.get(id) ?? null,
      };
      share.inside += 1;
      shares.set(id, share);
    }
  }
  let estimate = 0;
  const missing: string[] = [];
  let wholeGns = 0;
  for (const share of shares.values()) {
    if (share.value === null) {
      missing.push(share.id);
      continue;
    }
    estimate += (share.value * share.inside) / share.total;
    if (share.inside === share.total) {
      wholeGns += 1;
    }
  }
  const gns = [...shares.values()].sort(
    (a, b) => (b.value ?? 0) * (b.inside / b.total) - (a.value ?? 0) * (a.inside / a.total),
  );
  return { estimate, cells, gns, missing: missing.sort(), wholeGns };
}
