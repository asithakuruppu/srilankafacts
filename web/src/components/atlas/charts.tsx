/** Small hand-written SVG charts for the atlas panel (D-035: no chart dependency). */

import { histogram } from "@/lib/atlas/context";

export type Marker = {
  key: "place" | "neighbours" | "parent" | "similar" | "country";
  label: string;
  value: number;
};

const MARKER_Y: Record<Marker["key"], number> = {
  place: 0,
  neighbours: 1,
  parent: 2,
  similar: 3,
  country: 4,
};

/**
 * One value against its four references, on the distribution of every unit at the level.
 * The grey bars are a histogram of all units; each marker sits at its value on the same axis.
 */
export function ContextStrip({
  values,
  markers,
  format,
  caption,
}: {
  values: number[];
  markers: Marker[];
  format: (value: number) => string;
  caption: string;
}) {
  const width = 340;
  const top = 6;
  const plot = 44;
  const { counts, min, max } = histogram(values, 34);
  const span = max - min || 1;
  const x = (value: number) => 4 + ((Math.min(Math.max(value, min), max) - min) / span) * (width - 8);
  const peak = Math.max(...counts, 1);
  const bar = (width - 8) / Math.max(counts.length, 1);
  return (
    <figure className="strip">
      <svg viewBox={`0 0 ${width} 76`} role="img" aria-label={caption}>
        {counts.map((count, i) => (
          <rect
            key={i}
            className="strip-bar"
            x={4 + i * bar + 0.5}
            y={top + plot - (count / peak) * plot}
            width={Math.max(bar - 1, 0.5)}
            height={(count / peak) * plot}
          />
        ))}
        <line className="strip-axis" x1={4} x2={width - 4} y1={top + plot + 0.5} y2={top + plot + 0.5} />
        {markers
          .filter((marker) => marker.key !== "place")
          .map((marker) => (
            <g key={marker.key} className={`strip-mark strip-mark-${marker.key}`}>
              <line x1={x(marker.value)} x2={x(marker.value)} y1={top + 8 + MARKER_Y[marker.key] * 3} y2={top + plot + 5} />
              <circle cx={x(marker.value)} cy={top + plot + 5} r={3} />
            </g>
          ))}
        {markers
          .filter((marker) => marker.key === "place")
          .map((marker) => (
            <g key={marker.key} className="strip-mark strip-mark-place">
              <line x1={x(marker.value)} x2={x(marker.value)} y1={top - 2} y2={top + plot + 6} />
              <path
                d={`M${x(marker.value) - 5} ${top - 5} h10 l-5 6 z`}
              />
            </g>
          ))}
        <text className="strip-tick" x={4} y={72}>
          {format(min)}
        </text>
        <text className="strip-tick" x={width - 4} y={72} textAnchor="end">
          {format(max)}
        </text>
      </svg>
      <figcaption className="visually-hidden">{caption}</figcaption>
    </figure>
  );
}

/** Position of a place on one profile axis, against the range of all places. */
export function AxisBar({
  value,
  other,
  min,
  max,
}: {
  value: number;
  other?: number | null;
  min: number;
  max: number;
}) {
  const width = 200;
  const span = max - min || 1;
  const x = (v: number) => 2 + ((v - min) / span) * (width - 4);
  const zero = x(0);
  return (
    <svg className="axisbar" viewBox={`0 0 ${width} 14`} aria-hidden="true">
      <line className="axisbar-track" x1={2} x2={width - 2} y1={7} y2={7} />
      <line className="axisbar-zero" x1={zero} x2={zero} y1={2} y2={12} />
      <line className="axisbar-fill" x1={zero} x2={x(value)} y1={7} y2={7} />
      {other !== undefined && other !== null ? (
        <circle className="axisbar-other" cx={x(other)} cy={7} r={3.2} />
      ) : null}
      <circle className="axisbar-dot" cx={x(value)} cy={7} r={3.6} />
    </svg>
  );
}

export type ScatterPoint = { id: string; x: number; y: number };

/**
 * The similarity map: every DS division on the first two profile axes. A projection for
 * orientation only; distances are always measured on all retained axes.
 */
