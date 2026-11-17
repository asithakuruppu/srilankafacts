import { describe, expect, it } from "vitest";

import {
  ELECTION_MEASURES,
  candidateRows,
  displayName,
  formatShare,
  formatTotal,
  indexElectoral,
  measureValues,
} from "@/lib/atlas/elections";
import { levelForZoom, zoomBand } from "@/lib/atlas/scale";
import type { ElectionPlace, ElectoralFile } from "@/lib/atlas/types";

const totals = (turnout: number | null) => ({
  electors_registered: 100,
  votes_polled: 80,
  votes_valid: 78,
  votes_rejected: 2,
  turnout,
  votes_rejected_share: 2.5,
});

function place(id: string, level: ElectionPlace["level"], parent: string | null, turnout: number | null): ElectionPlace {
  return {
    id,
    level,
    name: id,
    ec_code: null,
    parent,
    values: totals(turnout),
    postal: null,
    votes: [
      [2, 30, 38.46],
      [1, null, null],
    ],
    not_available: 1,
    source: { locator: null, sha256: null, verification: ["machine_extracted"] },
  };
}

const file: ElectoralFile = {
  status: "release_values",
  election: { id: "presidential-2024", name: "Presidential Election 2024", date: "2024-09-21" },
  dataset_id: "election-results",
  release: "vtest",
  landing_page: null,
  publication: null,
  verification_note: "",
  candidates: [
    { ballot: 1, name: "FIRST CANDIDATE", party: "P1" },
    { ballot: 2, name: "SECOND CANDIDATE", party: "P2" },
  ],
  country: place("LK", "country", null, 80),
  eds: [place("LK-ED-01", "ed", null, 80), place("LK-ED-02", "ed", null, null)],
  pds: [place("LK-PD-01A", "pd", "LK-ED-01", 75), place("LK-PD-01B", "pd", "LK-ED-01", 85)],
};

describe("election helpers", () => {
  const index = indexElectoral(file);

  it("never shows a candidate's share on the map", () => {
    expect(ELECTION_MEASURES.map((m) => m.id)).not.toContain("votes_candidate_share");
  });

  it("keeps ballot order and leaves unread values unread", () => {
    const rows = candidateRows(index, file.eds[0]);
    expect(rows.map((r) => r.ballot)).toEqual([1, 2]);
    expect(rows[0].votes).toBeNull();
    expect(formatShare(rows[0].share)).toBe("not read");
    expect(formatTotal("turnout", null)).toBe("not read");
    expect(formatTotal("turnout", 79.4611)).toBe("79.46%");
    expect(formatTotal("electors_registered", 17140354)).toBe("17,140,354");
  });

  it("omits EDs whose value was not read from map values", () => {
    expect([...measureValues(index, "turnout").keys()]).toEqual(["LK-ED-01"]);
  });

  it("groups polling divisions under their ED", () => {
    expect(index.pdsOf.get("LK-ED-01")?.map((p) => p.id)).toEqual(["LK-PD-01A", "LK-PD-01B"]);
  });

  it("title-cases names printed in capitals only", () => {
    expect(displayName("ANURA KUMARA DISSANAYAKE")).toBe("Anura Kumara Dissanayake");
    expect(displayName("A.S.P. LIYANAGE")).toBe("A.S.P. Liyanage");
    expect(displayName("Colombo North")).toBe("Colombo North");
  });

  it("the ED scale ignores zoom", () => {
    expect(levelForZoom(12, ["ed"])).toBe("ed");
    expect(zoomBand("ed")).toEqual([0, 24]);
  });
});
