"use client";

import { formatValue } from "@/lib/format";

export type BarDatum = { id: string; name: string; value: number };

type Props = {
  data: BarDatum[];
  unit: string;
  decimals?: number;
  /** Vertical reference lines, for example the national value. */
  references?: { label: string; value: number }[];
  highlightId?: string | null;
  onSelect?: (id: string) => void;
  /** Accessible description of what the chart shows. */
  label: string;
};

const ROW = 24;
const LABEL_W = 170;
const VALUE_W = 92;
const WIDTH = 720;

/** Ranked horizontal bars. Rows are buttons so they can be keyboard-drilled. */
export default function BarChart({
  data,
  unit,
  decimals,
  references = [],
  highlightId,
  onSelect,
  label,
}: Props) {
  const sorted = [...data].sort((a, b) => b.value - a.value || a.name.localeCompare(b.name));
  const max = Math.max(0, ...sorted.map((d) => d.value), ...references.map((r) => r.value));
  const plotW = WIDTH - LABEL_W - VALUE_W;
  const x = (v: number) => (max === 0 ? 0 : (v / max) * plotW);
  const height = sorted.length * ROW + 6;

  return (
    <div className="chart-scroll">
      <svg
        viewBox={`0 0 ${WIDTH} ${height}`}
        width="100%"
        role="img"
        aria-label={label}
        className="chart-svg"
        style={{ minWidth: 520 }}
      >
        {sorted.map((d, i) => {
          const y = i * ROW + 3;
          const active = d.id === highlightId;
          const clickable = Boolean(onSelect);
          return (
            <g
              key={d.id}
              className={`cx-g${clickable ? " cx-g-click" : ""}${active ? " cx-g-active" : ""}`}
              onClick={clickable ? () => onSelect?.(d.id) : undefined}
            >
              <rect x={0} y={y} width={WIDTH} height={ROW - 2} className="cx-hit" />
              <text x={LABEL_W - 8} y={y + 15} textAnchor="end" className="chart-label">
                {d.name.length > 24 ? `${d.name.slice(0, 23)}…` : d.name}
              </text>
              <rect
                x={LABEL_W}
                y={y + 3}
                width={Math.max(1, x(d.value))}
                height={ROW - 8}
                className="cx-bar"
              />
              <text x={LABEL_W + x(d.value) + 6} y={y + 15} className="chart-value">
                {formatValue(d.value, unit, decimals)}
              </text>
            </g>
          );
        })}
        {references.map((ref) => (
          <g key={ref.label}>
            <line
              x1={LABEL_W + x(ref.value)}
              x2={LABEL_W + x(ref.value)}
              y1={0}
              y2={height}
              className="chart-ref"
            />
          </g>
        ))}
      </svg>
    </div>
  );
}
