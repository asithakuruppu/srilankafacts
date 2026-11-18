"use client";

import Link from "next/link";
import { useMemo } from "react";

import { AxisBar, ContextStrip, Scatter, Series, ShareBar, type Marker } from "@/components/atlas/charts";
import {
  describeDifference,
  median,
  rankOf,
  shareOf,
  summariseGroup,
  type ValueMap,
} from "@/lib/atlas/context";
import { loadClusters, loadGnAdjacency, loadLandscapeSimilar, loadPlace } from "@/lib/atlas/data";
import {
  explainPair,
  percentileAmong,
  pipelineReasons,
  distancesFrom,
  type ProfileIndex,
} from "@/lib/atlas/profile";
import { childLevel } from "@/lib/atlas/scale";
import {
  LEVEL_PLURAL_TEXT,
  LEVEL_SHORT,
  type Adjacency,
  type AtlasIndicator,
  type AtlasMeta,
  type ChangeFile,
  type ClusterClass,
  type FeatureFile,
  type LandscapeIndicator,
  type Lens,
  type LevelName,
  type NeighbourRef,
  type Unit,
} from "@/lib/atlas/types";
import { useLoaded } from "@/lib/atlas/use-loaded";
import { formatNumber, formatValue } from "@/lib/format";
import type { Hierarchy } from "@/lib/hierarchy";
import type { Observation, Place } from "@/lib/types";

type Props = {
  release: string;
  meta: AtlasMeta;
  lens: Lens;
  subject: string;
  subjectLevel: LevelName;
  known: boolean;
  indicator: AtlasIndicator | undefined;
  indicators: AtlasIndicator[];
  values: Partial<Record<LevelName, ValueMap>>;
  units: Record<string, Unit> | null;
  hierarchy: Hierarchy | null;
  adjacency: Adjacency | null;
  profile: ProfileIndex | null;
  profileSubject: string | null;
  similar: { id: string; distance: number }[];
  change: ChangeFile | null;
  compareId: string | null;
  nameOf: (id: string) => string;
  parentOf: (id: string) => string | null;
  levelOf: (id: string) => LevelName;
  onSelect: (id: string | null) => void;
  onCompare: (id: string | null) => void;
  onLens: (lens: Lens) => void;
  sheetOpen: boolean;
  onSheet: (open: boolean) => void;
  /** Named public features of the selected place's district (local preview only). */
  features?: FeatureFile | null;
};

const CLUSTER_TEXT: Record<ClusterClass, string> = {
  high_high: "Part of a cluster of high values",
  low_low: "Part of a cluster of low values",
  high_low: "A high value among lower neighbours",
  low_high: "A low value among higher neighbours",
};

const KEY_FACTS = [
  "population_total",
  "population_density",
  "occupied_housing_units",
  "persons_per_occupied_housing_unit",
];

function humanise(id: string): string {
  const text = id.replace(/^population_|^households_/, "").replaceAll("_", " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function ordinal(n: number): string {
  const mod100 = n % 100;
  const suffix =
    mod100 >= 11 && mod100 <= 13 ? "th" : (["th", "st", "nd", "rd"][n % 10] ?? "th");
  return `${n.toLocaleString("en-LK")}${suffix}`;
}

function PlaceButton({
  id,
  name,
  onSelect,
  children,
}: {
  id: string;
  name: string;
  onSelect: (id: string) => void;
  children?: React.ReactNode;
}) {
  return (
    <button type="button" className="place-link" onClick={() => onSelect(id)}>
      <span className="place-link-name">{name}</span>
      {children}
    </button>
  );
}

function SourceLine({ label, observation }: { label: string; observation: Observation }) {
  return (
    <li>
      <strong>{label}</strong>
      <span>
        {observation.dataset_id} · period {observation.period} ·{" "}
        {observation.verification.replaceAll("_", " ")}
      </span>
      <span>{observation.source_locator}</span>
      <code>sha256 {observation.snapshot_sha256.slice(0, 16)}…</code>
    </li>
  );
}

export default function PlacePanel(props: Props) {
  const { lens, subject, subjectLevel, known, units, hierarchy, nameOf, parentOf, onSelect } = props;
  const place = useLoaded(known ? () => loadPlace(subject) : null, `place|${subject}`);

  const trail = useMemo(() => {
    const ids: string[] = [];
    let current = parentOf(subject);
    let guard = 0;
    while (current && guard < 6) {
      ids.unshift(current);
      current = parentOf(current);
      guard += 1;
    }
    return ids;
  }, [parentOf, subject]);

  const title = known ? nameOf(subject) : "Place not found";
  const scripts = [place?.geography.name_si, place?.geography.name_ta].filter(Boolean) as string[];

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
          {trail.length === 0 ? (
            <span>Sri Lanka Facts atlas</span>
          ) : (
            trail.map((id) => (
              <button key={id} type="button" onClick={() => onSelect(id === "LK" ? null : id)}>
                {nameOf(id)}
              </button>
            ))
          )}
        </nav>
        <h2>{title}</h2>
        <p className="atlas-panel-sub">
          <span>{LEVEL_SHORT[subjectLevel]}</span>
          {scripts.map((name) => (
            <span key={name} className="atlas-script">
              {name}
            </span>
          ))}
          <code>{subject}</code>
        </p>
      </header>

      <div className="atlas-panel-body">
        {!known ? (
          <p className="atlas-empty">
            No place has the id <code>{subject}</code> in release {props.release}.
          </p>
        ) : lens === "geography" ? (
          <GeographyLens {...props} place={place} />
        ) : lens === "profile" ? (
          <ProfileLens {...props} place={place} />
        ) : lens === "change" ? (
          <ChangeLens {...props} />
        ) : (
          <LandscapeLens {...props} />
        )}

        {known ? (
          <p className="atlas-panel-foot">
            <Link href={`/place/${subject}`}>
              Full record for {title}: every value, with its source
            </Link>
          </p>
        ) : null}
      </div>
      {units && hierarchy ? null : (
        <p className="atlas-panel-loading" role="status">
          Loading places…
        </p>
      )}
    </aside>
  );
}

