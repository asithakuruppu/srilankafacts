import Link from "next/link";

import ExploreTable from "@/components/explore-table";
import { staticTableHref } from "@/lib/explore-levels";
import { exploreCombos, exploreLevels, exploreRows } from "@/lib/explore-server";
import { formatValue } from "@/lib/format";
import { getIndicators, getNationalValues } from "@/lib/release";

/**
 * Server-rendered explore view: readable without JavaScript (D-027). Used as the /explore
 * fallback (default indicator and level) and by /explore/table/[indicator]/[level].
 */
export default function ExploreStatic({
  indicatorId,
  levelName,
  headingLevel = "h1",
}: {
  indicatorId: string;
  levelName: string;
  headingLevel?: "h1" | "h2";
}) {
  const indicators = getIndicators();
  const indicator = indicators.find((item) => item.id === indicatorId);
  const level = exploreLevels().find((item) => item.name === levelName);
  if (!indicator || !level) {
    return null;
  }
  const combos = exploreCombos();
  const levelsForIndicator = exploreLevels().filter((item) =>
    combos.some((c) => c.indicator === indicatorId && c.level === item.name),
  );
  const indicatorsForLevel = indicators.filter((item) =>
    combos.some((c) => c.indicator === item.id && c.level === levelName),
  );
  const nationalValue = getNationalValues().get(indicatorId) ?? null;
  const rows = exploreRows(indicatorId, levelName);
  const Heading = headingLevel;
  const interactive = `/explore?indicator=${indicatorId}&level=${levelName}`;

  return (
    <div className="explore explore-static">
      <div className="shell explore-head">
        <div>
          <p className="eyebrow">Explore · table</p>
          <Heading>
            {indicator.name} by {level.singular}
          </Heading>
          <p className="lede">
            Census Atlas 2024. National value:{" "}
            <strong>{formatValue(nationalValue, indicator.unit, indicator.decimals)}</strong>.
            This table works without JavaScript; the{" "}
            <Link href={interactive}>interactive map</Link> needs it.
          </p>
        </div>
      </div>
      <nav className="shell section-tight" aria-label="Choose a table">
        <p className="small">
          <strong>Level:</strong>{" "}
          {levelsForIndicator.map((item, i) => (
            <span key={item.name}>
              {i > 0 ? " · " : ""}
              {item.name === levelName ? (
                <strong aria-current="page">{item.label}</strong>
              ) : (
                <Link href={staticTableHref(indicatorId, item.name)}>{item.label}</Link>
              )}
            </span>
          ))}
        </p>
        <p className="small">
          <strong>Indicator:</strong>{" "}
          {indicatorsForLevel.map((item, i) => (
            <span key={item.id}>
              {i > 0 ? " · " : ""}
              {item.id === indicatorId ? (
                <strong aria-current="page">{item.name}</strong>
              ) : (
                <Link href={staticTableHref(item.id, levelName)}>{item.name}</Link>
              )}
            </span>
          ))}
        </p>
      </nav>
      <section className="shell section section-tight">
        <ExploreTable
          rows={rows}
          indicatorId={indicatorId}
          indicatorName={indicator.name}
          indicatorUnit={indicator.unit}
          levelName={levelName}
          levelLabelPlural={level.label}
          nationalValue={nationalValue}
        />
      </section>
    </div>
  );
}
