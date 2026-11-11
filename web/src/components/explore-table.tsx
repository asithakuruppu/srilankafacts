import Link from "next/link";

import { MAX_TABLE_ROWS, type ExploreRow } from "@/lib/explore-levels";
import { formatNumber, formatValue, levelLabel } from "@/lib/format";

/** The explore table. No hooks, so it renders on the server and inside the client explorer. */
export default function ExploreTable({
  rows,
  indicatorId,
  indicatorName,
  indicatorUnit,
  levelName,
  levelLabelPlural,
  nationalValue,
  open = true,
}: {
  rows: ExploreRow[];
  indicatorId: string;
  indicatorName: string;
  indicatorUnit: string;
  levelName: string;
  levelLabelPlural: string;
  nationalValue: number | null;
  open?: boolean;
}) {
  return (
    <details className="table-details" open={open}>
      <summary>
        View as table ({formatNumber(rows.length)} areas
        {rows.length > MAX_TABLE_ROWS ? `, showing the highest ${MAX_TABLE_ROWS}` : ""})
      </summary>
      <div className="table-scroll">
        <table>
          <caption className="visually-hidden">
            {indicatorName} by {levelLabelPlural.toLowerCase()}, sorted from highest to lowest
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
                <td className="numeric">{formatValue(row.value, row.unit || indicatorUnit)}</td>
                <td className="numeric">{formatValue(nationalValue, indicatorUnit)}</td>
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
          The table is capped at {formatNumber(MAX_TABLE_ROWS)} rows to keep the page usable. The
          complete file is at <code>/api/v1/indicators/{indicatorId}/{levelName}.json</code>.
        </p>
      ) : null}
    </details>
  );
}
