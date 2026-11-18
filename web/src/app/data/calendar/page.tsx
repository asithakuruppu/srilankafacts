import fs from "node:fs";
import path from "node:path";

import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Release calendar",
  description: "Which sources Sri Lanka Facts holds, how often they publish, and what is due.",
  alternates: { canonical: "/data/calendar" },
};

type Row = {
  dataset_id: string;
  title: string;
  source: string;
  status: string;
  schedule: string;
  reference_period: string | null;
  landing_page: string | null;
  snapshots: number;
  last_snapshot: string | null;
  expected_next: string | null;
  state: "not_held" | "held_unscheduled" | "overdue" | "current";
  page_changed: boolean | null;
};
type Calendar = { generated_at: string; probed: boolean; counts: Record<string, number>; datasets: Row[]; note: string };

const STATE_TEXT: Record<Row["state"], string> = {
  overdue: "Overdue",
  current: "Current",
  held_unscheduled: "Held, no fixed schedule",
  not_held: "Not held yet",
};
const ORDER: Row["state"][] = ["overdue", "current", "held_unscheduled", "not_held"];

function readCalendar(): Calendar | null {
  const file = path.resolve(process.cwd(), "public/release/calendar.json");
  return fs.existsSync(file) ? (JSON.parse(fs.readFileSync(file, "utf8")) as Calendar) : null;
}

export default function CalendarPage() {
  const calendar = readCalendar();
  return (
    <section className="shell section">
      <p className="eyebrow">
        <Link href="/data">Data</Link> · Release calendar
      </p>
      <h1>Release calendar</h1>
      <p className="lede">
        Every source in the catalogue: whether a copy is held, how often it is published and
        whether a newer edition is due. Detection only; nothing here is a statistic.
      </p>
      {!calendar ? (
        <p className="muted">
          No calendar in this build. It comes from <code>uv run slf freshness</code>.
        </p>
      ) : (
        <>
          <p className="muted">
            Checked {calendar.generated_at.slice(0, 10)}
            {calendar.probed ? ", with landing pages probed" : ", from held snapshots only (landing pages not probed)"}.{" "}
            {ORDER.filter((state) => calendar.counts[state])
              .map((state) => `${calendar.counts[state]} ${STATE_TEXT[state].toLowerCase()}`)
              .join(" · ")}
            .
          </p>
          <div className="table-scroll">
            <table className="data-table" data-testid="calendar-table">
              <thead>
                <tr>
                  <th scope="col">Dataset</th>
                  <th scope="col">Source</th>
                  <th scope="col">State</th>
                  <th scope="col">Schedule</th>
                  <th scope="col">Last copy</th>
                  <th scope="col">Next expected</th>
                </tr>
              </thead>
              <tbody>
                {[...calendar.datasets]
                  .sort((a, b) => ORDER.indexOf(a.state) - ORDER.indexOf(b.state) || a.title.localeCompare(b.title))
                  .map((row) => (
                    <tr key={row.dataset_id}>
                      <th scope="row">
                        {row.landing_page ? (
                          <a href={row.landing_page} rel="noopener noreferrer">
                            {row.title}
                          </a>
                        ) : (
                          row.title
                        )}
                        <br />
                        <code>{row.dataset_id}</code>
                      </th>
                      <td>{row.source}</td>
                      <td>
                        {STATE_TEXT[row.state]}
                        {row.page_changed ? " · page changed" : ""}
                      </td>
                      <td>{row.schedule.replaceAll("_", " ")}</td>
                      <td>{row.last_snapshot ? row.last_snapshot.slice(0, 10) : "–"}</td>
                      <td>{row.expected_next ?? "–"}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
          <p className="muted">{calendar.note}</p>
        </>
      )}
    </section>
  );
}
