import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import IndicatorExplorer from "@/components/indicator-explorer";

import { formatValue } from "@/lib/format";
import { groupIndicators } from "@/lib/indicator-groups";
import { getIndicators, getNationalValues } from "@/lib/release";

export const metadata: Metadata = {
  title: "Indicators",
  description:
    "Census Atlas 2024 indicators in the Sri Lanka Facts preview, grouped by topic, each with its definition and national value.",
  alternates: { canonical: "/indicators" },
};

export default function IndicatorsPage() {
  const indicators = getIndicators();
  const national = getNationalValues();
  return (
    <div className="shell section">
      <header className="place-head">
        <p className="eyebrow">Census Atlas 2024</p>
        <h1>Indicators</h1>
        <p className="lede">
          {indicators.length} measures built from the DCS Census 2024 workbooks and tables held,
          grouped by topic. Pick one, then drill down from the country through province, district
          and DS division to the GN division. Each indicator page states the definition and the
          limits of the measure.
        </p>
      </header>
      <Suspense fallback={null}>
        <IndicatorExplorer
          indicators={groupIndicators(indicators).flatMap((group) =>
            group.indicators.map((indicator) => ({
              id: indicator.id,
              name: indicator.name,
              definition: indicator.definition,
              unit: indicator.unit,
              decimals: indicator.decimals,
              measureType: indicator.measure_type,
              levels: indicator.levels,
              group: group.label,
            })),
          )}
        />
      </Suspense>
      <h2 className="section">All indicators</h2>
      {groupIndicators(indicators).map((group) => (
        <section className="section" key={group.label} aria-label={group.label}>
          <h2>
            {group.label} <small className="muted">· {group.indicators.length}</small>
          </h2>
          <div className="indicator-list">
            {group.indicators.map((indicator) => (
              <Link
                key={indicator.id}
                href={`/indicator/${indicator.id}`}
                className="indicator-row"
              >
                <span>
                  <strong>{indicator.name}</strong>
                  <small>{indicator.definition}</small>
                </span>
                <span className="indicator-row-value">
                  {formatValue(
                    national.get(indicator.id) ?? null,
                    indicator.unit,
                    indicator.decimals,
                  )}
                  <small>{indicator.unit}</small>
                </span>
              </Link>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
