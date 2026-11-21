import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import {
  FLAG_TEXT,
  UNAVAILABLE_REASON,
  UNIT_SCHEMES,
  getUnitProfiles,
  isUnitScheme,
} from "@/lib/unit-profiles";

export function generateStaticParams() {
  return Object.keys(UNIT_SCHEMES).map((scheme) => ({ scheme }));
}

export const dynamicParams = false;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ scheme: string }>;
}): Promise<Metadata> {
  const { scheme } = await params;
  const title = isUnitScheme(scheme) ? UNIT_SCHEMES[scheme].title : "Areas";
  return { title, alternates: { canonical: `/units/${scheme}` } };
}

const pct = (v: number | null | undefined) => (v == null ? "n/a" : `${(v * 100).toFixed(1)}%`);
const num = (v: number | null | undefined) => (v == null ? "n/a" : Math.round(v).toLocaleString("en-US"));

export default async function UnitsPage({ params }: { params: Promise<{ scheme: string }> }) {
  const { scheme } = await params;
  if (!isUnitScheme(scheme)) {
    notFound();
  }
  const { title } = UNIT_SCHEMES[scheme];
  const doc = getUnitProfiles(scheme);
  if (!doc) {
    return (
      <section className="shell section">
        <p className="eyebrow">Areas</p>
        <h1>{title}</h1>
        <p className="muted" data-testid="units-unavailable">
          Unavailable. {UNAVAILABLE_REASON}
        </p>
        <p className="small muted">
          Method: <Link href="/methods">methods</Link> (D-046).
        </p>
      </section>
    );
  }
  return (
    <section className="shell section">
      <p className="eyebrow">Areas</p>
      <h1>{title}</h1>
      <p className="lede">
        Each area is a set of GN divisions. Counts are the sum of Census 2024 GN values weighted by
        membership; rates are recomputed from those counts. {doc.support}.
      </p>
      {doc.notice ? (
        <p className="notice" data-testid="units-notice">
          {doc.notice}
        </p>
      ) : null}
      <p className="small muted">{doc.attribution ?? `Source: ${doc.source}`}</p>
      {doc.spine_gns_without_unit != null ? (
        <p className="small muted">
          Coverage: {doc.spine_gns_without_unit.toLocaleString("en-US")} GN divisions belong to no
          area in this list, so these areas do not add up to the country.
        </p>
      ) : null}
      <table>
        <thead>
          <tr>
            <th>Area</th>
            <th>GN divisions</th>
            <th>Population</th>
            <th>Households</th>
            <th>Aged 0–14</th>
            <th>Aged 15+</th>
            <th>Per household</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          {doc.units.map((u) => (
            <tr key={u.id} id={u.id}>
              <th scope="row">{u.name ?? u.id}</th>
              <td>{u.gn_members}</td>
              <td>{num(u.counts.population_total)}</td>
              <td>{num(u.counts.households_total)}</td>
              <td>{pct(u.rates.share_aged_0_14)}</td>
              <td>{pct(u.rates.share_aged_15_plus)}</td>
              <td>{u.rates.population_per_household?.toFixed(2) ?? "n/a"}</td>
              <td className="small muted">{u.flags.map((f) => FLAG_TEXT[f] ?? f).join("; ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
