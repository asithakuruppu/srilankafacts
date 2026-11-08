export type SearchEntry = {
  i: string;
  n: string;
  s?: string | null;
  t?: string | null;
  l: number;
  p?: string | null;
  pn?: string | null;
};

export type SearchResult = SearchEntry & { score: number };

/**
 * Fold a name for tolerant matching.
 *
 * The release has no `alt_names` yet (checked 2026-11-08), so common romanisation
 * variants are folded here: doubled vowels, w/v, th/t, ph/f, repeated letters and
 * diacritics. Sinhala and Tamil are NFC-normalised and kept as their own strings.
 */
export function normalise(value: string): string {
  const text = value.normalize("NFC").toLowerCase().trim();
  if (/[\u0d80-\u0dff\u0b80-\u0bff]/.test(text)) {
    // Sinhala and Tamil vowel signs are combining marks: do not strip them.
    return text.replace(/\s+/g, " ").trim();
  }
  let folded = text.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  folded = folded.replace(/[^a-z0-9 ]+/g, " ");
  folded = folded.replace(/\s+/g, " ");
  folded = folded.replace(/oo/g, "u").replace(/ou/g, "u");
  folded = folded.replace(/th/g, "t").replace(/ph/g, "f");
  folded = folded.replace(/dh/g, "d").replace(/bh/g, "b").replace(/gh/g, "g");
  folded = folded.replace(/w/g, "v");
  folded = folded.replace(/(.)\1+/g, "$1");
  return folded.trim();
}

function scoreName(query: string, name: string, weight: number): number {
  if (!name) {
    return 0;
  }
  if (name === query) {
    return 1000 * weight;
  }
  if (name.startsWith(query)) {
    return 700 * weight;
  }
  const words = name.split(" ");
  if (words.some((word) => word.startsWith(query))) {
    return 500 * weight;
  }
  if (name.includes(query)) {
    return 300 * weight;
  }
  const tokens = query.split(" ");
  if (tokens.length > 1 && tokens.every((token) => name.includes(token))) {
    return 200 * weight;
  }
  return 0;
}

export function searchPlaces(
  entries: SearchEntry[],
  query: string,
  limit = 8,
): SearchResult[] {
  const folded = normalise(query);
  if (folded.length === 0) {
    return [];
  }
  const results: SearchResult[] = [];
  for (const entry of entries) {
    const candidates: Array<[string, number]> = [
      [entry.n ?? "", 1],
      [entry.s ?? "", 1.05],
      [entry.t ?? "", 1.05],
    ];
    let best = 0;
    for (const [name, weight] of candidates) {
      if (!name) {
        continue;
      }
      best = Math.max(best, scoreName(folded, normalise(name), weight));
    }
    if (best > 0) {
      results.push({ ...entry, score: best });
    }
  }
  results.sort((a, b) => {
    if (b.score !== a.score) {
      return b.score - a.score;
    }
    if (a.l !== b.l) {
      return a.l - b.l;
    }
    return a.n.localeCompare(b.n);
  });
  return results.slice(0, limit);
}
