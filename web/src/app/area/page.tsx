import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import AreaTool from "@/components/atlas/area-tool";
import { getAtlasMeta, getIndicators } from "@/lib/release";

import "../atlas.css";

export const metadata: Metadata = {
  title: "Areas and points",
  description:
    "Estimate census counts inside a radius or a drawn shape, and find which places contain a point.",
  alternates: { canonical: "/area" },
};

export default function AreaPage() {
  const meta = getAtlasMeta();
  const indicators = getIndicators()
    .filter((item) => item.measure_type === "count" && item.levels.includes("gn"))
    .map((item) => ({ id: item.id, name: item.name, unit: item.unit }));
  return (
    <section className="area-page">
      <header className="shell area-head">
        <p className="eyebrow">Areas and points</p>
        <h1>Any area, not just official ones</h1>
        <p className="lede">
          Draw a circle or a shape to estimate how many people or households live inside it, or
          click a point to see which GN, DS, district and electoral district contain it.
        </p>
      </header>
      {meta?.grid ? (
        <Suspense fallback={<p className="shell muted">Loading the map…</p>}>
          <AreaTool indicators={indicators} />
        </Suspense>
      ) : (
        <p className="shell muted">
          This build has no analytic grid, so areas cannot be estimated. It comes from{" "}
          <code>uv run slf grid build</code> and <code>slf atlas export --grid-dir</code>. The{" "}
          <Link href="/">atlas</Link> still works.
        </p>
      )}
    </section>
  );
}
