import fs from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  axisShares,
  blockShares,
  compositeVectors,
  nearestIn,
  pointSpace,
  type CompositeFile,
  type TrajectoryFile,
} from "@/lib/atlas/spaces";
import { searchPlaces, type SearchEntry } from "@/lib/search";
import { buildTextIndex, textScores, textSearch } from "@/lib/text-space";

const composite: CompositeFile = {
  space_id: "composite",
  space_version: "0.1",
  base: { space_id: "profile", space_version: "0.3", level: "ds" },
  note: "",
  blocks: [
    { id: "demography", label: "Population and age", inputs: 6 },
    { id: "identity", label: "Ethnic group and religion", inputs: 16 },
  ],
  axes: [
    { axis: 1, draft_label: "a", label_status: "machine_generated_draft" },
    { axis: 2, draft_label: "b", label_status: "machine_generated_draft" },
  ],
  ids: ["A", "B", "C"],
  contrib: [
    [
      [0, 0],
      [0, 0],
    ],
    [
      [1, 0],
      [0, 3],
    ],
    [
      [0, 2],
      [0, 0],
    ],
  ],
};

describe("composite space", () => {
  it("weights scale block contributions; all ones is the base space", () => {
    expect(compositeVectors(composite, [1, 1])).toEqual([
      [0, 0],
      [1, 3],
      [0, 2],
    ]);
    const noIdentity = pointSpace(composite.ids, compositeVectors(composite, [1, 0]));
    expect(nearestIn(noIdentity, "A", 2).map((n) => n.id)).toEqual(["B", "C"]);
    const equal = pointSpace(composite.ids, compositeVectors(composite, [1, 1]));
    expect(nearestIn(equal, "A", 2).map((n) => n.id)).toEqual(["C", "B"]);
  });

  it("splits a squared distance exactly by axis and by block", () => {
    const shares = blockShares(composite, [1, 1], "A", "B");
    expect(shares).not.toBeNull();
    const sum = (v: number[]) => v.reduce((s, x) => s + x, 0);
    expect(sum(shares!.axis)).toBeCloseTo(1, 12);
    expect(sum(shares!.block)).toBeCloseTo(1, 12);
    expect(shares!.block[1]).toBeCloseTo(0.9, 12); // 9 of 10 comes from identity on axis 2
    const space = pointSpace(composite.ids, compositeVectors(composite, [1, 1]));
    expect(axisShares(space, "A", "B")).toEqual([0.1, 0.9]);
  });
});

const entries: SearchEntry[] = [
  { i: "LK11", n: "Colombo", s: "කොළඹ", t: "கொழும்பு", l: 2 },
  { i: "LK1103", n: "Colombo", s: null, t: null, l: 3 },
  { i: "LK12", n: "Gampaha", s: "ගම්පහ", t: null, l: 2 },
  { i: "LK1127", n: "Dehiwala", s: null, t: null, l: 3 },
];

describe("text space", () => {
  const index = buildTextIndex(entries);

  it("finds misspellings and every script", () => {
    expect(textSearch(index, "Colmbo")[0].id).toBe("LK11");
    expect(textSearch(index, "කොළඹ")[0]).toEqual({ id: "LK11", score: 1 });
    expect(textSearch(index, "கொழும்பு")[0].id).toBe("LK11");
    expect(textSearch(index, "  ")).toEqual([]);
  });

  it("lets a misspelt query reach the search results, ranked by similarity", () => {
    const text = { scores: (q: string) => textScores(index, q) };
    expect(searchPlaces(entries, "Dehivla", 8)).toEqual([]);
    expect(searchPlaces(entries, "Dehivla", 8, text)[0].i).toBe("LK1127");
    // An exact match still outranks a fuzzy one.
    expect(searchPlaces(entries, "Gampaha", 8, text)[0].i).toBe("LK12");
  });
});

// Agreement with the pipeline on every unit, when the local builds are present (not in CI).
const root = path.resolve(__dirname, "../..");
const spacesDir = path.resolve(root, "../pipeline/data/build/spaces");
const readJson = <T,>(file: string): T => JSON.parse(fs.readFileSync(file, "utf8")) as T;

function sameRanking(
  got: { id: string; distance: number }[],
  want: [string, number][],
  tolerance: number,
): boolean {
  if (got.length !== want.length) {
    return false;
  }
  return got.every((g, i) => {
    if (Math.abs(g.distance - want[i][1]) > tolerance) {
      return false;
    }
    // An order swap is only acceptable between two equal distances.
    return g.id === want[i][0] || Math.abs(want[i][1] - g.distance) <= tolerance;
  });
}

describe.skipIf(!fs.existsSync(path.join(spacesDir, "expected_composite.json")))(
  "browser vs pipeline (local builds)",
  () => {
    it("composite: the same 10 nearest for every DS division under every preset", () => {
      const file = readJson<CompositeFile>(path.join(spacesDir, "composite.json"));
      const expected = readJson<
        Record<string, { weights: number[]; similar: Record<string, [string, number][]> }>
      >(path.join(spacesDir, "expected_composite.json"));
      let checked = 0;
      for (const preset of Object.values(expected)) {
        const space = pointSpace(file.ids, compositeVectors(file, preset.weights));
        for (const id of file.ids) {
          expect(sameRanking(nearestIn(space, id, 10), preset.similar[id], 2e-6)).toBe(true);
          checked += 1;
        }
      }
      expect(checked).toBe(file.ids.length * Object.keys(expected).length);
    });

    it("trajectory: the same 10 nearest for every unit in the space", () => {
      const file = readJson<TrajectoryFile>(path.join(spacesDir, "trajectory.json"));
      const space = pointSpace(file.ids, file.vectors);
      for (const id of file.ids) {
        expect(sameRanking(nearestIn(space, id, 10), file.similar[id], 2e-6)).toBe(true);
      }
    });

    it.skipIf(!fs.existsSync(path.join(root, "public/search-index.json")))(
      "text: the same top 5 for a misspelling of every name",
      () => {
        const index = buildTextIndex(readJson<SearchEntry[]>(path.join(root, "public/search-index.json")));
        const expected = readJson<{ k: number; queries: Record<string, [string, number][]> }>(
          path.join(spacesDir, "expected_text.json"),
        );
        const mismatches: string[] = [];
        for (const [query, want] of Object.entries(expected.queries)) {
          const got = textSearch(index, query, expected.k).map((r) => ({ id: r.id, distance: r.score }));
          if (!sameRanking(got, want, 2e-6)) {
            mismatches.push(query);
          }
        }
        expect(mismatches.slice(0, 5)).toEqual([]);
      },
      120_000,
    );
  },
);
