/**
 * Election results in the atlas (D-039, D-040). Pure helpers, no DOM.
 *
 * Presentation rules: candidates keep ballot-paper order and are never ranked; the map shows
 * only measures about the election as a whole (turnout, rejected ballots, electors, valid
 * votes), never a candidate's share; an unread value stays "not read", never zero.
 */

import type { ElectionPlace, ElectionTotals, ElectoralFile } from "@/lib/atlas/types";

export type ElectionMeasure = {
  id: keyof ElectionTotals;
  label: string;
  unit: "percent" | "persons" | "votes";
  definition: string;
};

/** Measures the map can colour by, in this order. */
export const ELECTION_MEASURES: ElectionMeasure[] = [
  {
    id: "turnout",
    label: "Turnout",
    unit: "percent",
    definition: "Votes polled as a percentage of registered electors (postal votes included).",
  },
  {
    id: "votes_rejected_share",
    label: "Rejected ballots",
    unit: "percent",
    definition: "Rejected ballots as a percentage of votes polled.",
  },
  {
    id: "electors_registered",
    label: "Registered electors",
    unit: "persons",
    definition: "Electors on the 2024 register, as printed on the Commission's result sheets.",
  },
  {
    id: "votes_valid",
    label: "Valid votes",
    unit: "votes",
    definition: "Ballots counted as valid.",
  },
];

export const TOTAL_ROWS: { id: keyof ElectionTotals; label: string }[] = [
  { id: "electors_registered", label: "Registered electors" },
  { id: "votes_polled", label: "Votes polled" },
  { id: "votes_valid", label: "Valid votes" },
  { id: "votes_rejected", label: "Rejected ballots" },
  { id: "turnout", label: "Turnout" },
  { id: "votes_rejected_share", label: "Rejected, share of polled" },
];

export function isPercent(id: keyof ElectionTotals): boolean {
  return id === "turnout" || id === "votes_rejected_share";
}

/** "79.46%", "17,140,354", or "not read" for a value the pipeline could not read. */
export function formatTotal(id: keyof ElectionTotals, value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "not read";
  }
  return isPercent(id)
    ? `${value.toLocaleString("en-LK", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`
    : Math.round(value).toLocaleString("en-LK");
}

export function formatShare(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "not read";
  }
  return `${value.toLocaleString("en-LK", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;
}

export type ElectionIndex = {
  file: ElectoralFile;
  byId: Map<string, ElectionPlace>;
  pdsOf: Map<string, ElectionPlace[]>;
  candidate: Map<number, { name: string; party: string }>;
};

export function indexElectoral(file: ElectoralFile): ElectionIndex {
  const byId = new Map<string, ElectionPlace>();
  const pdsOf = new Map<string, ElectionPlace[]>();
  for (const place of [...(file.country ? [file.country] : []), ...file.eds, ...file.pds]) {
    byId.set(place.id, place);
  }
  for (const pd of file.pds) {
    if (pd.parent) {
      const list = pdsOf.get(pd.parent) ?? [];
      list.push(pd);
      pdsOf.set(pd.parent, list);
    }
  }
  return {
    file,
    byId,
    pdsOf,
    candidate: new Map(file.candidates.map((c) => [c.ballot, { name: c.name, party: c.party }])),
  };
}

/** One value per ED for a measure, omitting EDs where it was not read. */
export function measureValues(index: ElectionIndex, id: keyof ElectionTotals): Map<string, number> {
  const values = new Map<string, number>();
  for (const ed of index.file.eds) {
    const value = ed.values[id];
    if (value !== null && Number.isFinite(value)) {
      values.set(ed.id, value);
    }
  }
  return values;
}

/** Candidate rows in ballot order; the file is already in ballot order, this keeps it so. */
export function candidateRows(
  index: ElectionIndex,
  place: ElectionPlace,
): { ballot: number; name: string; party: string; votes: number | null; share: number | null }[] {
  return [...place.votes]
    .sort((a, b) => a[0] - b[0])
    .map(([ballot, votes, share]) => ({
      ballot,
      name: index.candidate.get(ballot)?.name ?? `Ballot ${ballot}`,
      party: index.candidate.get(ballot)?.party ?? "",
      votes,
      share,
    }));
}

/** Title-case a name printed in capitals on the sheets ("ANURA KUMARA" -> "Anura Kumara"). */
export function displayName(name: string): string {
  if (name !== name.toUpperCase()) {
    return name;
  }
  return name
    .toLowerCase()
    .replace(/(^|[\s.(-])([a-z])/g, (_m, lead: string, ch: string) => lead + ch.toUpperCase());
}
