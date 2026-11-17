import type { Metadata } from "next";
import Link from "next/link";

import { formatTotal } from "@/lib/atlas/elections";
import { getElectoral } from "@/lib/elections-server";

export const metadata: Metadata = {
  title: "Elections",
  description: "Official election results by electoral district, with their source.",
  alternates: { canonical: "/elections" },
};

export default function ElectionsPage() {
  const electoral = getElectoral();
  return (
    <section className="shell section">
      <p className="eyebrow">Elections</p>
      <h1>Election results</h1>
      <p className="lede">
        Official results of the Election Commission of Sri Lanka, by electoral district and
        polling division, each traced to the result sheet it was read from.
      </p>
      {electoral ? (
        <ul className="election-list">
          <li>
            <Link href={`/elections/${electoral.election.id}`}>{electoral.election.name}</Link>{" "}
            <span className="muted">
              · {electoral.election.date} · {electoral.eds.length} electoral districts,{" "}
              {electoral.pds.length} polling divisions · turnout{" "}
              {formatTotal("turnout", electoral.country?.values.turnout)}
            </span>
          </li>
        </ul>
      ) : (
        <p className="muted">
          No election results in this build yet. They come from the release&rsquo;s
          election-results observations through <code>uv run slf atlas export</code>.
        </p>
      )}
      <h2>Not held yet</h2>
      <p>
        Parliamentary, provincial council and local authority elections, and presidential
        elections before 2024, are not yet ingested. Local authority and MOH areas are not drawn:
        no boundary or GN list with recorded reuse rights is held.
      </p>
      <p className="small muted">
        Method: <Link href="/methods">methods</Link> (election results, D-039; polling divisions
        in tables only, D-040).
      </p>
    </section>
  );
}
