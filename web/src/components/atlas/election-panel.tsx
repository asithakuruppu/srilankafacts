"use client";

import Link from "next/link";

import {
  ELECTION_MEASURES,
  TOTAL_ROWS,
  candidateRows,
  displayName,
  formatShare,
  formatTotal,
  type ElectionIndex,
} from "@/lib/atlas/elections";
import type { ElectionPlace, ElectionTotals } from "@/lib/atlas/types";

type Props = {
  available: boolean;
  election: ElectionIndex | null;
  subject: string | null;
  measure: keyof ElectionTotals;
  onMeasure: (id: keyof ElectionTotals) => void;
  onSelect: (id: string | null) => void;
  nameOf: (id: string) => string;
  sheetOpen: boolean;
  onSheet: (open: boolean) => void;
};

function Totals({ place }: { place: ElectionPlace }) {
  return (
    <table className="election-totals">
      <tbody>
        {TOTAL_ROWS.map((row) => (
          <tr key={row.id}>
            <th scope="row">{row.label}</th>
            <td>{formatTotal(row.id, place.values[row.id])}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Results for one unit in ballot-paper order. Nothing is sorted by votes. */
export function CandidateTable({ election, place }: { election: ElectionIndex; place: ElectionPlace }) {
  const rows = candidateRows(election, place);
  return (
    <div className="table-scroll">
      <table className="election-candidates">
        <caption>Votes by candidate, in ballot-paper order</caption>
        <thead>
          <tr>
            <th scope="col">Ballot</th>
            <th scope="col">Candidate</th>
            <th scope="col">Party code</th>
            <th scope="col">Votes</th>
            <th scope="col">Share of valid</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.ballot}>
              <td>{row.ballot}</td>
              <td>{displayName(row.name)}</td>
              <td>{row.party}</td>
              <td>{row.votes === null ? "not read" : row.votes.toLocaleString("en-LK")}</td>
              <td>{formatShare(row.share)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Source({ election, place }: { election: ElectionIndex; place: ElectionPlace }) {
  const { file } = election;
  return (
    <details className="atlas-sources">
      <summary>Source for these numbers</summary>
      <ul>
        <li>
          <strong>{file.publication?.attribution ?? "Election Commission of Sri Lanka"}</strong>
          <span>
            {file.dataset_id} · {file.election.date} · release {file.release} ·{" "}
            {place.source.verification.join(", ").replaceAll("_", " ")}
          </span>
          {place.source.locator ? <span>{place.source.locator}</span> : null}
          {place.source.sha256 ? <code>sha256 {place.source.sha256.slice(0, 16)}…</code> : null}
        </li>
      </ul>
      <p className="atlas-note">{file.verification_note}</p>
      {file.publication ? (
        <p className="atlas-note">
          {file.publication.notice} ({file.publication.decision})
        </p>
      ) : null}
      {file.landing_page ? (
        <p className="atlas-note">
          Official results page: <a href={file.landing_page}>{file.landing_page}</a>
        </p>
      ) : null}
    </details>
  );
}

export default function ElectionPanel(props: Props) {
  const { election, subject, nameOf, onSelect } = props;
  const place = election ? (subject ? election.byId.get(subject) : election.file.country) : null;
  const title = !props.available
    ? "Elections"
    : subject && !place
      ? "Not an electoral district"
      : subject
        ? nameOf(subject)
        : "Sri Lanka";
  const pds = place && election ? (election.pdsOf.get(place.id) ?? []) : [];

  return (
    <aside className="atlas-panel" aria-label="Selected place">
      <button
        type="button"
        className="atlas-panel-handle"
        aria-expanded={props.sheetOpen}
        onClick={() => props.onSheet(!props.sheetOpen)}
      >
        <span className="visually-hidden">{props.sheetOpen ? "Collapse" : "Expand"} the panel</span>
      </button>
      <header className="atlas-panel-head">
        <nav className="atlas-trail" aria-label="Containing areas">
          {subject ? (
            <button type="button" onClick={() => onSelect(null)}>
              Sri Lanka
            </button>
          ) : (
            <span>{election?.file.election.name ?? "Elections"}</span>
          )}
        </nav>
        <h2>{title}</h2>
        <p className="atlas-panel-sub">
          <span>{subject ? "Electoral district" : "Country"}</span>
          {place?.districts?.length ? (
            <span>
              {" "}
              · made of {place.districts.length === 1 ? "the district" : "the districts"}{" "}
              {place.districts.map(nameOf).join(", ")}
            </span>
          ) : null}
        </p>
      </header>
      <div className="atlas-panel-body">
        {!props.available ? (
          <p className="atlas-empty">
            No election results in this build. They come from the release&rsquo;s
            election-results observations through <code>slf atlas export</code>.
          </p>
        ) : !election ? (
          <p className="atlas-empty" role="status">
            Loading election results…
          </p>
        ) : !place ? (
          <p className="atlas-empty">
            Results are shown by electoral district. Select one on the map or below.
          </p>
        ) : (
          <>
            <section className="atlas-section">
              <h3>{election.file.election.name}</h3>
              <p className="atlas-note">
                Held {election.file.election.date}. Official results of the Election Commission,
                {subject ? " polling divisions plus postal votes" : " all 22 electoral districts"}.
              </p>
              <Totals place={place} />
              {place.postal ? (
                <p className="atlas-note">
                  Of which postal votes: {formatTotal("votes_polled", place.postal.votes_polled)}{" "}
                  polled, {formatTotal("votes_valid", place.postal.votes_valid)} valid. Postal votes
                  are counted per electoral district and are never assigned to polling divisions.
                </p>
              ) : null}
              <label className="election-measure">
                <span>Colour the map by</span>
                <select
                  value={props.measure}
                  onChange={(event) => props.onMeasure(event.target.value as keyof ElectionTotals)}
                >
                  {ELECTION_MEASURES.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.label}
                    </option>
                  ))}
                </select>
              </label>
            </section>

            <section className="atlas-section">
              <details>
                <summary>
                  Votes for all {election.file.candidates.length} candidates, in ballot-paper order
                </summary>
                <CandidateTable election={election} place={place} />
                {place.not_available > 0 ? (
                  <p className="atlas-note">
                    {place.not_available} value{place.not_available === 1 ? " was" : "s were"} not
                    read from the sheets and {place.not_available === 1 ? "is" : "are"} shown as
                    &ldquo;not read&rdquo;, never as zero.
                  </p>
                ) : null}
              </details>
            </section>

            {pds.length > 0 ? (
              <section className="atlas-section">
                <h3>Polling divisions</h3>
                <p className="atlas-note">
                  Polling divisions are in tables only: no official list of their GN divisions
                  and no boundary with known rights exists yet (D-040).
                </p>
                <div className="table-scroll">
                  <table className="election-pds">
                    <thead>
                      <tr>
                        <th scope="col">Polling division</th>
                        <th scope="col">Electors</th>
                        <th scope="col">Valid votes</th>
                        <th scope="col">Turnout</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pds.map((pd) => (
                        <tr key={pd.id}>
                          <th scope="row">{pd.name ?? pd.id}</th>
                          <td>{formatTotal("electors_registered", pd.values.electors_registered)}</td>
                          <td>{formatTotal("votes_valid", pd.values.votes_valid)}</td>
                          <td>{formatTotal("turnout", pd.values.turnout)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            ) : null}

            {!subject ? (
              <section className="atlas-section">
                <h3>Electoral districts</h3>
                <ul className="place-list">
                  {election.file.eds.map((ed) => (
                    <li key={ed.id}>
                      <button type="button" className="place-link" onClick={() => onSelect(ed.id)}>
                        <span className="place-link-name">{ed.name ?? ed.id}</span>
                        <span className="place-link-value">
                          turnout {formatTotal("turnout", ed.values.turnout)}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
                <p className="atlas-note">Listed in Election Commission number order.</p>
              </section>
            ) : null}

            <p className="atlas-note">
              <Link href={`/elections/${election.file.election.id}${subject ? `#${subject}` : ""}`}>
                Full results table
              </Link>
            </p>
            <Source election={election} place={place} />
          </>
        )}
      </div>
    </aside>
  );
}
