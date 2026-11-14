import type { Metadata } from "next";
import Link from "next/link";

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
          grouped by topic. Each page states the definition, the national value, the district
          distribution and the limits of the measure.
        </p>
      </header>
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
