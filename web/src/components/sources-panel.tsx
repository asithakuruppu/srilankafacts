import type { SourceComparison } from "@/lib/types";

function formatCount(value: number | null): string {
  return value === null ? "no matching unit" : value.toLocaleString("en-GB");
}

/**
 * Side-by-side source comparison (D-019). Differences are shown, not resolved: each claim keeps
 * its source, reference date and locator, and the preferred claim states why it is preferred.
 */
export default function SourcesPanel({ comparisons }: { comparisons: SourceComparison[] }) {
  const differ = comparisons.filter((item) => !item.agree);
  return (
    <section className="section" id="sources" aria-labelledby="sources-heading">
      <div className="section-head">
        <div>
          <p className="eyebrow">Sources compared</p>
          <h2 id="sources-heading">
            {differ.length > 0 ? "Sources disagree here" : "Sources agree here"}
          </h2>
        </div>
        <p className="section-note">
          Where more than one publishable source states the same thing about this place, each
          claim is shown side by side. A difference is reported, not corrected; sources can
          differ because of their reference dates or how units are drawn.
        </p>
      </div>
      <div className="sources-list">
        {comparisons.map((item) => (
          <div className="panel" key={item.indicator_id}>
            <h3>
              {item.label}
              {item.agree ? (
                <span className="tag tag-quiet">Agree</span>
              ) : (
                <span className="tag">Sources disagree</span>
              )}
            </h3>
            <table className="compare-table">
              <thead>
                <tr>
                  <th scope="col">Source</th>
                  <th scope="col">Reference date</th>
                  <th scope="col">Value</th>
                </tr>
              </thead>
              <tbody>
                {item.claims.map((claim) => (
                  <tr key={claim.source_id}>
                    <th scope="row">
                      {claim.label}
                      {claim.preferred ? <small className="delta">Shown by default</small> : null}
                      <small className="delta">{claim.locator}</small>
                    </th>
                    <td>{claim.reference_date}</td>
                    <td className="numeric">{formatCount(claim.value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!item.agree && item.spread !== null ? (
              <p className="small">
                Difference: {item.spread.toLocaleString("en-GB")}
                {item.relative_spread !== null
                  ? ` (${(item.relative_spread * 100).toFixed(1)}% of the larger value)`
                  : ""}
                .
              </p>
            ) : null}
            <p className="muted small">
              {item.preferred_reason} {item.note}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
