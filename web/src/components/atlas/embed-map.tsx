"use client";

import { useSearchParams } from "next/navigation";
import { useCallback, useMemo, useState } from "react";

import AtlasMap from "@/components/atlas/atlas-map";
import { classIndex, quantileBreaks } from "@/lib/atlas/context";
import { loadLevelValues, loadUnits } from "@/lib/atlas/data";
import { MAP_LEVELS, rampFor, SEQUENTIAL, type AdminMapLevel } from "@/lib/atlas/scale";
import { LEVEL_PLURAL, type AtlasIndicator } from "@/lib/atlas/types";
import { useLoaded } from "@/lib/atlas/use-loaded";
import { useTheme } from "@/lib/atlas/use-theme";
import { formatValue } from "@/lib/format";

/** A chrome-free map of one census indicator at one level, for embedding with attribution. */
export default function EmbedMap({ indicators, release, citation }: { indicators: AtlasIndicator[]; release: string; citation: string }) {
  const params = useSearchParams();
  const theme = useTheme();
  const indicator = indicators.find((item) => item.id === params.get("ind")) ?? indicators.find((item) => item.id === "population_density") ?? indicators[0];
  const asked = params.get("level") as AdminMapLevel | null;
  const level: AdminMapLevel =
    asked && MAP_LEVELS.includes(asked) && indicator?.levels.includes(asked)
      ? asked
      : (["district", "ds", "province"] as AdminMapLevel[]).find((l) => indicator?.levels.includes(l)) ?? "district";
  const units = useLoaded(loadUnits, "units");
  const values = useLoaded(indicator ? () => loadLevelValues(indicator.id, level) : null, `${indicator?.id}|${level}`);
  const [error, setError] = useState<string | null>(null);

  const { colors, entries } = useMemo(() => {
    if (!values || !indicator) {
      return { colors: null, entries: [] as { color: string; label: string }[] };
    }
    const ramp = rampFor(SEQUENTIAL, theme);
    const breaks = quantileBreaks([...values.values()], 5);
    const palette = breaks.length === 4 ? ramp : ramp.filter((_, i) => i % 2 === 0).slice(0, breaks.length + 1);
    const map = new Map<string, string>();
    for (const [id, value] of values) {
      map.set(id, palette[Math.min(classIndex(value, breaks), palette.length - 1)]);
    }
    const fmt = (value: number) => formatValue(value, indicator.unit, indicator.decimals);
    return {
      colors: map,
      entries: palette.slice(0, breaks.length + 1).map((color, i) => ({
        color,
        label: breaks.length === 0 ? "all equal" : i === 0 ? `under ${fmt(breaks[0])}` : i === breaks.length ? `${fmt(breaks[i - 1])}+` : `${fmt(breaks[i - 1])}–${fmt(breaks[i])}`,
      })),
    };
  }, [indicator, theme, values]);

  const nameOf = useCallback((id: string) => units?.[id]?.n ?? id, [units]);
  const parentOf = useCallback((id: string) => units?.[id]?.p ?? null, [units]);
  const tooltip = useCallback(
    (id: string) => {
      const value = values?.get(id);
      return { title: nameOf(id), detail: value === undefined || !indicator ? "No value" : formatValue(value, indicator.unit, indicator.decimals) };
    },
    [indicator, nameOf, values],
  );
  const link = `/?ind=${indicator?.id ?? ""}&level=${level}`;

  return (
    <div className="embed-frame">
      <AtlasMap
        theme={theme}
        level={level}
        colors={colors}
        selected={null}
        dimOutside={false}
        highlight={[]}
        units={units}
        edLabels={null}
        nameOf={nameOf}
        parentOf={parentOf}
        tooltip={tooltip}
        inset={{ right: 0, bottom: 120 }}
        onReady={() => undefined}
        onZoom={() => undefined}
        onSelect={() => undefined}
        onError={setError}
      />
      <div className="embed-legend" data-testid="embed-legend">
        <p>
          <strong>{indicator?.short}</strong> · {LEVEL_PLURAL[level]} · Census 2024
        </p>
        <ul>
          {entries.map((entry) => (
            <li key={entry.label}>
              <i style={{ background: entry.color }} aria-hidden="true" />
              {entry.label}
            </li>
          ))}
        </ul>
        <p className="embed-credit">
          <a href={link} target="_blank" rel="noopener">
            Sri Lanka Facts
          </a>{" "}
          · {release} · Source: Department of Census and Statistics, Census 2024 · Non-commercial use · Private preview
        </p>
        {error ? <p role="alert">{error}</p> : null}
      </div>
      <span className="visually-hidden">{citation}</span>
    </div>
  );
}
