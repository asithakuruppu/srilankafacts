import type { Metadata } from "next";
import Link from "next/link";

import { getCorrections, getGeography, geographyLabel } from "@/lib/release";
import type { Correction } from "@/lib/types";

export const metadata: Metadata = {
  title: "Corrections",
  description:
    "Every error found in Sri Lanka Facts values after release, what changed, and in which release it was fixed.",
  alternates: { canonical: "/corrections" },
};

const CAUSE: Record<string, string> = {
  extraction: "Value read wrongly from the source",
  harmonisation: "Wrong mapping between source and indicator",
  geography_match: "Values attached to the wrong place",
  unit_or_scale: "Wrong unit or scale",
  rounding: "Rounding",
  display: "Shown wrongly on the website",
  source_ambiguity: "Source unclear",
  source_error: "Error in the source",
};

function formatDate(value: string | null): string {
  if (!value) {
    return "not yet";
  }
  return new Date(`${value}T00:00:00Z`).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  });
}

function places(entry: Correction) {
  return entry.geographies.map((id, index) => {
    const geo = getGeography(id);
    return (
      <span key={id}>
        {index > 0 ? ", " : null}
        {geo ? <Link href={`/place/${id}`}>{geographyLabel(geo)}</Link> : id}{" "}
        <code>{id}</code>
      </span>
    );
  });
}

export default function CorrectionsPage() {
  const log = getCorrections();
  const entries = log?.entries ?? [];

  return (
    <div className="shell section methods">
      <header className="place-head">
        <p className="eyebrow">Corrections</p>
        <h1>Errors we found and fixed</h1>
        <p className="lede">
          Releases never change once built. When a wrong value is found, the fix goes into a new
          release and is recorded here: what was wrong, what changed, why it happened, and the
          evidence. Entries are drafted from the evidence and approved by the project lead before a
          public release.
        </p>
      </header>

      {log === null ? (
        <p className="notice notice-warn">
          This release was built without a corrections log. See the project repository for{" "}
          <code>docs/corrections/log.yaml</code>.
        </p>
      ) : entries.length === 0 ? (
        <p className="notice">No corrections have been recorded.</p>
      ) : (
        <ol className="corrections-list">
          {entries.map((entry) => (
            <li key={entry.id} id={entry.id}>
              <article className="panel">
                <h2>
                  {entry.id}: {CAUSE[entry.cause] ?? entry.cause}
                  {entry.scope === "private_preview" ? (
                    <span className="tag">Private preview</span>
                  ) : null}
                  {entry.approved_by ? null : (
                    <span className="tag">Draft, awaiting approval</span>
                  )}
                </h2>
                <dl className="corrections-meta">
                  <div>
                    <dt>Found</dt>
                    <dd>{formatDate(entry.found)}</dd>
                  </div>
                  <div>
                    <dt>Fixed</dt>
                    <dd>
                      {formatDate(entry.fixed)}
                      {entry.fixed_in ? (
                        <>
                          {" "}
                          in <code>{entry.fixed_in}</code>
                        </>
                      ) : null}
                    </dd>
                  </div>
                  <div>
                    <dt>Affected releases</dt>
                    <dd>{entry.affected_releases.join(", ")}</dd>
                  </div>
                  <div>
                    <dt>Values changed</dt>
                    <dd>{entry.values_changed.toLocaleString("en-GB")}</dd>
                  </div>
                  {entry.geographies.length > 0 ? (
                    <div>
                      <dt>Places</dt>
                      <dd>{places(entry)}</dd>
                    </div>
                  ) : null}
                  <div>
                    <dt>Indicators</dt>
                    <dd>
                      {Array.isArray(entry.indicators)
                        ? entry.indicators.join(", ")
                        : entry.indicators}
                    </dd>
                  </div>
                </dl>
                <h3>What was wrong</h3>
                <p>{entry.what_was_wrong}</p>
                <h3>What changed</h3>
                <p>{entry.what_changed}</p>
                <h3>Evidence</h3>
                <ul>
                  {entry.evidence.map((item) => (
                    <li key={item}>
                      <code>{item}</code>
                    </li>
                  ))}
                </ul>
              </article>
            </li>
          ))}
        </ol>
      )}

      <section className="section-tight">
        <h2>Found something wrong?</h2>
        <p>
          Every value on a place page opens to its source workbook row and snapshot. If a value
          does not match its source, please tell us with the place, the indicator and what the
          source says. A reporting channel is being set up for the public beta.
        </p>
      </section>
    </div>
  );
}
