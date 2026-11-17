import type { Metadata } from "next";
import Link from "next/link";

import {
  TOTAL_ROWS,
  candidateRows,
  displayName,
  formatShare,
  formatTotal,
  indexElectoral,
  type ElectionIndex,
} from "@/lib/atlas/elections";
import type { ElectionPlace } from "@/lib/atlas/types";
import { getElectoral } from "@/lib/elections-server";

export const metadata: Metadata = {
  title: "Presidential Election 2024",
  description:
    "Official results of the 2024 presidential election by electoral district and polling division, with sources.",
  alternates: { canonical: "/elections/presidential-2024" },
};

function Candidates({ index, place }: { index: ElectionIndex; place: ElectionPlace }) {
  return (
    <div className="table-scroll">
      <table>
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
          {candidateRows(index, place).map((row) => (
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

function SourceLine({ place }: { place: ElectionPlace }) {
  return (
    <p className="source-line">
      {place.source.locator ?? "no locator"}
      {place.source.sha256 ? ` · sha256 ${place.source.sha256.slice(0, 16)}…` : ""} ·{" "}
      {place.source.verification.join(", ").replaceAll("_", " ")}
    </p>
  );
}

export default function Presidential2024Page() {
  const electoral = getElectoral();
  if (!electoral || electoral.election.id !== "presidential-2024") {
    return (
      <section className="shell section">
        <h1>Presidential Election 2024</h1>
        <p className="muted">No election results in this build yet.</p>
        <p>
          <Link href="/elections">All elections</Link>
        </p>
      </section>
    );
  }
  const index = indexElectoral(electoral);
  const country = electoral.country;
  return (
    <section className="shell section election-page">
      <p className="eyebrow">
        <Link href="/elections">Elections</Link> · {electoral.election.date}
      </p>
      <h1>{electoral.election.name}</h1>
      <p className="lede">
        Official results of the Election Commission of Sri Lanka by electoral district (polling
        divisions plus postal votes) and by polling division. Candidates are listed in
        ballot-paper order. Values the pipeline could not read are shown as &ldquo;not
        read&rdquo;, never as zero.
      </p>
      <p className="notice">
        {electoral.verification_note}{" "}
        {electoral.publication ? `${electoral.publication.notice} (${electoral.publication.decision})` : null}
      </p>
      <p>
        <Link href="/?lens=elections">See it on the map</Link>
        {electoral.landing_page ? (
          <>
            {" "}
            · <a href={electoral.landing_page}>Official results page</a>
          </>
        ) : null}
      </p>

      {country ? (
        <>
          <h2>Sri Lanka</h2>
          <div className="table-scroll">
            <table>
              <tbody>
                {TOTAL_ROWS.map((row) => (
                  <tr key={row.id}>
                    <th scope="row">{row.label}</th>
                    <td>{formatTotal(row.id, country.values[row.id])}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Candidates index={index} place={country} />
          <SourceLine place={country} />
        </>
      ) : null}

      <h2>By electoral district</h2>
      <p className="muted small">In Election Commission number order. Postal votes included.</p>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">Electoral district</th>
              {TOTAL_ROWS.map((row) => (
                <th key={row.id} scope="col">
                  {row.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {electoral.eds.map((ed) => (
              <tr key={ed.id}>
                <th scope="row">
                  <a href={`#${ed.id}`}>{ed.name ?? ed.id}</a>
                </th>
                {TOTAL_ROWS.map((row) => (
                  <td key={row.id}>{formatTotal(row.id, ed.values[row.id])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {electoral.eds.map((ed) => {
        const pds = index.pdsOf.get(ed.id) ?? [];
        return (
          <section key={ed.id} id={ed.id} className="election-ed">
            <h3>
              {ed.name} <span className="muted small">electoral district {ed.ec_code}</span>
            </h3>
            {ed.postal ? (
              <p className="small">
                Postal votes: {formatTotal("votes_polled", ed.postal.votes_polled)} polled,{" "}
                {formatTotal("votes_valid", ed.postal.votes_valid)} valid (counted for the
                district, never assigned to a polling division).
              </p>
            ) : null}
            <details className="table-details">
              <summary>Votes by candidate</summary>
              <Candidates index={index} place={ed} />
            </details>
            <details className="table-details">
              <summary>{pds.length} polling divisions</summary>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Polling division</th>
                      {TOTAL_ROWS.map((row) => (
                        <th key={row.id} scope="col">
                          {row.label}
                        </th>
                      ))}
                      <th scope="col">Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pds.map((pd) => (
                      <tr key={pd.id}>
                        <th scope="row">{pd.name ?? pd.id}</th>
                        {TOTAL_ROWS.map((row) => (
                          <td key={row.id}>{formatTotal(row.id, pd.values[row.id])}</td>
                        ))}
                        <td className="small">{pd.source.locator}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
            <SourceLine place={ed} />
          </section>
        );
      })}

      <p className="small muted">
        {electoral.publication?.attribution} Dataset <code>{electoral.dataset_id}</code>, release{" "}
        <code>{electoral.release}</code>. Polling divisions have no map: no official list of their
        GN divisions and no boundary with known rights exists yet (D-040).
      </p>
    </section>
  );
}
