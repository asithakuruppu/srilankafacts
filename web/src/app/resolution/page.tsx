import fs from "node:fs";
import path from "node:path";

import type { Metadata } from "next";
import Link from "next/link";

import FinestMap from "@/components/resolution/finest-map";
import ResolutionCatalogue from "@/components/resolution/catalogue";
import type { ResolutionEntry } from "@/lib/atlas/types";
import { getAtlasMeta } from "@/lib/release";

import "../atlas.css";

export const metadata: Metadata = {
  title: "Finest view",
  description: "Every dataset at the best resolution the platform holds, with what it really tells us.",
  alternates: { canonical: "/resolution" },
};

function readRows(): ResolutionEntry[] | null {
  const file = path.resolve(process.cwd(), "public/release/atlas/resolution.json");
  if (!fs.existsSync(file)) {
    return null;
  }
  return (JSON.parse(fs.readFileSync(file, "utf8")) as { datasets: ResolutionEntry[] }).datasets;
}

export default function ResolutionPage() {
  const meta = getAtlasMeta();
  const rows = meta?.resolution ? readRows() : null;
  return (
    <section className="shell resolution-page">
      <p className="eyebrow">Finest view</p>
      <h1>Every dataset at its best resolution</h1>
      <p className="lede">
        The main atlas shows everything at GN level. Many sources are finer, from 10 m land cover to 1 km soil maps.
        This page lists each dataset&apos;s native resolution and shows the finer layers the platform actually holds.
        Finer cells are not always finer information: a 100 m population grid built from GN totals still knows only the GN total.
      </p>
      {rows ? (
        <>
          <h2>Native resolution of each dataset</h2>
          <ResolutionCatalogue rows={rows} />
        </>
      ) : (
        <p className="muted">
          This build has no resolution manifest. It comes from <code>slf atlas export --catalog-dir</code>. The{" "}
          <Link href="/">atlas</Link> still works.
        </p>
      )}
      <h2>The finest layers on a map</h2>
      {meta ? (
        <FinestMap hasGrid={Boolean(meta.grid)} hasFeatures={Boolean(meta.features)} />
      ) : (
        <p className="muted">This build has no atlas bundle, so there is no map.</p>
      )}
      <p className="muted">
        Raster layers such as 10 m land cover and canopy height are summarised per GN division today; showing them at native
        resolution needs a tile stack that is not built yet.
      </p>
    </section>
  );
}