export function Scatter({
  points,
  selected,
  compare,
  near,
  onPick,
  nameOf,
}: {
  points: ScatterPoint[];
  selected: string | null;
  compare: string | null;
  near: Set<string>;
  onPick: (id: string) => void;
  nameOf: (id: string) => string;
}) {
  const size = 320;
  const pad = 10;
  const xs = points.map((p) => p.x);
  const ys = points.map((p) => p.y);
  const [minX, maxX, minY, maxY] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const sx = (v: number) => pad + ((v - minX) / (maxX - minX || 1)) * (size - 2 * pad);
  const sy = (v: number) => size * 0.72 - pad - ((v - minY) / (maxY - minY || 1)) * (size * 0.72 - 2 * pad);
  const rank = (p: ScatterPoint) => (p.id === selected ? 3 : p.id === compare ? 2 : near.has(p.id) ? 1 : 0);
  const ordered = [...points].sort((a, b) => rank(a) - rank(b));
  return (
    <svg
      className="scatter"
      viewBox={`0 0 ${size} ${size * 0.72}`}
      role="img"
      aria-label="DS divisions on the first two profile axes; places near each other have similar profiles"
    >
      <line className="scatter-zero" x1={sx(0)} x2={sx(0)} y1={0} y2={size * 0.72} />
      <line className="scatter-zero" x1={0} x2={size} y1={sy(0)} y2={sy(0)} />
      {ordered.map((point) => {
        const state =
          point.id === selected
            ? "is-selected"
            : point.id === compare
              ? "is-compare"
              : near.has(point.id)
                ? "is-near"
                : "";
        return (
          <circle
            key={point.id}
            className={`scatter-dot ${state}`}
            cx={sx(point.x)}
            cy={sy(point.y)}
            r={state ? 4.2 : 2.2}
            onClick={() => onPick(point.id)}
          >
            <title>{nameOf(point.id)}</title>
          </circle>
        );
      })}
    </svg>
  );
}

/** Census population series as a line with a dot per census. */
export function Series({
  points,
  format,
}: {
  points: { year: number; value: number }[];
  format: (value: number) => string;
}) {
  const width = 340;
  const height = 120;
  const pad = { l: 6, r: 6, t: 10, b: 20 };
  if (points.length < 2) {
    return null;
  }
  const minYear = points[0].year;
  const maxYear = points[points.length - 1].year;
  const maxValue = Math.max(...points.map((p) => p.value));
  const x = (year: number) => pad.l + ((year - minYear) / (maxYear - minYear)) * (width - pad.l - pad.r);
  const y = (value: number) => height - pad.b - (value / maxValue) * (height - pad.t - pad.b);
  const path = points.map((p, i) => `${i === 0 ? "M" : "L"}${x(p.year).toFixed(1)} ${y(p.value).toFixed(1)}`).join(" ");
  const first = points[0];
  const last = points[points.length - 1];
  return (
    <svg
      className="series"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={`Population at each census from ${first.year} (${format(first.value)}) to ${last.year} (${format(last.value)})`}
    >
      <line className="series-axis" x1={pad.l} x2={width - pad.r} y1={height - pad.b} y2={height - pad.b} />
      <path className="series-line" d={path} />
      {points.map((p) => (
        <circle key={p.year} className="series-dot" cx={x(p.year)} cy={y(p.value)} r={2.4}>
          <title>{`${p.year}: ${format(p.value)}`}</title>
        </circle>
      ))}
      <text className="strip-tick" x={pad.l} y={height - 5}>
        {first.year}
      </text>
      <text className="strip-tick" x={width - pad.r} y={height - 5} textAnchor="end">
        {last.year}
      </text>
    </svg>
  );
}

/** Horizontal share bar (0 to 1). */
export function ShareBar({ share, tone = "accent" }: { share: number; tone?: "accent" | "muted" }) {
  return (
    <span className={`sharebar sharebar-${tone}`} aria-hidden="true">
      <span style={{ width: `${Math.max(0, Math.min(1, share)) * 100}%` }} />
    </span>
  );
}
