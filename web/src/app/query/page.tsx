import fs from "node:fs";
import path from "node:path";

import type { Metadata } from "next";
import Link from "next/link";

import QueryConsole from "@/components/query-console";
import { getLatest } from "@/lib/release";

export const metadata: Metadata = {
  title: "Query the data",
  description: "Run SQL on the release's observation tables in your browser.",
  alternates: { canonical: "/query" },
};

function parquetFiles(): string[] {
  const file = path.resolve(process.cwd(), "public/release/meta.json");
  if (!fs.existsSync(file)) {
    return [];
  }
  return (JSON.parse(fs.readFileSync(file, "utf8")) as { parquet?: string[] }).parquet ?? [];
}

export default function QueryPage() {
  const files = parquetFiles();
  const latest = getLatest();
  return (
    <section className="shell section">
      <p className="eyebrow">
        <Link href="/data">Data</Link> · Query
      </p>
      <h1>Query the data</h1>
      <p className="lede">
        SQL on the release&rsquo;s observation tables, with DuckDB running in your browser. Every
        row keeps its dataset, snapshot hash, source locator and verification status.
      </p>
      {files.length ? (
        <QueryConsole files={files} />
      ) : (
        <p className="muted">This build has no Parquet files to query.</p>
      )}
      <p className="muted small">
        Release <code>{latest.release}</code>. {latest.citation} Census 2024 values may be reused
        non-commercially with attribution (D-030).
      </p>
    </section>
  );
}
