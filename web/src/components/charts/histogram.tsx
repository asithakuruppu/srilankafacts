import { formatValue } from "@/lib/format";
import { histogramBins } from "@/lib/hierarchy";

type Props = {
  values: number[];
  unit: string;
  decimals?: number;
  /** Value of the selected area, marked on the axis. */
  marker?: number | null;
  label: string;
};

const W = 720;
const H = 170;
const PAD = { l: 34, r: 10, t: 10, b: 30 };

/** Equal-width histogram of child values; each bar's count is printed above it. */
export default function Histogram({ values, unit, decimals, marker, label }: Props) {
  const bins = histogramBins(values);
  if (bins.length === 0) {
    return null;
  }
  const maxCount = Math.max(...bins.map((b) => b.count));
  const lo = bins[0].from;
  const hi = bins[bins.length - 1].to;
  const plotW = W - PAD.l - PAD.r;
  const plotH = H - PAD.t - PAD.b;
  const bw = plotW / bins.length;
  const mx =
    marker !== null && marker !== undefined && hi > lo
      ? PAD.l + ((marker - lo) / (hi - lo)) * plotW
      : null;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={label} className="chart-svg">
      <line x1={PAD.l} x2={W - PAD.r} y1={H - PAD.b} y2={H - PAD.b} className="chart-axis" />
      {bins.map((b, i) => {
        const h = (b.count / maxCount) * plotH;
        return (
          <g key={b.from}>
            <rect
              x={PAD.l + i * bw + 1}
              y={H - PAD.b - h}
              width={bw - 2}
              height={h}
              className="cx-bar"
            />
            <text x={PAD.l + i * bw + bw / 2} y={H - PAD.b - h - 3} textAnchor="middle" className="chart-value">
              {b.count}
            </text>
          </g>
        );
      })}
      <text x={PAD.l} y={H - 10} className="chart-label">
        {formatValue(lo, unit, decimals)}
      </text>
      <text x={W - PAD.r} y={H - 10} textAnchor="end" className="chart-label">
        {formatValue(hi, unit, decimals)}
      </text>
      {mx !== null ? (
        <line x1={mx} x2={mx} y1={PAD.t} y2={H - PAD.b} className="chart-ref" />
      ) : null}
    </svg>
  );
}
