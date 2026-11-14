import Provenance from "@/components/provenance";
import { formatValue } from "@/lib/format";
import { getObservationFor } from "@/lib/release";
import type { Place } from "@/lib/types";

/**
 * Ethnic group and religion (D-033): DS divisions and larger areas only, from DCS's own DS and
 * district tables. Shown in DCS's column order, never sorted by value, with no rankings, maps
 * or links to indicator pages.
 */
const TOPICS = [
  {
    key: "ethnicity",
    title: "Population by ethnic group",
    table: "A6 (DS) and A2 (district)",
    categories: [
      ["sinhalese", "Sinhalese"],
      ["sri_lanka_tamil", "Sri Lanka Tamil"],
      ["indian_tamil", "Indian Tamil / Malaiyaga Thamilar"],
      ["sri_lanka_moor", "Sri Lanka Moor / Muslim"],
      ["burgher", "Burgher"],
      ["malay", "Malay"],
      ["sri_lanka_chetty", "Sri Lanka Chetty"],
      ["bharatha", "Bharatha"],
      ["veddha", "Veddha"],
      ["other", "Other"],
    ],
  },
  {
    key: "religion",
    title: "Population by religion",
    table: "A7 (DS) and A3 (district)",
    categories: [
      ["buddhist", "Buddhist"],
      ["hindu", "Hindu"],
      ["islam", "Islam"],
      ["roman_catholic", "Roman Catholic"],
      ["other_christian", "Other Christian"],
      ["other", "Other"],
    ],
  },
] as const;

export const IDENTITY_INDICATORS = new Set(
  TOPICS.flatMap((topic) =>
    topic.categories.flatMap(([slug]) => {
      const id = `population_${topic.key}_${slug}`;
      return [id, `${id}_share`];
    }),
  ),
);

export default function IdentityPanel({ place }: { place: Place }) {
  const present = TOPICS.filter((topic) =>
    topic.categories.some(([slug]) =>
      getObservationFor(place, `population_${topic.key}_${slug}`),
    ),
  );
  if (present.length === 0) {
    return null;
  }
  return (
    <section className="section" id="ethnicity-religion" aria-labelledby="identity-heading">
      <div className="section-head">
        <div>
          <p className="eyebrow">Census 2024</p>
          <h2 id="identity-heading">Ethnic group and religion</h2>
        </div>
        <p className="section-note">
          As published by the Department of Census and Statistics for this area, in DCS&apos;s
          categories and column order. Shown for DS divisions and larger areas only; GN figures
          are not shown because DCS folds groups of fewer than 10 people into “Other” at GN
          level.
        </p>
      </div>
      {present.map((topic) => (
        <div className="table-scroll" key={topic.key}>
          <table className="data-table">
            <caption>
              {topic.title} (DCS table {topic.table})
            </caption>
            <thead>
              <tr>
                <th scope="col">Category</th>
                <th scope="col">Persons</th>
                <th scope="col">Share</th>
                <th scope="col">Source</th>
              </tr>
            </thead>
            <tbody>
              {topic.categories.map(([slug, label]) => {
                const id = `population_${topic.key}_${slug}`;
                const count = getObservationFor(place, id);
                const share = getObservationFor(place, `${id}_share`);
                return (
                  <tr key={id}>
                    <th scope="row">{label}</th>
                    <td className="numeric">{formatValue(count?.value ?? null, "persons", 0)}</td>
                    <td className="numeric">{formatValue(share?.value ?? null, "percent", 1)}</td>
                    <td>{count ? <Provenance value={count} /> : null}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ))}
    </section>
  );
}
