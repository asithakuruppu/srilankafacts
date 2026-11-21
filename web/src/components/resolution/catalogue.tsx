"use client";

import { useState } from "react";

import { filterRows, formatMetres, shownAs, type TierFilter } from "@/lib/atlas/resolution";
import type { ResolutionEntry } from "@/lib/atlas/types";

const FILTERS: [TierFilter, string][] = [
  ["all", "All datasets"],
  ["finer", "Finer than GN"],
  ["held", "Finer in the source, shown only at GN or not yet integrated"],
  ["gn", "GN"],
];

export default function ResolutionCatalogue({ rows }: { rows: ResolutionEntry[] }) {
  const [filter, setFilter] = useState<TierFilter>("all");
  const shown = filterRows(rows, filter);
  return (
    <div className="resolution-catalogue">
      <label className="resolution-filter">
        <span>Show</span>
        <select value={filter} onChange={(event) => setFilter(event.target.value as TierFilter)}>
          {FILTERS.map(([id, label]) => (
            <option key={id} value={id}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <p className="muted" aria-live="polite">
        {shown.length} of {rows.length} datasets, finest first.
      </p>
      <div className="table-scroll">
        <table>
          <caption className="visually-hidden">Native resolution of each dataset</caption>
          <thead>
            <tr>
              <th scope="col">Dataset</th>
              <th scope="col">Native resolution</th>
              <th scope="col">Information unit</th>
              <th scope="col">Shown today as</th>
              <th scope="col">Status</th>
              <th scope="col">Rights</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((row) => (
              <tr key={row.dataset_id}>
                <th scope="row">
                  {row.landing_page ? <a href={row.landing_page}>{row.title}</a> : row.title}
                  <br />
                  <small className="muted">{row.source_name ?? row.dataset_id}</small>
                </th>
                <td>{formatMetres(row)}</td>
                <td>{row.information_unit ?? "not recorded"}</td>
                <td>{shownAs(row)}</td>
                <td>{row.status === "active" ? "In the platform" : "Not yet integrated"}</td>
                <td>{row.use === "any" ? row.rights_status : `${row.rights_status}, ${row.use.replace("_", "-")}`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
