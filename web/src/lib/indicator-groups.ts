import type { IndicatorMeta } from "@/lib/types";

/** Reader-facing groups, keyed by the catalogue topic (first two entries joined by "/"). */
const GROUPS: { label: string; topics: string[] }[] = [
  { label: "Population, sex and density", topics: ["population", "population/sex", "population/housing"] },
  { label: "Age", topics: ["population/age"] },
  { label: "Sector", topics: ["population/sector"] },
  { label: "Local authority type", topics: ["population/local-government"] },
  { label: "Households and housing units", topics: ["housing"] },
  { label: "Drinking water", topics: ["housing/water"] },
  { label: "Cooking fuel and lighting", topics: ["housing/energy"] },
  { label: "Toilet facilities", topics: ["housing/sanitation"] },
  {
    label: "Housing structure and materials (DS divisions and larger)",
    topics: ["housing/structure", "housing/wall", "housing/roof", "housing/floor"],
  },
];

export type IndicatorGroup = { label: string; indicators: IndicatorMeta[] };

function topicKey(indicator: IndicatorMeta): string {
  return (indicator.topic ?? []).slice(0, 2).join("/");
}

/** Group indicators for display; anything without a known topic goes to "Other". */
export function groupIndicators(indicators: IndicatorMeta[]): IndicatorGroup[] {
  const byTopic = new Map<string, number>();
  GROUPS.forEach((group, i) => group.topics.forEach((topic) => byTopic.set(topic, i)));
  const buckets: IndicatorMeta[][] = GROUPS.map(() => []);
  const other: IndicatorMeta[] = [];
  for (const indicator of indicators) {
    const i = byTopic.get(topicKey(indicator));
    if (i === undefined) {
      other.push(indicator);
    } else {
      buckets[i].push(indicator);
    }
  }
  const groups = GROUPS.map((group, i) => ({ label: group.label, indicators: buckets[i] }));
  groups.push({ label: "Other", indicators: other });
  return groups.filter((group) => group.indicators.length > 0);
}
