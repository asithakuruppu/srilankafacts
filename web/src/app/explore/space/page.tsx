import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import SpaceExplorer from "@/components/space-explorer";
import { getAtlasMeta } from "@/lib/release";

import "../../atlas.css";

export const metadata: Metadata = {
  title: "Places like this: geography beside similarity",
  description:
    "DS divisions on the map beside the same divisions placed by similarity, with linked selection and the reasons for every distance.",
  alternates: { canonical: "/explore/space" },
};

export default function SpaceExplorerPage() {
  const meta = getAtlasMeta();
  const spaces = meta?.spaces ?? null;
  return (
    <div className="shell section space-page">
      <header className="place-head">
        <p className="eyebrow">
          <Link href="/explore">Explore</Link> · similarity
        </p>
        <h1>Places like this</h1>
        <p className="lede">
          Every DS division twice: on the map, and placed by how alike their census profiles are.
          Pick a place in either view to see where similar places are in the country, and why.
        </p>
      </header>
      {!meta || !spaces?.composite ? (
        <p className="muted">
          No similarity spaces in this build yet. They come from <code>uv run slf profile spaces</code>{" "}
          and <code>uv run slf atlas export --spaces-dir …</code>.
        </p>
      ) : (
        <Suspense fallback={<p className="muted">Loading the explorer…</p>}>
          <SpaceExplorer spaces={spaces} />
        </Suspense>
      )}
      <p className="small muted">
        A distance is a similarity statement, never a fact or a ranking (rule 13). Types and axis
        names are machine drafts awaiting review. <Link href="/methods">Methods</Link>.
      </p>
    </div>
  );
}
