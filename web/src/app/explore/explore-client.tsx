"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import MapView from "@/components/map-view";
import { type AreaDataset, fetchAreaDataset } from "@/lib/areas";
import { formatNumber, formatValue, levelLabel } from "@/lib/format";

type IndicatorOption = {
  id: string;
  name: string;
  unit: string;
  decimals: number;
  measureType: string;
};

type LevelOption = { name: string; boundary: number; label: string };

const LEVEL_DEFINITIONS: LevelOption[] = [
  { name: "province", boundary: 1, label: "Provinces" },
  { name: "district", boundary: 2, label: "Districts" },
  { name: "ds", boundary: 3, label: "DS divisions" },
  { name: "gn", boundary: 4, label: "GN divisions" },
];

const MAX_TABLE_ROWS = 500;

export default function ExploreClient({
  indicators,
  boundaryLevels,
  national,
}: {
  indicators: IndicatorOption[];
  boundaryLevels: number[];
  national: Record<string, number>;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const levels = LEVEL_DEFINITIONS.filter((level) => boundaryLevels.includes(level.boundary));
  const defaultIndicator =
    indicators.find((indicator) => indicator.id === "population_density")?.id ??
    indicators[0]?.id ??
    "population_total";
  const defaultLevel =
    levels.find((level) => level.name === "district")?.name ?? levels[0]?.name ?? "district";

  const [indicatorId, setIndicatorId] = useState(
    indicators.some((indicator) => indicator.id === params.get("indicator"))
      ? (params.get("indicator") as string)
      : defaultIndicator,
  );
  const [levelName, setLevelName] = useState(
    levels.some((level) => level.name === params.get("level"))
      ? (params.get("level") as string)
      : defaultLevel,
  );
  const [compare, setCompare] = useState(params.get("compare") === "1");
  const [dataset, setDataset] = useState<{ key: string; value: AreaDataset } | null>(null);
  const [error, setError] = useState<{ key: string; message: string } | null>(null);
  const [copied, setCopied] = useState(false);

  const indicator = indicators.find((item) => item.id === indicatorId) ?? indicators[0];
  const level = levels.find((item) => item.name === levelName) ?? levels[0];
  const dataKey = `${indicatorId}|${levelName}`;
  const loading = dataset?.key !== dataKey;

  useEffect(() => {
    const controller = new AbortController();
    fetchAreaDataset(indicatorId, levelName, level.boundary, controller.signal)
      .then((next) => {
        setDataset({ key: dataKey, value: next });
      })
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setError({
            key: dataKey,
            message: caught instanceof Error ? caught.message : "Data failed to load.",
          });
        }
      });
    return () => controller.abort();
  }, [dataKey, indicatorId, level.boundary, levelName]);

  const activeDataset = dataset?.key === dataKey ? dataset.value : null;
  const activeError = error?.key === dataKey ? error.message : null;

  function update(next: {
    indicator?: string;
    level?: string;
    compare?: boolean;
  }) {
    const query = new URLSearchParams();
    query.set("indicator", next.indicator ?? indicatorId);
    query.set("level", next.level ?? levelName);
    const nextCompare = next.compare ?? compare;
    if (nextCompare) {
      query.set("compare", "1");
    }
    router.replace(`${pathname}?${query.toString()}`, { scroll: false });
  }

  const rows = useMemo(() => {
    if (!activeDataset) {
      return [];
    }
    return [...activeDataset.rows]
      .filter((row) => row.value !== null)
      .sort((a, b) => (b.value ?? 0) - (a.value ?? 0));
  }, [activeDataset]);

  const nationalValue = national[indicatorId] ?? null;

  return (
    <div className="explore">
      <div className="shell explore-head">
        <div>
          <p className="eyebrow">Explore</p>
          <h1>Census Atlas 2024</h1>
          <p className="lede">
            Colour one indicator across the country, switch levels, and open any area for its
            full record. Every state is in the URL, so a view can be shared or bookmarked.
          </p>
        </div>
        <div className="explore-controls" role="group" aria-label="Map controls">
          <label>
            <span>Indicator</span>
            <select
              value={indicatorId}
              onChange={(event) => {
                setIndicatorId(event.target.value);
                update({ indicator: event.target.value });
              }}
            >
              {indicators.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Level</span>
            <select
              value={levelName}
              onChange={(event) => {
                setLevelName(event.target.value);
                update({ level: event.target.value });
              }}
            >
              {levels.map((item) => (
                <option key={item.name} value={item.name}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Period</span>
            <select value="2024" disabled>
              <option value="2024">2024</option>
            </select>
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={compare}
              onChange={(event) => {
                setCompare(event.target.checked);
                update({ compare: event.target.checked });
              }}
            />
            <span>Difference from national</span>
          </label>
          <button
            type="button"
            className="button button-quiet button-small"
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(window.location.href);
                setCopied(true);
                window.setTimeout(() => setCopied(false), 1800);
              } catch {
                setCopied(false);
              }
            }}
          >
            {copied ? "Link copied" : "Copy link"}
          </button>
        </div>
      </div>

      <div className="shell explore-body">
        <div className="explore-map-wrap">
          {activeError ? (
            <p className="notice notice-error" role="alert">
              {activeError}
            </p>
          ) : null}
          {loading ? <p className="map-loading">Loading {level.label.toLowerCase()}…</p> : null}
          <MapView
            indicatorId={indicatorId}
            levelName={levelName}
            boundaryLevel={level.boundary}
            unit={indicator?.unit ?? ""}
            decimals={indicator?.decimals}
            nationalValue={nationalValue}
            compare={compare}
            preloaded={activeDataset}
            className="explore-map"
          />
        </div>

        <aside className="explore-panel">
          <p className="panel-kicker">
            {level.label} · {rows.length.toLocaleString("en-LK")} with values
          </p>
          <h2>{indicator?.name}</h2>
          <p className="muted">
            National value: <strong>{formatValue(nationalValue, indicator?.unit ?? "")}</strong>
          </p>
          <p className="small muted">
            {indicator?.measureType === "count"
              ? "Counts partly reflect how many people or homes are in a place. Compare with care."
              : "Rates are computed from counts. Small denominators are unstable; see the methods page."}
          </p>
          <p className="small muted">
            Click an area on the map to open its place page. The table below is the accessible
            alternative to the map.
          </p>
          <Link
            className="button button-quiet button-small"
            href={`/indicator/${indicatorId}`}
          >
            About this indicator
          </Link>
        </aside>
      </div>

      <section className="shell section section-tight">
        <details className="table-details" open={levelName !== "gn"}>
          <summary>
            View as table ({formatNumber(rows.length)} areas
            {rows.length > MAX_TABLE_ROWS ? `, showing the highest ${MAX_TABLE_ROWS}` : ""})
          </summary>
          <div className="table-scroll">
            <table>
              <caption className="visually-hidden">
                {indicator?.name} by {level.label.toLowerCase()}, sorted from highest to
                lowest
              </caption>
              <thead>
                <tr>
                  <th scope="col">Area</th>
                  <th scope="col">Level</th>
                  <th scope="col">Value</th>
                  <th scope="col">National</th>
                  <th scope="col">Source</th>
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, MAX_TABLE_ROWS).map((row) => (
                  <tr key={row.id}>
                    <th scope="row">
                      <Link href={`/place/${row.id}`}>{row.name}</Link>
                    </th>
                    <td>{levelLabel(row.levelName)}</td>
                    <td className="numeric">
                      {formatValue(row.value, row.unit || indicator?.unit || "")}
                    </td>
                    <td className="numeric">
                      {formatValue(nationalValue, indicator?.unit ?? "")}
                    </td>
                    <td>
                      <Link href={`/place/${row.id}#data`}>record</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {rows.length > MAX_TABLE_ROWS ? (
            <p className="muted small">
              The table is capped at {formatNumber(MAX_TABLE_ROWS)} rows to keep the page
              usable. The complete file is at{" "}
              <code>/api/v1/indicators/{indicatorId}/{levelName}.json</code>.
            </p>
          ) : null}
        </details>
      </section>
    </div>
  );
}
