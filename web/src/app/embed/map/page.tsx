import type { Metadata } from "next";
import { Suspense } from "react";

import EmbedMap from "@/components/atlas/embed-map";
import { groupIndicators } from "@/lib/indicator-groups";
import { getAtlasMeta, getIndicators, getLatest } from "@/lib/release";

import "../../atlas.css";

export const metadata: Metadata = {
  title: "Map (embed)",
  robots: { index: false },
};

export default function EmbedMapPage() {
  const latest = getLatest();
  const meta = getAtlasMeta();
  const indicators = groupIndicators(getIndicators()).flatMap((group) =>
    group.indicators.map((indicator) => ({
      id: indicator.id,
      name: indicator.name,
      short: indicator.short_name ?? indicator.name,
      unit: indicator.unit,
      decimals: indicator.decimals,
      measureType: indicator.measure_type,
      higherIs: indicator.higher_is,
      definition: indicator.definition,
      levels: indicator.levels.map((level) => (level === "ds-provisional" ? "ds" : level)),
      group: group.label,
    })),
  );
  return meta ? (
    <Suspense fallback={null}>
      <EmbedMap indicators={indicators} release={latest.release} citation={latest.citation} />
    </Suspense>
  ) : (
    <p className="embed-frame">This build has no atlas bundle.</p>
  );
}
