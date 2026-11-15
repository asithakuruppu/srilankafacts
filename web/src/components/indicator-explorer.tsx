"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import BarChart from "@/components/charts/bar-chart";
import Histogram from "@/components/charts/histogram";
import StatTile from "@/components/stat-tile";
import { formatNumber, formatValue } from "@/lib/format";
import {
  type Hierarchy,
  LEVEL_SINGULAR,
  childLevelName,
  childrenOf,
  pathTo,
  rankOf,
} from "@/lib/hierarchy";
import { type LevelValue, loadHierarchy, loadLevelValues } from "@/lib/indicator-data";

export type ExplorerIndicator = {
  id: string;
  name: string;
  definition: string;
  unit: string;
  decimals: number;
  measureType: string;
  levels: string[];
  group: string;
};

const LEVEL_FILE = ["country", "province", "district", "ds", "gn"];
const DEFAULT_AREA = "LK";

type Loaded = { key: string; values: Record<string, Map<string, LevelValue>> };

export default function IndicatorExplorer({ indicators }: { indicators: ExplorerIndicator[] }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  const indicatorId = indicators.some((item) => item.id === params.get("i"))
    ? (params.get("i") as string)
    : (indicators.find((item) => item.id === "population_total") ?? indicators[0]).id;
  const areaId = params.get("a") || DEFAULT_AREA;
  const indicator = indicators.find((item) => item.id === indicatorId) ?? indicators[0];

  const [hierarchy, setHierarchy] = useState<Hierarchy | null>(null);
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadHierarchy()
      .then(setHierarchy)
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Load failed."));
  }, []);

  const path = useMemo(
    () => (hierarchy ? pathTo(hierarchy, areaId) : []),
    [hierarchy, areaId],
  );
  const area = path.at(-1) ?? null;
  const parent = path.length > 1 ? path[path.length - 2] : null;
  const childLevel = area ? childLevelName(area.level) : null;
  const children = useMemo(
    () => (hierarchy && area ? childrenOf(hierarchy, area.id) : []),
    [hierarchy, area],
  );

  const wanted = useMemo(() => {
    if (!area) {
      return [];
    }
    return [
      ...new Set(
        [0, area.level, area.level - 1, area.level + 1]
          .filter((level) => level >= 0 && level <= 4)
          .map((level) => LEVEL_FILE[level]),
      ),
    ].filter((level) => indicator.levels.includes(level));
  }, [area, indicator.levels]);
  const dataKey = `${indicatorId}|${wanted.join(",")}`;
  const ready = loaded?.key === dataKey;

  useEffect(() => {
    let live = true;
    Promise.all(wanted.map((level) => loadLevelValues(indicatorId, level)))
      .then((maps) => {
        if (live) {
          setLoaded({ key: dataKey, values: Object.fromEntries(wanted.map((l, i) => [l, maps[i]])) });
          setError(null);
        }
      })
      .catch((caught) => {
        if (live) {
          setError(caught instanceof Error ? caught.message : "Data failed to load.");
        }
      });
    return () => {
      live = false;
    };
  }, [dataKey, indicatorId, wanted]);

  function go(next: { i?: string; a?: string }) {
    const query = new URLSearchParams();
    query.set("i", next.i ?? indicatorId);
    const a = next.a ?? areaId;
    if (a !== DEFAULT_AREA) {
      query.set("a", a);
    }
    router.replace(`${pathname}?${query.toString()}`, { scroll: false });
  }

  const valueOf = (level: number | null, id: string | null): number | null => {
    if (!ready || level === null || !id) {
      return null;
    }
    return loaded.values[LEVEL_FILE[level]]?.get(id)?.value ?? null;
  };

  const ownValue = area ? valueOf(area.level, area.id) : null;
  const parentValue = parent ? valueOf(parent.level, parent.id) : null;
  const nationalValue = valueOf(0, DEFAULT_AREA);

  const childRows = useMemo(() => {
    if (!ready || !area || !childLevel) {
      return [];
    }
    const map = loaded.values[childLevel];
    return children
      .map((child) => ({ id: child.id, name: child.name, value: map?.get(child.id)?.value ?? null }))
      .filter((row): row is { id: string; name: string; value: number } => row.value !== null);
  }, [ready, loaded, area, childLevel, children]);

  const siblingRows = useMemo(() => {
    if (!ready || !area || !parent || !hierarchy) {
      return [];
    }
    const map = loaded.values[LEVEL_FILE[area.level]];
    return childrenOf(hierarchy, parent.id)
      .map((node) => ({ id: node.id, value: map?.get(node.id)?.value ?? null }))
      .filter((row): row is { id: string; value: number } => row.value !== null);
  }, [ready, loaded, area, parent, hierarchy]);

  const rank = area ? rankOf(siblingRows, area.id) : null;
  const dec = indicator.decimals;
  const isCount = indicator.measureType === "count";
  const hasGn = indicator.levels.includes("gn");
  const childAvailable = childLevel !== null && indicator.levels.includes(childLevel);
  const missing = children.length - childRows.length;
  const references = !isCount
    ? [
        ...(nationalValue !== null ? [{ label: "Sri Lanka", value: nationalValue }] : []),
      ]
    : [];

  // One select per depth: the chosen area at that depth, listing the siblings under its parent.
  const selects = [] as { depth: number; options: { id: string; name: string }[]; value: string }[];
  if (hierarchy) {
    for (let depth = 1; depth <= 4; depth += 1) {
      const above = path[depth - 1];
      if (!above) {
        break;
      }
      selects.push({
        depth,
        options: childrenOf(hierarchy, above.id).map((n) => ({ id: n.id, name: n.name })),
        value: path[depth]?.id ?? "",
      });
    }
  }

  return (
    <section className="indicator-explorer" aria-label="Indicator drill-down">
      <div className="explore-controls ix-controls" role="group" aria-label="Choose indicator and area">
        <label className="ix-wide">
          <span>Indicator</span>
          <select value={indicatorId} onChange={(event) => go({ i: event.target.value })}>
            {[...new Set(indicators.map((item) => item.group))].map((group) => (
              <optgroup key={group} label={group}>
                {indicators
                  .filter((item) => item.group === group)
                  .map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
              </optgroup>
            ))}
          </select>
        </label>
        {selects.map(({ depth, options, value }) => {
          const disabled = depth === 4 && !hasGn;
          return (
            <label key={depth}>
              <span>{LEVEL_SINGULAR[depth]}</span>
              <select
                value={value}
                disabled={disabled}
                onChange={(event) => go({ a: event.target.value || path[depth - 1].id })}
              >
                <option value="">All ({options.length})</option>
                {options.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.name}
                  </option>
                ))}
              </select>
            </label>
          );
        })}
      </div>

      {error ? (
        <p className="notice notice-error" role="alert">
          {error}
        </p>
      ) : null}
      {!hierarchy || !area ? <p className="muted">Loading areas…</p> : null}

      {area ? (
        <div className="ix-body">
          <p className="ix-crumbs">
            {path.map((node, index) => (
              <span key={node.id}>
                {index > 0 ? " › " : ""}
                {index < path.length - 1 ? (
                  <button type="button" className="link-button" onClick={() => go({ a: node.id })}>
                    {node.name}
                  </button>
                ) : (
                  <strong>{node.name}</strong>
                )}
              </span>
            ))}
          </p>
          <h2>{indicator.name}</h2>
          <p className="muted small">{indicator.definition}</p>

          <div className="stat-grid ix-stats">
            <StatTile
              label={`${LEVEL_SINGULAR[area.level]}: ${area.name}`}
              value={ready ? formatValue(ownValue, indicator.unit, dec) : "…"}
              note="2024 census"
            />
            {parent ? (
              <StatTile
                label={parent.name}
                value={ready ? formatValue(parentValue, indicator.unit, dec) : "…"}
                note="Parent area"
              />
            ) : null}
            {area.level > 0 ? (
              <StatTile
                label="Sri Lanka"
                value={ready ? formatValue(nationalValue, indicator.unit, dec) : "…"}
                note="National"
              />
            ) : null}
            {rank !== null ? (
              <StatTile
                label={`Rank among ${LEVEL_SINGULAR[area.level].toLowerCase()}s in ${parent?.name ?? ""}`}
                value={`${rank} of ${siblingRows.length}`}
                note="1 = highest value"
              />
            ) : null}
          </div>

          {childLevel === null ? (
            <p className="muted">
              This is the finest level. <Link href={`/place/${area.id}`}>Open the full place page</Link>.
            </p>
          ) : !childAvailable ? (
            <p className="notice">
              This indicator is not published at {LEVEL_SINGULAR[area.level + 1].toLowerCase()} level,
              so there is nothing finer to show here. Choose a larger area or another indicator.
            </p>
          ) : !ready ? (
            <p className="muted">Loading {LEVEL_SINGULAR[area.level + 1].toLowerCase()} values…</p>
          ) : (
            <>
              <h3>
                {LEVEL_SINGULAR[area.level + 1]}s in {area.name}{" "}
                <small className="muted">· {childRows.length} with values</small>
              </h3>
              <p className="muted small">
                Click a bar to drill into that area.
                {references.length > 0 ? " The dashed line is the national value." : ""}
                {isCount
                  ? " Counts partly reflect how many people or homes are in a place; compare with care."
                  : ""}
              </p>
              <BarChart
                data={childRows}
                unit={indicator.unit}
                decimals={dec}
                references={references}
                label={`${indicator.name} by ${LEVEL_SINGULAR[area.level + 1].toLowerCase()} in ${area.name}`}
                onSelect={(id) => go({ a: id })}
              />
              {childRows.length > 2 ? (
                <>
                  <h3>Distribution</h3>
                  <Histogram
                    values={childRows.map((row) => row.value)}
                    unit={indicator.unit}
                    decimals={dec}
                    marker={ownValue}
                    label={`Distribution of ${indicator.name} across ${LEVEL_SINGULAR[area.level + 1].toLowerCase()}s in ${area.name}; bar labels are counts of areas`}
                  />
                </>
              ) : null}
              {missing > 0 ? (
                <p className="muted small">
                  {formatNumber(missing)} of {formatNumber(children.length)} areas have no published
                  value for this indicator and are not charted.
                </p>
              ) : null}
              <details className="ix-table">
                <summary>Show as table</summary>
                <table>
                  <thead>
                    <tr>
                      <th scope="col">{LEVEL_SINGULAR[area.level + 1]}</th>
                      <th scope="col">Value ({indicator.unit}), 2024</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...childRows]
                      .sort((a, b) => b.value - a.value)
                      .map((row) => (
                        <tr key={row.id}>
                          <td>
                            <Link href={`/place/${row.id}`}>{row.name}</Link>
                          </td>
                          <td>{formatValue(row.value, indicator.unit, dec)}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </details>
            </>
          )}
          <p className="muted small">
            Source: DCS Census 2024, release data.{" "}
            <Link href={`/indicator/${indicator.id}`}>Definition, map and limits of this measure</Link>
            {childLevel === "gn"
              ? ". GN values are taken as published; some GN divisions could not be matched to the geography spine and are absent."
              : "."}
          </p>
        </div>
      ) : null}
    </section>
  );
}
