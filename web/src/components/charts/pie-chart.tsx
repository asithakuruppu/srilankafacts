import type { Slice } from "@/lib/composition";
import { formatNumber } from "@/lib/format";

// Categorical colours that keep 3:1 contrast against both the light and dark surfaces.
export const PIE_COLOURS = [
  "#3b63d6",
  "#d9822b",
  "#2a9d8f",
  "#b5446e",
  "#7a5fc4",
  "#7d9b2f",
  "#c0392b",
  "#2f8fbf",
];
const MERGED_COLOUR = "#8a90a0";

type Props = {
  slices: Slice[];
  selectedId?: string | null;
  onSelect?: (id: string) => void;
  label: string;
};

const SIZE = 220;
const R = 100;
const C = SIZE / 2;

function polar(angle: number): [number, number] {
  return [C + R * Math.sin(angle), C - R * Math.cos(angle)];
}

export function sliceColour(slices: Slice[], index: number): string {
  return slices[index].id === null ? MERGED_COLOUR : PIE_COLOURS[index % PIE_COLOURS.length];
}

/** Pie of parts of a whole; the legend beside it prints every value. */
export default function PieChart({ slices, selectedId, onSelect, label }: Props) {
  const total = slices.reduce((sum, slice) => sum + slice.value, 0);
  const arcs = slices.map((slice, index) => {
    const before = slices.slice(0, index).reduce((sum, item) => sum + item.value, 0);
    const share = total > 0 ? slice.value / total : 0;
    const start = total > 0 ? (before / total) * 2 * Math.PI : 0;
    return { slice, index, share, start, end: start + share * 2 * Math.PI };
  });
  return (
    <div className="pie">
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} role="img" aria-label={label} className="pie-svg">
        {arcs.map(({ slice, index, share, start, end }) => {
          const fill = sliceColour(slices, index);
          const active = slice.id !== null && slice.id === selectedId;
          const common = {
            fill,
            className: `pie-slice${active ? " pie-slice-active" : ""}${slice.id && onSelect ? " pie-slice-click" : ""}`,
            onClick: slice.id && onSelect ? () => onSelect(slice.id as string) : undefined,
          };
          const title = (
            <title>{`${slice.label}: ${formatNumber(slice.value, 1)}%`}</title>
          );
          if (share >= 0.9999) {
            return (
              <circle key={index} cx={C} cy={C} r={R} {...common}>
                {title}
              </circle>
            );
          }
          const [x1, y1] = polar(start);
          const [x2, y2] = polar(end);
          const large = end - start > Math.PI ? 1 : 0;
          return (
            <path
              key={index}
              d={`M ${C} ${C} L ${x1} ${y1} A ${R} ${R} 0 ${large} 1 ${x2} ${y2} Z`}
              {...common}
            >
              {title}
            </path>
          );
        })}
      </svg>
      <ul className="pie-legend">
        {slices.map((slice, index) => (
          <li key={slice.label} className={slice.id === selectedId ? "pie-legend-active" : ""}>
            <span className="pie-swatch" style={{ background: sliceColour(slices, index) }} />
            {slice.id && onSelect ? (
              <button type="button" className="link-button" onClick={() => onSelect(slice.id as string)}>
                {slice.label}
              </button>
            ) : (
              <span>
                {slice.label}
                {slice.merged ? ` (${slice.merged})` : ""}
              </span>
            )}
            <strong>{formatNumber(slice.value, 1)}%</strong>
          </li>
        ))}
      </ul>
    </div>
  );
}
