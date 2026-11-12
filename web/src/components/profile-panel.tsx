import Link from "next/link";

import type { PlaceProfile } from "@/lib/types";

const AXIS_RANGE = 4; // scores are drawn on a fixed -4..4 scale; values beyond it are clamped

function levelWord(level: PlaceProfile["level"]): string {
  return level === "ds" ? "DS divisions" : "GN divisions";
}

function listNames(ids: string[], names: Map<string, string>): string {
  return ids.map((id) => names.get(id) ?? id).join(", ");
}

/**
 * Profile-space panel (D-031). DS pages list similar places with reasons; GN pages show the axis
 * position and distance from the centre, and link to the DS division's similar places.
 */
export default function ProfilePanel({
  profile,
  indicatorNames,
  parentLabel,
}: {
  profile: PlaceProfile;
  indicatorNames: Map<string, string>;
  parentLabel: string | null;
}) {
  const drafts = profile.axes.some((axis) => axis.label_status !== "human_approved");
  return (
    <section className="section" id="profile" aria-labelledby="profile-heading">
      <div className="section-head">
        <div>
          <p className="eyebrow">Profile comparison</p>
          <h2 id="profile-heading">
            {profile.similar ? "Places with a similar profile" : "Where this place sits"}
          </h2>
        </div>
        <p className="section-note">
          Computed from nine census values (population, age structure, sex ratio, housing and
          density) in the profile space v{profile.space_version}. A distance says how alike two
          profiles are. It is not a fact about the places and not a ranking.
        </p>
      </div>

      <p className="notice notice-warn">
        <strong>Read with care.</strong> {profile.note}
      </p>

      <div className="profile-grid">
        <div className="panel">
          <h3>Position on the profile axes</h3>
          <table className="compare-table profile-axes">
            <thead>
              <tr>
                <th scope="col">Axis</th>
                <th scope="col">Higher values mean{drafts ? " (draft label)" : ""}</th>
                <th scope="col">Score</th>
              </tr>
            </thead>
            <tbody>
              {profile.axes.map((axis) => {
                const clamped = Math.max(-AXIS_RANGE, Math.min(AXIS_RANGE, axis.score));
                const left = 50 + (Math.min(clamped, 0) / AXIS_RANGE) * 50;
                const width = (Math.abs(clamped) / AXIS_RANGE) * 50;
                return (
                  <tr key={axis.axis}>
                    <th scope="row">
                      {axis.axis}
                      <small className="delta">
                        {(axis.variance_explained * 100).toFixed(0)}% of variation
                      </small>
                    </th>
                    <td>{axis.draft_label}</td>
                    <td className="numeric">
                      {axis.score.toFixed(2)}
                      <span className="axis-bar" aria-hidden="true">
                        <span style={{ left: `${left}%`, width: `${width}%` }} />
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="muted small">
            0 is the national centre of {levelWord(profile.level)}. Scores are in standardised
            units.
          </p>
        </div>

        <div className="panel">
          <h3>Distance from the national centre</h3>
          <p className="profile-figure">
            {profile.distance_from_centre.toFixed(2)}
            <small>
              further out than {profile.percentile.toFixed(0)}% of {levelWord(profile.level)}
            </small>
          </p>
          <p className="small">
            Largest contributions:{" "}
            {listNames(profile.unusual_indicators, indicatorNames)}.
          </p>
        </div>
      </div>

      {profile.similar ? (
        <div className="table-scroll">
          <table className="compare-table" aria-describedby="similar-note">
            <caption className="muted small" id="similar-note">
              The 10 closest {levelWord(profile.level)} in the profile space. &ldquo;Alike&rdquo;
              lists the values that add least to the distance; &ldquo;differs&rdquo; lists those
              that add most.
            </caption>
            <thead>
              <tr>
                <th scope="col">Place</th>
                <th scope="col">Distance</th>
                <th scope="col">Alike in</th>
                <th scope="col">Differs in</th>
              </tr>
            </thead>
            <tbody>
              {profile.similar.map((item) => (
                <tr key={item.geography_id}>
                  <th scope="row">
                    <Link href={`/place/${item.geography_id}`}>
                      {item.name_en ?? item.geography_id}
                    </Link>
                  </th>
                  <td className="numeric">{item.distance.toFixed(2)}</td>
                  <td>{listNames(item.alike, indicatorNames)}</td>
                  <td>{listNames(item.different, indicatorNames)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="notice">
          {profile.similar_note}{" "}
          {profile.similar_via ? (
            <Link href={`/place/${profile.similar_via}#profile`}>
              Similar places for {parentLabel ?? profile.similar_via}
            </Link>
          ) : null}
        </p>
      )}
    </section>
  );
}
