"use client";

import type { AsyncDuckDB, AsyncDuckDBConnection } from "@duckdb/duckdb-wasm";
import { useEffect, useRef, useState } from "react";

const PRESETS: { label: string; sql: string }[] = [
  {
    label: "Population by district",
    sql: `SELECT g.name_en AS district, o.value AS persons, o.source_locator
FROM census o JOIN geographies g USING (geography_id)
WHERE o.indicator_id = 'population_total' AND g.level = 2
ORDER BY persons DESC;`,
  },
  {
    label: "GN divisions in Colombo DS with most households",
    sql: `SELECT g.name_en AS gn, o.value AS households
FROM topics o JOIN geographies g USING (geography_id)
WHERE o.indicator_id = 'households_total' AND g.parent_id = 'LK1103'
ORDER BY households DESC LIMIT 20;`,
  },
  {
    label: "Indicators and their row counts",
    sql: `SELECT indicator_id, count(*) AS rows, min(period) AS period
FROM (SELECT indicator_id, period FROM census UNION ALL SELECT indicator_id, period FROM topics)
GROUP BY indicator_id ORDER BY indicator_id;`,
  },
  {
    label: "Values not checked by a person",
    sql: `SELECT verification, count(*) AS rows
FROM (SELECT verification FROM census UNION ALL SELECT verification FROM topics)
GROUP BY verification;`,
  },
];

const VIEWS: Record<string, string> = {
  census: "census-2024-gnd-tables.parquet",
  topics: "census-2024-topic-tables.parquet",
  elections: "election-results.parquet",
};

type Result = { columns: string[]; rows: unknown[][]; total: number; ms: number };

function cell(value: unknown): string {
  if (value === null || value === undefined) {
    return "–";
  }
  if (typeof value === "bigint") {
    return value.toString();
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? value.toLocaleString("en-LK") : value.toLocaleString("en-LK", { maximumFractionDigits: 4 });
  }
  if (typeof value === "object") {
    return JSON.stringify(value, (_, v) => (typeof v === "bigint" ? v.toString() : v));
  }
  return String(value);
}

export default function QueryConsole({ files }: { files: string[] }) {
  const db = useRef<{ db: AsyncDuckDB; conn: AsyncDuckDBConnection } | null>(null);
  const [state, setState] = useState<"idle" | "loading" | "ready" | "running" | "error">("idle");
  const [sql, setSql] = useState(PRESETS[0].sql);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);
  const views = Object.entries(VIEWS).filter(([, file]) => files.includes(file));

  async function start(): Promise<{ db: AsyncDuckDB; conn: AsyncDuckDBConnection }> {
    if (db.current) {
      return db.current;
    }
    setState("loading");
    const duckdb = await import("@duckdb/duckdb-wasm");
    const worker = new Worker("/release/duckdb/duckdb-browser-eh.worker.js");
    const instance = new duckdb.AsyncDuckDB(new duckdb.VoidLogger(), worker);
    await instance.instantiate(`${window.location.origin}/release/duckdb/duckdb-eh.wasm`);
    const conn = await instance.connect();
    const base = `${window.location.origin}/release/`;
    for (const [view, file] of views) {
      await instance.registerFileURL(file, `${base}observations/${file}`, duckdb.DuckDBDataProtocol.HTTP, false);
      await conn.query(`CREATE VIEW ${view} AS SELECT * FROM read_parquet('${file}')`);
    }
    await instance.registerFileURL("geographies.parquet", `${base}geographies.parquet`, duckdb.DuckDBDataProtocol.HTTP, false);
    await conn.query(
      "CREATE VIEW geographies AS SELECT geography_id, level, parent_id, name_en, name_si, name_ta FROM read_parquet('geographies.parquet')",
    );
    db.current = { db: instance, conn };
    setState("ready");
    return db.current;
  }

  async function run() {
    setError(null);
    try {
      const { conn } = await start();
      setState("running");
      const t0 = performance.now();
      const table = await conn.query(sql);
      const columns = table.schema.fields.map((field) => field.name);
      const rows = table.toArray().slice(0, 1000).map((row) => columns.map((name) => (row as Record<string, unknown>)[name]));
      setResult({ columns, rows, total: table.numRows, ms: Math.round(performance.now() - t0) });
      setState("ready");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
      setState(db.current ? "ready" : "error");
    }
  }

  useEffect(() => {
    return () => {
      void db.current?.conn.close();
      void db.current?.db.terminate();
    };
  }, []);

  return (
    <div className="query-console">
      <div className="query-presets" role="group" aria-label="Example queries">
        {PRESETS.map((preset) => (
          <button key={preset.label} type="button" className="text-button" onClick={() => setSql(preset.sql)}>
            {preset.label}
          </button>
        ))}
      </div>
      <label className="visually-hidden" htmlFor="query-sql">
        SQL query
      </label>
      <textarea
        id="query-sql"
        className="query-sql"
        value={sql}
        spellCheck={false}
        rows={8}
        onChange={(event) => setSql(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
            void run();
          }
        }}
      />
      <p>
        <button type="button" className="button" onClick={() => void run()} disabled={state === "loading" || state === "running"}>
          {state === "loading" ? "Loading the engine (about 33 MB, once)…" : state === "running" ? "Running…" : "Run query"}
        </button>{" "}
        <span className="muted small">
          Tables: {views.map(([view]) => view).join(", ")}, geographies. Runs in your browser; nothing is sent anywhere.
        </span>
      </p>
      {error ? (
        <p className="atlas-empty" role="alert">
          {error}
        </p>
      ) : null}
      {result ? (
        <>
          <p className="muted small" data-testid="query-summary">
            {result.total.toLocaleString("en-LK")} rows in {result.ms} ms
            {result.total > result.rows.length ? `; showing the first ${result.rows.length}` : ""}.
          </p>
          <div className="table-scroll">
            <table className="data-table" data-testid="query-result">
              <thead>
                <tr>
                  {result.columns.map((name) => (
                    <th key={name} scope="col">
                      {name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.rows.map((row, index) => (
                  <tr key={index}>
                    {row.map((value, column) => (
                      <td key={column}>{cell(value)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : null}
    </div>
  );
}
