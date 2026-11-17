/**
 * The `text` space v0.1: character 2- and 3-gram TF-IDF vectors of place names, cosine
 * similarity. Mirrors `pipeline/slf/spaces.py` (`build_text_index`, `text_search`) exactly so
 * the browser's results can be checked against the pipeline's for every unit. No model.
 */

import { normalise, type SearchEntry } from "@/lib/search";

export const TEXT_SPACE = { id: "text", version: "0.1" } as const;

export type TextIndex = {
  placeOf: number[];
  entries: SearchEntry[];
  idf: Map<string, number>;
  postings: Map<string, { docs: number[]; weights: number[] }>;
  docs: number;
};

export function grams(text: string): Map<string, number> {
  const chars = Array.from(` ${text} `);
  const out = new Map<string, number>();
  for (const n of [2, 3]) {
    for (let i = 0; i + n <= chars.length; i += 1) {
      const gram = chars.slice(i, i + n).join("");
      out.set(gram, (out.get(gram) ?? 0) + 1);
    }
  }
  return out;
}

/** One document per non-empty name (English, Sinhala, Tamil) of each place. */
export function buildTextIndex(entries: SearchEntry[]): TextIndex {
  const placeOf: number[] = [];
  const counts: Map<string, number>[] = [];
  entries.forEach((entry, p) => {
    for (const name of [entry.n, entry.s, entry.t]) {
      if (name) {
        const folded = normalise(name);
        if (folded) {
          placeOf.push(p);
          counts.push(grams(folded));
        }
      }
    }
  });
  const df = new Map<string, number>();
  for (const c of counts) {
    for (const g of c.keys()) {
      df.set(g, (df.get(g) ?? 0) + 1);
    }
  }
  const docs = counts.length;
  const idf = new Map<string, number>();
  for (const [g, v] of df) {
    idf.set(g, Math.log((docs + 1) / (v + 1)) + 1);
  }
  const postings = new Map<string, { docs: number[]; weights: number[] }>();
  counts.forEach((c, d) => {
    let norm = 0;
    const weights: [string, number][] = [];
    for (const [g, tf] of c) {
      const w = tf * (idf.get(g) ?? 0);
      weights.push([g, w]);
      norm += w * w;
    }
    norm = Math.sqrt(norm);
    for (const [g, w] of weights) {
      let list = postings.get(g);
      if (!list) {
        list = { docs: [], weights: [] };
        postings.set(g, list);
      }
      list.docs.push(d);
      list.weights.push(w / norm);
    }
  });
  return { placeOf, entries, idf, postings, docs };
}

/** Best cosine per place for a query, as a map from entry index to score. */
export function textScores(index: TextIndex, query: string): Map<number, number> {
  const best = new Map<number, number>();
  const folded = normalise(query);
  if (!folded) {
    return best;
  }
  const unseen = Math.log(index.docs + 1) + 1;
  const q = grams(folded);
  let norm = 0;
  const weights: [string, number][] = [];
  for (const [g, tf] of q) {
    const w = tf * (index.idf.get(g) ?? unseen);
    weights.push([g, w]);
    norm += w * w;
  }
  norm = Math.sqrt(norm);
  const scores = new Map<number, number>();
  for (const [g, w] of weights) {
    const list = index.postings.get(g);
    if (!list) {
      continue;
    }
    const scale = w / norm;
    for (let i = 0; i < list.docs.length; i += 1) {
      const d = list.docs[i];
      scores.set(d, (scores.get(d) ?? 0) + list.weights[i] * scale);
    }
  }
  for (const [d, score] of scores) {
    const p = index.placeOf[d];
    if (score > (best.get(p) ?? 0)) {
      best.set(p, score);
    }
  }
  return best;
}

/** Top places by text similarity: ties by level (coarser first), then id. */
export function textSearch(index: TextIndex, query: string, k = 5): { id: string; score: number }[] {
  const best = textScores(index, query);
  const round9 = (v: number) => Math.round(v * 1e9) / 1e9;
  return [...best.entries()]
    .sort(
      ([pa, a], [pb, b]) =>
        round9(b) - round9(a) ||
        index.entries[pa].l - index.entries[pb].l ||
        (index.entries[pa].i < index.entries[pb].i ? -1 : 1),
    )
    .slice(0, k)
    .map(([p, score]) => ({ id: index.entries[p].i, score: Math.round(score * 1e6) / 1e6 }));
}
