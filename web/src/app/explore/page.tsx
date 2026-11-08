import type { Metadata } from "next";
import { Suspense } from "react";

import ExploreClient from "@/app/explore/explore-client";
import { getBoundaryLevels, getIndicators, getNationalValues } from "@/lib/release";

export const metadata: Metadata = {
  title: "Explore",
  description:
    "Explore Census Atlas 2024 indicators by province, district, DS division and GN division.",
  alternates: { canonical: "/explore" },
};

export default function ExplorePage() {
  const indicators = getIndicators();
  const boundaryLevels = getBoundaryLevels();
  const national = Object.fromEntries(getNationalValues());
  return (
    <Suspense fallback={<div className="shell section">Loading explorer…</div>}>
      <ExploreClient
        indicators={indicators.map((indicator) => ({
          id: indicator.id,
          name: indicator.name,
          unit: indicator.unit,
          decimals: indicator.decimals,
          measureType: indicator.measure_type,
        }))}
        boundaryLevels={boundaryLevels}
        national={national}
      />
    </Suspense>
  );
}