function HierarchyLists({
  subject,
  subjectLevel,
  hierarchy,
  neighbours,
  childValues,
  neighbourValues,
  format,
  onSelect,
  nameOf,
}: {
  subject: string;
  subjectLevel: LevelName;
  hierarchy: Hierarchy | null;
  neighbours: NeighbourRef[] | null;
  childValues: ValueMap | undefined;
  neighbourValues: ValueMap | undefined;
  format: ((value: number) => string) | null;
  onSelect: (id: string) => void;
  nameOf: (id: string) => string;
}) {
  const next = childLevel(subjectLevel);
  const kids = useMemo(() => {
    const list = [...(hierarchy?.childrenOf.get(subject) ?? [])];
    return list.sort((a, b) => {
      const va = childValues?.get(a.id);
      const vb = childValues?.get(b.id);
      if (va === undefined || vb === undefined) {
        return Number(va === undefined) - Number(vb === undefined) || a.name.localeCompare(b.name);
      }
      return vb - va;
    });
  }, [childValues, hierarchy, subject]);
  const peak = Math.max(...kids.map((kid) => childValues?.get(kid.id) ?? 0), 0);
  const sortedNeighbours = useMemo(
    () =>
      [...(neighbours ?? [])].sort(
        (a, b) => (neighbourValues?.get(b[0]) ?? -Infinity) - (neighbourValues?.get(a[0]) ?? -Infinity),
      ),
    [neighbourValues, neighbours],
  );
  const neighbourPeak = Math.max(...sortedNeighbours.map(([id]) => neighbourValues?.get(id) ?? 0), 0);
  return (
    <>
      {next && kids.length > 0 ? (
        <section className="atlas-section">
          <h3>
            Contains {formatNumber(kids.length)} {LEVEL_PLURAL_TEXT[next]}
          </h3>
          <ul className="place-list">
            {kids.map((kid) => {
              const value = childValues?.get(kid.id);
              return (
                <li key={kid.id}>
                  <PlaceButton id={kid.id} name={kid.name} onSelect={onSelect}>
                    {value !== undefined && format ? (
                      <>
                        <ShareBar share={peak > 0 ? value / peak : 0} />
                        <span className="place-link-value">{format(value)}</span>
                      </>
                    ) : (
                      <span className="place-link-value is-missing">
                        {childValues ? "no value" : ""}
                      </span>
                    )}
                  </PlaceButton>
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}
      {subjectLevel !== "country" ? (
        <section className="atlas-section">
          <h3>Neighbours</h3>
          {neighbours === null ? (
            <p className="atlas-empty">Loading neighbours…</p>
          ) : sortedNeighbours.length === 0 ? (
            <p className="atlas-empty">
              The neighbour graph has no entry for this place, so no neighbours are listed.
            </p>
          ) : (
            <ul className="place-list">
              {sortedNeighbours.map(([id, kind]) => {
                const value = neighbourValues?.get(id);
                return (
                  <li key={id}>
                    <PlaceButton id={id} name={nameOf(id)} onSelect={onSelect}>
                      {kind === 1 ? <span className="tag">nearest, no shared border</span> : null}
                      {value !== undefined && format ? (
                        <>
                          <ShareBar share={neighbourPeak > 0 ? value / neighbourPeak : 0} tone="muted" />
                          <span className="place-link-value">{format(value)}</span>
                        </>
                      ) : null}
                    </PlaceButton>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      ) : null}
    </>
  );
}

function useNeighbours(props: Props): NeighbourRef[] | null {
  const { subject, subjectLevel, adjacency, parentOf } = props;
  const dsId = subjectLevel === "gn" ? parentOf(subject) : null;
  const districtId = dsId ? parentOf(dsId) : null;
  const gnGraph = useLoaded(
    districtId ? () => loadGnAdjacency(districtId) : null,
    `gn-adjacency|${districtId}`,
  );
  if (subjectLevel === "country") {
    return [];
  }
  if (subjectLevel === "gn") {
    return gnGraph ? (gnGraph[subject] ?? []) : null;
  }
  if (!adjacency || subjectLevel === "ed") {
    return null;
  }
  return adjacency[subjectLevel]?.[subject] ?? [];
}

function GeographyLens(
  props: Props & { place: Place | null; landscape?: LandscapeIndicator; similarLabel?: string },
) {
  const { indicator, values, subject, subjectLevel, nameOf, parentOf, levelOf, similar, units, place, landscape } =
    props;
  const neighbours = useNeighbours(props);
  const clusters = useLoaded(
    indicator && !landscape ? () => loadClusters(indicator.id) : null,
    `clusters|${indicator?.id}|${Boolean(landscape)}`,
  );
  if (!indicator) {
    return <p className="atlas-empty">No indicator in this release.</p>;
  }
  const format = (value: number) => formatValue(value, indicator.unit, indicator.decimals);
  const isCount = indicator.measureType === "count";
  const hasLevel = indicator.levels.includes(subjectLevel);
  const levelValues = values[subjectLevel];
  const own = levelValues?.get(subject) ?? null;
  const national = values.country?.get("LK") ?? null;
  const parentId = parentOf(subject);
  const parentLevel = parentId ? levelOf(parentId) : null;
  const parentValue = parentId && parentLevel ? (values[parentLevel]?.get(parentId) ?? null) : null;
  const rank = levelValues ? rankOf(subject, levelValues) : null;
  const neighbourIds = (neighbours ?? []).map(([id]) => id);
  const neighbourSummary = levelValues ? summariseGroup(neighbourIds, levelValues, own) : null;
  const similarIds = subjectLevel === "ds" ? similar.map((item) => item.id) : [];
  const similarSummary = levelValues && similarIds.length ? summariseGroup(similarIds, levelValues, own) : null;
  const clusterClass = (["high_high", "low_low", "high_low", "low_high"] as ClusterClass[]).find(
    (name) =>
      subjectLevel !== "country" &&
      subjectLevel !== "province" &&
      subjectLevel !== "ed" &&
      clusters?.[subjectLevel]?.[name]?.includes(subject),
  );
  const observation = place?.values.find((value) => value.indicator_id === indicator.id) ?? null;
  const small =
    subjectLevel === "district" || subjectLevel === "ds" || subjectLevel === "gn"
      ? (clusters?.[subjectLevel]?.small?.[subject] ?? null)
      : null;

  const markers: Marker[] = [];
  if (own !== null) {
    markers.push({ key: "place", label: nameOf(subject), value: own });
    if (neighbourSummary?.median !== null && neighbourSummary?.median !== undefined) {
      markers.push({ key: "neighbours", label: "Neighbours", value: neighbourSummary.median });
    }
    if (!isCount && parentValue !== null && subjectLevel !== "province") {
      markers.push({ key: "parent", label: "Parent", value: parentValue });
    }
    if (similarSummary?.median !== null && similarSummary?.median !== undefined) {
      markers.push({ key: "similar", label: "Similar", value: similarSummary.median });
    }
    if (!isCount && national !== null) {
      markers.push({ key: "country", label: "Sri Lanka", value: national });
    }
  }

  const facts = KEY_FACTS.map((id) => ({
    id,
    observation: place?.values.find((value) => value.indicator_id === id) ?? null,
    meta: props.indicators.find((item) => item.id === id),
  })).filter((fact) => fact.observation && fact.observation.value !== null && fact.id !== indicator.id);
  const area = units?.[subject]?.a ?? null;

  return (
    <>
      <section className="atlas-section atlas-headline">
        <p className="atlas-kicker">
          {indicator.name} · {landscape ? `${landscape.period} · modelled estimate` : "Census 2024"}
        </p>
        {!hasLevel ? (
          <p className="atlas-empty">
            This indicator is not published for {LEVEL_PLURAL_TEXT[subjectLevel]}. Its
            finest level is the {indicator.levels.includes("ds") ? "DS division" : "district"}.
          </p>
        ) : own === null ? (
          <p className="atlas-empty">
            {levelValues ? "No value is published for this place." : "Loading…"}
          </p>
        ) : (
          <>
            <p className="atlas-figure">{format(own)}</p>
            {subjectLevel !== "country" && rank ? (
              <p className="atlas-rank">
                {ordinal(rank.rank)} highest of {formatNumber(rank.total)}{" "}
                {LEVEL_PLURAL_TEXT[subjectLevel]} with a value. A position, not a
                judgement.
              </p>
            ) : null}
            {small ? (
              <p className="atlas-note" data-testid="small-number-note">
                <span className="tag">small number</span> This figure rests on{" "}
                {small[0] === null ? "fewer than 100" : formatNumber(small[0])} people or
                households, so it can swing widely by chance.
                {small[1] !== null
                  ? ` A smoothed estimate, which leans on the wider pattern, is ${format(small[1])}; it is modelled, not a census figure.`
                  : ""}
              </p>
            ) : null}
          </>
        )}
      </section>

      {own !== null && subjectLevel !== "country" && levelValues ? (
        <section className="atlas-section">
          <h3>Compared to where?</h3>
          <ContextStrip
            values={[...levelValues.values()]}
            markers={markers}
            format={format}
            caption={`${nameOf(subject)} at ${format(own)} on the distribution of all ${LEVEL_PLURAL_TEXT[subjectLevel]}`}
          />
          <dl className="compare">
            <div className="compare-row compare-neighbours">
              <dt>
                <i aria-hidden="true" />
                Neighbours
              </dt>
              {neighbours === null ? (
                <dd className="is-missing">Loading…</dd>
              ) : !neighbourSummary || neighbourSummary.median === null ? (
                <dd className="is-missing">No neighbour has a value.</dd>
              ) : (
                <dd>
                  <strong>{format(neighbourSummary.median)}</strong> median of{" "}
                  {neighbourSummary.withValue}.{" "}
                  <span className={`diff diff-${describeDifference(own, neighbourSummary.median, indicator.unit).direction}`}>
                    {describeDifference(own, neighbourSummary.median, indicator.unit).text}
                  </span>
                  ; higher than {neighbourSummary.lower} of {neighbourSummary.withValue}.
                </dd>
              )}
            </div>
            <div className="compare-row compare-parent">
              <dt>
                <i aria-hidden="true" />
                {parentId ? nameOf(parentId) : "Parent"}
              </dt>
              {parentValue === null ? (
                <dd className="is-missing">No parent value.</dd>
              ) : isCount ? (
                <dd>
                  <strong>{(shareOf(own, parentValue) ?? 0).toFixed(1)}%</strong> of{" "}
                  {nameOf(parentId ?? "")} ({format(parentValue)})
                </dd>
              ) : (
                <dd>
                  <strong>{format(parentValue)}</strong>{" "}
                  <span className={`diff diff-${describeDifference(own, parentValue, indicator.unit).direction}`}>
                    {describeDifference(own, parentValue, indicator.unit).text}
                  </span>
                </dd>
              )}
            </div>
            <div className="compare-row compare-similar">
              <dt>
                <i aria-hidden="true" />
                {props.similarLabel ?? "Similar places"}
              </dt>
              {subjectLevel !== "ds" ? (
                <dd className="is-missing">
                  Similar places are measured between DS divisions only
                  {subjectLevel === "gn" ? " (GN lists are not stable enough to publish)" : ""}.
                </dd>
              ) : !similarSummary || similarSummary.median === null ? (
                <dd className="is-missing">
                  {landscape
                    ? "No landscape neighbours for this division."
                    : props.meta.profile
                      ? "No profile for this division."
                      : "No profile space in this build."}
                </dd>
              ) : (
                <dd>
                  <strong>{format(similarSummary.median)}</strong> median of the{" "}
                  {similarSummary.withValue} most similar.{" "}
                  <span className={`diff diff-${describeDifference(own, similarSummary.median, indicator.unit).direction}`}>
                    {describeDifference(own, similarSummary.median, indicator.unit).text}
                  </span>
                  .{" "}
                  {landscape ? null : (
                    <button type="button" className="text-button" onClick={() => props.onLens("profile")}>
                      Which places, and why
                    </button>
                  )}
                </dd>
              )}
            </div>
            <div className="compare-row compare-country">
              <dt>
                <i aria-hidden="true" />
                Sri Lanka
              </dt>
              {national === null ? (
                <dd className="is-missing">No national value.</dd>
              ) : isCount ? (
                <dd>
                  <strong>{(shareOf(own, national) ?? 0).toFixed(2)}%</strong> of the country (
                  {format(national)})
                </dd>
              ) : (
                <dd>
                  <strong>{format(national)}</strong>{" "}
                  <span className={`diff diff-${describeDifference(own, national, indicator.unit).direction}`}>
                    {describeDifference(own, national, indicator.unit).text}
                  </span>
                </dd>
              )}
            </div>
          </dl>
          {clusterClass ? (
            <p className="atlas-note">
              <strong>{CLUSTER_TEXT[clusterClass]}.</strong> Local Moran&apos;s I, q ≤ 0.05. A
              description of the pattern, not a cause.
            </p>
          ) : null}
          {isCount ? (
            <p className="atlas-note">
              Counts follow how many people or homes a place has. The parent and country rows
              show this place&apos;s share of them.
            </p>
          ) : null}
        </section>
      ) : null}

      <HierarchyLists
        subject={subject}
        subjectLevel={subjectLevel}
        hierarchy={props.hierarchy}
        neighbours={neighbours}
        childValues={(() => {
          const next = childLevel(subjectLevel);
          return next ? values[next] : undefined;
        })()}
        neighbourValues={levelValues}
        format={format}
        onSelect={props.onSelect}
        nameOf={nameOf}
      />

      {facts.length > 0 || area !== null ? (
        <section className="atlas-section">
          <h3>Key facts</h3>
          <dl className="facts">
            {facts.map((fact) => (
              <div key={fact.id}>
                <dt>{fact.meta?.short ?? humanise(fact.id)}</dt>
                <dd>
                  {formatValue(fact.observation?.value ?? null, fact.observation?.unit ?? "", fact.meta?.decimals)}
                </dd>
              </div>
            ))}
            {area !== null ? (
              <div>
                <dt>Area</dt>
                <dd>{formatNumber(area, area < 100 ? 1 : 0)} km²</dd>
              </div>
            ) : null}
          </dl>
        </section>
      ) : null}

      <details className="atlas-sources">
        <summary>Sources for these numbers</summary>
        <ul>
          {landscape ? (
            <li>
              <strong>{landscape.name}</strong>
              <span>
                {landscape.source_name ?? landscape.dataset_id} · period {landscape.period}
                {landscape.time_start && landscape.time_end && landscape.time_start !== landscape.time_end
                  ? ` (${landscape.time_start} to ${landscape.time_end})`
                  : ""}{" "}
                · {landscape.data_nature.replaceAll("_", " ")} · {landscape.verification.replaceAll("_", " ")}
              </span>
              <span>
                Information floor: {landscape.floor}. Licence: {landscape.licence ?? "not recorded"}
                {landscape.commercial_reuse === "yes" ? "" : " (commercial reuse not confirmed)"}.
              </span>
              <span>{landscape.source_locator}</span>
              <code>sha256 {landscape.snapshot_sha256.slice(0, 16)}…</code>
            </li>
          ) : null}
          {observation ? <SourceLine label={indicator.name} observation={observation} /> : null}
          {facts.map((fact) =>
            fact.observation ? (
              <SourceLine
                key={fact.id}
                label={fact.meta?.short ?? humanise(fact.id)}
                observation={fact.observation}
              />
            ) : null,
          )}
          {area !== null ? (
            <li>
              <strong>Area and boundaries</strong>
              <span>COD-AB v03 administrative boundaries (Survey Department, via OCHA), from the geography spine.</span>
              <span>
                Map outlines are simplified for display
                {props.meta.detail_tolerance_m ? ` (${props.meta.detail_tolerance_m} m when zoomed in)` : ""}; areas
                are computed from the unsimplified shapes.
              </span>
            </li>
          ) : null}
          <li>
            <strong>Neighbours</strong>
            <span>
              Units that share at least 10 m of border on the COD-AB v03 boundaries; a unit with
              none gets its 3 nearest. See <Link href="/methods">methods</Link>.
            </span>
          </li>
          {!place && !landscape ? <li>Loading the record…</li> : null}
        </ul>
        <p className="atlas-note">{indicator.definition}</p>
      </details>
    </>
  );
}

function ProfileLens(props: Props & { place: Place | null }) {
  const { profile, profileSubject, subject, subjectLevel, similar, compareId, nameOf, parentOf, indicators, place } = props;
  const names = useMemo(() => new Map(indicators.map((item) => [item.id, item.short])), [indicators]);
  const indicatorName = (id: string) => names.get(id) ?? humanise(id);
  const ranges = useMemo(() => {
    if (!profile) {
      return [];
    }
    return profile.file.axes.map((_, i) => {
      const column = profile.file.vectors.map((vector) => vector[i]);
      return { min: Math.min(...column), max: Math.max(...column) };
    });
  }, [profile]);
  const points = useMemo(
    () =>
      profile
        ? profile.file.ids.map((id, i) => ({
            id,
            x: profile.file.vectors[i][0],
            y: profile.file.vectors[i][1],
          }))
        : [],
    [profile],
  );
  const inside = useMemo(() => {
    if (!profile || subjectLevel === "ds" || subjectLevel === "gn") {
      return [];
    }
    return profile.file.ids
      .map((id, i) => ({ id, percentile: profile.file.percentile[i] }))
      .filter(({ id }) => {
        if (subjectLevel === "country") {
          return true;
        }
        const district = parentOf(id);
        return district === subject || (district ? parentOf(district) === subject : false);
      })
      .sort((a, b) => (b.percentile ?? 0) - (a.percentile ?? 0));
  }, [parentOf, profile, subject, subjectLevel]);

  if (!props.meta.profile) {
    return (
      <p className="atlas-empty">
        This build has no profile space. Run <code>slf atlas export --profile-dir …</code> to add
        it.
      </p>
    );
  }
  if (!profile) {
    return <p className="atlas-empty">Loading the profile space…</p>;
  }
  const file = profile.file;
  const method = (
    <details className="atlas-sources">
      <summary>How similarity is measured</summary>
      <p className="atlas-note">
        Space <code>{file.space_id}</code> v{file.space_version}, {file.period}: each DS division
        is a point on {file.axes.length} axes kept from a principal component analysis of
        standardised census inputs (demography, housing, and ethnic group and religion shares),
        with each block weighted equally. Similarity is the straight-line distance between two
        points. The squared distance is a sum over axes, so each axis&apos;s share is exact.
      </p>
      <p className="atlas-note">
        {file.note} Axis names are machine-drafted and not yet reviewed. See{" "}
        <Link href="/methods">methods</Link>.
      </p>
    </details>
  );

  if (!profileSubject) {
    return (
      <>
        <section className="atlas-section">
          <p className="atlas-kicker">Profile space v{file.space_version}</p>
          <p>
            Profiles are measured for DS divisions. Pick one on the map, in the chart, or from
            the list to see the places most like it and why.
          </p>
          <Scatter
            points={points}
            selected={null}
            compare={null}
            near={new Set(inside.length < points.length ? inside.map((item) => item.id) : [])}
            onPick={(id) => props.onSelect(id)}
            nameOf={nameOf}
          />
          <p className="atlas-note">
            Each dot is a DS division on the first two axes. Dots near each other have similar
            profiles. This is a flat view of a {file.axes.length}-axis space, for orientation
            only.
            {inside.length < points.length && inside.length > 0
              ? ` Highlighted: the ${inside.length} divisions in ${nameOf(subject)}.`
              : ""}
          </p>
        </section>
        <section className="atlas-section">
          <h3>
            {subjectLevel === "country" ? "Least like the average division" : `DS divisions in ${nameOf(subject)}`}
          </h3>
          <ul className="place-list">
            {inside.slice(0, subjectLevel === "country" ? 12 : 40).map((item) => (
              <li key={item.id}>
                <PlaceButton id={item.id} name={nameOf(item.id)} onSelect={(id) => props.onSelect(id)}>
                  <ShareBar share={(item.percentile ?? 0) / 100} />
                  <span className="place-link-value">
                    {item.percentile === null ? "" : `farther than ${Math.round(item.percentile)}%`}
                  </span>
                </PlaceButton>
              </li>
            ))}
          </ul>
          <p className="atlas-note">
            &ldquo;Farther than 90%&rdquo; means the division is farther from the national centre
            than 90% of divisions: unusual, not better or worse.
          </p>
        </section>
        {method}
      </>
    );
  }

  const row = profile.row.get(profileSubject) ?? 0;
  const vector = file.vectors[row];
  const all = distancesFrom(profile, profileSubject) ?? new Map<string, number>();
  const compare = compareId && profile.row.has(compareId) ? explainPair(profile, profileSubject, compareId) : null;
  const compareVector = compareId && profile.row.has(compareId) ? file.vectors[profile.row.get(compareId) ?? 0] : null;
  const reasons = compareId ? pipelineReasons(profile, profileSubject, compareId) : null;
  const contrasts = file.contrasts
    .filter(([a, b]) => a === profileSubject || b === profileSubject)
    .map(([a, b, d, pct, flagged]) => ({ id: a === profileSubject ? b : a, distance: d, percentile: pct, flagged }))
    .sort((a, b) => b.distance - a.distance);
  const gnProfile = subjectLevel === "gn" ? place?.profile : null;

  return (
    <>
      {subjectLevel === "gn" ? (
        <section className="atlas-section">
          <p className="atlas-note">
            Similar-place lists are not published for GN divisions: they change too much under
            ordinary small-number variation. What follows is for {nameOf(profileSubject)}, the DS
            division this GN is in.
            {gnProfile
              ? ` This GN itself is farther from the national centre than ${Math.round(gnProfile.percentile)}% of GN divisions.`
              : ""}
          </p>
        </section>
      ) : null}

      <section className="atlas-section">
        <p className="atlas-kicker">How unusual · profile space v{file.space_version}</p>
        <p className="atlas-figure atlas-figure-small">
          Farther from the centre than {Math.round(file.percentile[row] ?? 0)}% of divisions
        </p>
        <p className="atlas-note">
          Distance {file.norm[row].toFixed(2)} from the national centre. Most distinctive inputs:{" "}
          {file.top_indicators[row].map(indicatorName).join(", ") || "none listed"}. Unusual is
          not better or worse.
        </p>
      </section>

      {compare && compareId ? (
        <section className="atlas-section atlas-compare">
          <h3>
            {nameOf(profileSubject)} and {nameOf(compareId)}
          </h3>
          <p>
            Distance <strong>{compare.distance.toFixed(2)}</strong>: the{" "}
            {ordinal(Math.round((percentileAmong(compare.distance, all.values()) / 100) * all.size) + 1)}{" "}
            nearest of {all.size} DS divisions to {nameOf(profileSubject)}.
          </p>
          <table className="axis-table">
            <caption>Where the distance comes from, axis by axis</caption>
            <thead>
              <tr>
                <th scope="col">Axis (draft name)</th>
                <th scope="col">Positions</th>
                <th scope="col">Share</th>
              </tr>
            </thead>
            <tbody>
              {[...compare.axes]
                .map((axis, i) => ({ axis, i }))
                .sort((a, b) => b.axis.share - a.axis.share)
                .map(({ axis, i }) => (
                  <tr key={axis.axis}>
                    <th scope="row">{axis.label}</th>
                    <td>
                      <AxisBar value={axis.a} other={axis.b} min={ranges[i].min} max={ranges[i].max} />
                    </td>
                    <td>{Math.round(axis.share * 100)}%</td>
                  </tr>
                ))}
            </tbody>
          </table>
          {reasons ? (
            <dl className="reasons">
              <div>
                <dt>Most alike in</dt>
                <dd>{reasons.alike.map((item) => indicatorName(item.indicator)).join(", ")}</dd>
              </div>
              <div>
                <dt>Differ most in</dt>
                <dd>
                  {reasons.different
                    .map((item) => `${indicatorName(item.indicator)} (${Math.round(item.share * 100)}% of the distance)`)
                    .join(", ")}
                </dd>
              </div>
            </dl>
          ) : (
            <p className="atlas-note">
              Input-level reasons are precomputed for each division&apos;s {file.similar.k} nearest
              only; this pair is farther apart than that.
            </p>
          )}
          <p className="atlas-actions">
            <button type="button" className="text-button" onClick={() => props.onSelect(compareId)}>
              Go to {nameOf(compareId)}
            </button>
            <button type="button" className="text-button" onClick={() => props.onCompare(null)}>
              Close comparison
            </button>
          </p>
        </section>
      ) : null}

      <section className="atlas-section">
        <h3>Places like this</h3>
        <ol className="place-list place-list-similar">
          {similar.map((item) => {
            const why = pipelineReasons(profile, profileSubject, item.id);
            const district = parentOf(item.id);
            return (
              <li key={item.id} className={item.id === compareId ? "is-active" : ""}>
                <button type="button" className="place-link" onClick={() => props.onCompare(item.id)}>
                  <span className="place-link-name">
                    {nameOf(item.id)}
                    {district ? <small>{nameOf(district)}</small> : null}
                  </span>
                  <span className="place-link-value">{item.distance.toFixed(2)}</span>
                  {why ? (
                    <span className="place-link-why">
                      Alike in {why.alike.slice(0, 2).map((r) => indicatorName(r.indicator).toLowerCase()).join(", ")}
                      ; differs most in {indicatorName(why.different[0]?.indicator ?? "").toLowerCase()}
                    </span>
                  ) : null}
                </button>
              </li>
            );
          })}
        </ol>
        <p className="atlas-note">
          The 10 nearest DS divisions, with their distance. Select one to see where the distance
          comes from. They are ringed on the map. Similarity is not a ranking.
        </p>
      </section>

      <section className="atlas-section">
        <h3>The similarity map</h3>
        <Scatter
          points={points}
          selected={profileSubject}
          compare={compareId}
          near={new Set(similar.map((item) => item.id))}
          onPick={(id) => (id === profileSubject ? undefined : props.onCompare(id))}
          nameOf={nameOf}
        />
        <p className="atlas-note">
          Every DS division on the first two axes ({Math.round((file.axes[0].variance_explained + file.axes[1].variance_explained) * 100)}%
          of the variance). A flat view for orientation; distances use all {file.axes.length} axes.
        </p>
      </section>

      <section className="atlas-section">
        <h3>Position on each axis</h3>
        <ul className="axis-list">
          {file.axes.map((axis, i) => (
            <li key={axis.axis}>
              <span className="axis-name">
                {axis.draft_label}
                <small>
                  {Math.round(axis.variance_explained * 100)}% of variance · draft name
                </small>
              </span>
              <AxisBar value={vector[i]} other={compareVector?.[i]} min={ranges[i].min} max={ranges[i].max} />
            </li>
          ))}
        </ul>
      </section>

      {contrasts.length > 0 ? (
        <section className="atlas-section">
          <h3>Near here, unlike here</h3>
          <ul className="place-list">
            {contrasts.map((item) => (
              <li key={item.id}>
                <button type="button" className="place-link" onClick={() => props.onCompare(item.id)}>
                  <span className="place-link-name">{nameOf(item.id)}</span>
                  {item.flagged ? <span className="tag">sharp contrast</span> : null}
                  <ShareBar share={item.percentile / 100} tone="muted" />
                  <span className="place-link-value">{item.distance.toFixed(2)}</span>
                </button>
              </li>
            ))}
          </ul>
          <p className="atlas-note">
            Bordering DS divisions by profile distance. The bar shows where the pair sits among
            all bordering pairs in the country.
          </p>
        </section>
      ) : null}
      {method}
    </>
  );
}

function ChangeLens(props: Props) {
  const { change, subject, subjectLevel, nameOf, parentOf } = props;
  if (!props.meta.change) {
    return (
      <p className="atlas-empty">
        This build has no census history. Run <code>slf atlas export --history-dir …</code> to add
        it.
      </p>
    );
  }
  if (!change) {
    return <p className="atlas-empty">Loading census change…</p>;
  }
  const row = change.ds.find((item) => item.id === subject) ?? null;
  const within = change.ds
    .filter((item) => {
      if (subjectLevel === "district") {
        return parentOf(item.id) === subject;
      }
      if (subjectLevel === "province") {
        const district = parentOf(item.id);
        return district ? parentOf(district) === subject : false;
      }
      return false;
    })
    .sort((a, b) => (b.growth_pct ?? -Infinity) - (a.growth_pct ?? -Infinity));
  const series = change.national
    .filter((point) => point.population !== null)
    .map((point) => ({ year: point.year, value: point.population as number }));
  const persons = (value: number | null) => (value === null ? "not available" : formatNumber(value));
  const growthMedian = median(change.ds.map((item) => item.growth_pct).filter((v): v is number => v !== null));
  const sources = (
    <details className="atlas-sources">
      <summary>Sources and status</summary>
      <p className="atlas-note">{change.note}</p>
      <ul>
        {change.sources.map((source) => (
          <li key={source.id}>
            <strong>{source.id}</strong>
            <span>{source.url}</span>
            <span>retrieved {source.retrieved_at} · {source.licence_note}</span>
            <code>sha256 {source.sha256?.slice(0, 16)}…</code>
          </li>
        ))}
      </ul>
    </details>
  );

  if (subjectLevel === "gn") {
    return (
      <>
        <p className="atlas-empty">
          Change is measured for DS divisions. GN boundaries and lists changed between 2012 and
          2024, and no GN-level comparison is built.
        </p>
        {parentOf(subject) ? (
          <p>
            <button type="button" className="text-button" onClick={() => props.onSelect(parentOf(subject))}>
              See {nameOf(parentOf(subject) ?? "")}
            </button>
          </p>
        ) : null}
        {sources}
      </>
    );
  }

  if (subjectLevel === "ds") {
    return (
      <>
        <section className="atlas-section atlas-headline">
          <p className="atlas-kicker">Population, census 2012 to census 2024</p>
          {!row || row.growth_pct === null ? (
            <p className="atlas-empty">No 2012 to 2024 comparison exists for this division.</p>
          ) : (
            <>
              <p className="atlas-figure">
                {row.growth_pct > 0 ? "+" : ""}
                {row.growth_pct}%
              </p>
              <p className="atlas-rank">
                {persons(row.pop_2012)} in 2012, {persons(row.pop_2024)} in 2024 (
                {row.annual_rate_pct !== null ? `${row.annual_rate_pct}% a year` : "rate not available"}). The
                median DS division changed by {growthMedian?.toFixed(1)}%.
              </p>
              <p className={`atlas-note comparison-${row.comparison}`}>
                <strong>{row.comparison === "exact" ? "Exact comparison." : "Approximate comparison."}</strong>{" "}
                {row.reason ?? ""} ({row.change_type.replaceAll("_", " ")}; method {row.method.replaceAll("_", " ")})
              </p>
            </>
          )}
        </section>
        {sources}
      </>
    );
  }

  const total = change.areas?.find((item) => item.id === subject) ?? null;

  return (
    <>
      {total ? (
        <section className="atlas-section atlas-headline" data-testid="change-area-total">
          <p className="atlas-kicker">Population, census 2012 to census 2024</p>
          <p className="atlas-figure">
            {total.growth_pct > 0 ? "+" : ""}
            {total.growth_pct}%
          </p>
          <p className="atlas-rank">
            {persons(total.pop_2012)} in 2012, {persons(total.pop_2024)} in 2024: the sum of{" "}
            {total.ds_rows} DS divisions.
            {total.approximate > 0
              ? ` ${total.approximate} of them changed their GN lists, which moves people between divisions but not out of this total unless a GN crossed its border.`
              : ""}
          </p>
          {change.not_mapped?.length ? (
            <p className="atlas-note">
              Counted in the totals but not drawn on the map, because the boundary source has no
              unit for it: {change.not_mapped.join(", ")}.
            </p>
          ) : null}
        </section>
      ) : null}
      {subjectLevel === "country" ? (
        <section className="atlas-section">
          <p className="atlas-kicker">Sri Lanka at each census, {series[0]?.year} to {series[series.length - 1]?.year}</p>
          <Series points={series} format={(value) => formatNumber(value)} />
          <table className="mini-table">
            <caption className="visually-hidden">Population at each census</caption>
            <thead>
              <tr>
                <th scope="col">Census</th>
                <th scope="col">Population</th>
                <th scope="col">Source</th>
              </tr>
            </thead>
            <tbody>
              {change.national.map((point) => (
                <tr key={point.year}>
                  <th scope="row">{point.year}</th>
                  <td>{point.population === null ? "–" : formatNumber(point.population)}</td>
                  <td>
                    {point.source}
                    {point.page ? `, p. ${point.page}` : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="atlas-note">
            Figures before 2012 are rounded from thousands in the source table. The map shows
            change by DS division between 2012 and 2024; select a district or division.
          </p>
        </section>
      ) : (
        <section className="atlas-section">
          <h3>
            DS divisions in {nameOf(subject)}, 2012 to 2024
          </h3>
          <ul className="place-list">
            {within.map((item) => (
              <li key={item.id}>
                <PlaceButton id={item.id} name={nameOf(item.id)} onSelect={(id) => props.onSelect(id)}>
                  {item.comparison !== "exact" ? <span className="tag">approximate</span> : null}
                  <span className="place-link-value">
                    {item.growth_pct === null ? "no comparison" : `${item.growth_pct > 0 ? "+" : ""}${item.growth_pct}%`}
                  </span>
                </PlaceButton>
              </li>
            ))}
          </ul>
          <p className="atlas-note">
            No total is shown for {nameOf(subject)}: a district series exists in the history
            build but is keyed by name only, so it is not joined here.
          </p>
        </section>
      )}
      {sources}
    </>
  );
}

function LandscapeLens(props: Props) {
  const landscape = props.lens === "landscape" ? (props.indicator as LandscapeIndicator | undefined) : undefined;
  const similarFile = useLoaded(props.meta.landscape ? loadLandscapeSimilar : null, `landscape-similar|${props.meta.landscape}`);
  const similar = useMemo(
    () =>
      props.subjectLevel === "ds"
        ? (similarFile?.places[props.subject] ?? []).map(([id, distance]) => ({ id, distance }))
        : [],
    [props.subject, props.subjectLevel, similarFile],
  );
  if (!props.meta.landscape) {
    return (
      <section className="atlas-section">
        <p className="atlas-kicker">Landscape</p>
        <p className="atlas-empty">
          This build has no landscape layers. They come from <code>uv run slf spatial build</code>{" "}
          and <code>slf atlas export --landscape-dir</code>.
        </p>
      </section>
    );
  }
  if (!landscape) {
    return <p className="atlas-empty">Loading landscape layers…</p>;
  }
  return (
    <>
      <p className="atlas-note atlas-landscape-note">
        <span className="tag">modelled estimate</span> Measured from satellite and open map data,
        not from the census. Information floor: <strong>{landscape.floor}</strong>; values for a
        place are sums or shares of the pixels or features whose centre lies inside it.
      </p>
      <GeographyLens
        {...props}
        place={null}
        landscape={landscape}
        similar={similar}
        similarLabel="Similar landscapes"
      />
      <WhatsHere {...props} />
      {similar.length && similarFile ? (
        <section className="atlas-section">
          <h3>Most similar landscapes</h3>
          <ol className="plain-list">
            {similar.slice(0, 5).map((item) => (
              <li key={item.id}>
                <button type="button" className="text-button" onClick={() => props.onSelect(item.id)}>
                  {props.nameOf(item.id)}
                </button>{" "}
                <small className="muted">distance {item.distance.toFixed(2)}</small>
              </li>
            ))}
          </ol>
          <p className="atlas-note">
            Distance in the <code>{similarFile.space_id}</code> space v{similarFile.space_version}{" "}
            (terrain, land cover and change; D-045, proposed). Axis names are machine drafts.
          </p>
        </section>
      ) : null}
    </>
  );
}


const FEATURE_TITLES: Record<string, string> = {
  school: "Schools",
  health: "Health facilities",
  heritage: "Wikidata places",
  place: "Place names (GeoNames)",
};

/** Named public features inside the selected GN (listed) or DS (counted). */
function WhatsHere(props: Props) {
  const { features, subject, subjectLevel, parentOf } = props;
  if (!features || (subjectLevel !== "gn" && subjectLevel !== "ds")) {
    return null;
  }
  const inside = features.points.filter((point) =>
    subjectLevel === "gn" ? point[5] === subject : parentOf(point[5]) === subject,
  );
  const byKind = new Map<string, typeof inside>();
  for (const point of inside) {
    byKind.set(point[2], [...(byKind.get(point[2]) ?? []), point]);
  }
  return (
    <section className="atlas-section" data-testid="whats-here">
      <h3>What is here</h3>
      {inside.length === 0 ? (
        <p className="atlas-empty">No named school, health facility or place is mapped inside.</p>
      ) : (
        [...byKind.entries()].map(([kind, points]) => (
          <div key={kind} className="whats-here-group">
            <p className="atlas-kicker">
              {FEATURE_TITLES[kind] ?? kind} · {points.length}
            </p>
            {subjectLevel === "gn" ? (
              <ul className="plain-list">
                {points.slice(0, 12).map((point) => (
                  <li key={`${point[0]},${point[1]},${point[3]}`}>
                    {point[3]}
                    {point[4] ? <small className="muted"> · {point[4].replaceAll("|", ", ").replaceAll("_", " ")}</small> : null}
                  </li>
                ))}
                {points.length > 12 ? <li className="muted">and {points.length - 12} more</li> : null}
              </ul>
            ) : null}
          </div>
        ))
      )}
      <p className="atlas-note">
        From open map and registry data (Giga, healthsites.io and OpenStreetMap, Wikidata,
        GeoNames), placed in a division by its point. Mapping is incomplete and uneven; an
        empty list does not mean there is nothing there. Names only: no addresses or people.
      </p>
    </section>
  );
}
