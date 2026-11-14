import type { Metadata } from "next";
import Link from "next/link";

import { formatValue } from "@/lib/format";
import { getIndicators, getNationalValues } from "@/lib/release";

export const metadata: Metadata = {
  title: "Indicators",
  description: "The 14 Census Atlas 2024 indicators in the Sri Lanka Facts preview.",
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
          {indicators.length} measures built from the DCS Census 2024 workbooks and tables held. Each page states
          the definition, the national value, the district distribution and the limits of the
          measure.
        </p>
      </header>
      <div className="indicator-list">
        {indicators.map((indicator) => (
          <Link key={indicator.id} href={`/indicator/${indicator.id}`} className="indicator-row">
            <span>
              <strong>{indicator.name}</strong>
              <small>{indicator.definition}</small>
            </span>
            <span className="indicator-row-value">
              {formatValue(national.get(indicator.id) ?? null, indicator.unit, indicator.decimals)}
              <small>{indicator.unit}</small>
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
