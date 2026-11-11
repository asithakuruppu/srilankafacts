import type { Metadata } from "next";
import { Suspense } from "react";

import ExploreClient from "@/app/explore/explore-client";
import ExploreStatic from "@/components/explore-static";
import { defaultIndicatorId, defaultLevelName } from "@/lib/explore-levels";
import { exploreLevels } from "@/lib/explore-server";
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
  // The explorer reads the URL in the browser, so the prerendered HTML holds this fallback.
  // Rendering the default table here keeps /explore readable without JavaScript (D-027).
  const fallback = (
    <ExploreStatic
      indicatorId={defaultIndicatorId(indicators.map((indicator) => indicator.id))}
      levelName={defaultLevelName(exploreLevels())}
    />
  );
  return (
    <Suspense fallback={fallback}>
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
