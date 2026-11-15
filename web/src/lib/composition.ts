/** Share indicators that are parts of one whole (they add to 100%), for pie charts. */

export type ShareMember = { id: string; label: string };
export type ShareFamily = { key: string; title: string; members: ShareMember[] };

type CatalogEntry = { id: string; name: string; measureType: string };

const AGE_BAND = /^population_age_\d+_(\d+|plus)_share$/;
// Broad groups that overlap the 5-year bands; they are not parts of the same whole.
const AGE_OVERLAP = new Set(["population_age_0_14_share", "population_age_60_plus_share"]);

/**
 * Families come from the catalogue names: "Share of … by X: Category" groups by the text before the
 * colon, and the 5-year age bands form one family. Each family was checked against the release:
 * its members add to 100% at country and district level (see tests and the PR notes).
 */
export function shareFamilies(indicators: CatalogEntry[]): Map<string, ShareFamily> {
  const families = new Map<string, ShareFamily>();
  const add = (key: string, title: string, member: ShareMember) => {
    const family = families.get(key) ?? { key, title, members: [] };
    family.members.push(member);
    families.set(key, family);
  };
  for (const indicator of indicators) {
    if (indicator.measureType !== "share") {
      continue;
    }
    if (AGE_BAND.test(indicator.id) && !AGE_OVERLAP.has(indicator.id)) {
      add("age5", "Population by 5-year age group", {
        id: indicator.id,
        label: indicator.name.replace(/^Share of population aged /, ""),
      });
      continue;
    }
    const colon = indicator.name.indexOf(": ");
    if (colon > 0 && !AGE_BAND.test(indicator.id)) {
      const title = indicator.name.slice(0, colon).replace(/^Share of /, "");
      add(title, title.charAt(0).toUpperCase() + title.slice(1), {
        id: indicator.id,
        label: indicator.name.slice(colon + 2),
      });
    }
  }
  for (const [key, family] of [...families]) {
    if (family.members.length < 2) {
      families.delete(key);
    }
  }
  return families;
}

/** Map each member indicator id to its family. */
export function familyByIndicator(families: Map<string, ShareFamily>): Map<string, ShareFamily> {
  const byId = new Map<string, ShareFamily>();
  for (const family of families.values()) {
    for (const member of family.members) {
      byId.set(member.id, family);
    }
  }
  return byId;
}

export type Slice = { id: string | null; label: string; value: number; merged?: number };

/**
 * Pie slices: zero values are dropped; when there are more than `max` categories the smallest are
 * merged into one "Smaller categories" slice (the selected indicator is always kept apart).
 */
export function pieSlices(
  parts: { id: string; label: string; value: number }[],
  selectedId: string | null,
  max = 8,
): Slice[] {
  const positive = parts.filter((part) => part.value > 0).sort((a, b) => b.value - a.value);
  if (positive.length <= max) {
    return positive.map((part) => ({ id: part.id, label: part.label, value: part.value }));
  }
  const keep = positive.slice(0, max - 1);
  const rest = positive.slice(max - 1);
  const selected = rest.find((part) => part.id === selectedId);
  const kept = selected ? [...keep.slice(0, max - 2), selected] : keep;
  const merged = positive.filter((part) => !kept.includes(part));
  const slices: Slice[] = kept
    .sort((a, b) => b.value - a.value)
    .map((part) => ({ id: part.id, label: part.label, value: part.value }));
  slices.push({
    id: null,
    label: "Smaller categories",
    value: merged.reduce((sum, part) => sum + part.value, 0),
    merged: merged.length,
  });
  return slices;
}
