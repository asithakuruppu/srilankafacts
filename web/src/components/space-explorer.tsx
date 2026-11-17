"use client";

import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import AtlasMap, { type AtlasMapHandle } from "@/components/atlas/atlas-map";
import { loadAdjacency, loadSpace, loadUnits } from "@/lib/atlas/data";
import {
  axisShares,
  blockShares,
  compositeVectors,
  distancesIn,
  farAlike,
  nearestIn,
  pointSpace,
  type CompositeFile,
  type PointSpace,
  type Question,
  type TrajectoryFile,
  type TypologyFile,
} from "@/lib/atlas/spaces";
import { PROXIMITY, rampFor } from "@/lib/atlas/scale";
import { classIndex, quantileBreaks } from "@/lib/atlas/context";
import { useLoaded } from "@/lib/atlas/use-loaded";

type SpaceName = "profile" | "trajectory";
type Flags = { typology: boolean; composite: boolean; trajectory: boolean; text: boolean };

/** Categorical colours for types, readable in both themes; order is not a ranking. */
const TYPE_COLOURS = ["#3f5cc6", "#c98a00", "#1f8a70", "#c2571a", "#8a55c4", "#2a8fbd", "#b0417a", "#6d7a1f", "#7a5c3e", "#5a6070"];

const QUESTIONS: { id: Question; label: string }[] = [
  { id: "like", label: "Places like this" },
  { id: "near_unlike", label: "Near here, unlike here" },
  { id: "far_like", label: "Far away, like here" },
  { id: "unusual", label: "How unusual is this place?" },
];

const FAR_KM = 100;
const K = 10;

function useTheme(): "light" | "dark" {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const read = () => {
      const chosen = document.documentElement.dataset.theme;
      setTheme(chosen === "dark" || chosen === "light" ? chosen : media.matches ? "dark" : "light");
    };
    read();
    media.addEventListener("change", read);
    const observer = new MutationObserver(read);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => {
      media.removeEventListener("change", read);
      observer.disconnect();
    };
  }, []);
  return theme;
}

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function parseWeights(text: string | null, n: number): number[] {
  const parts = (text ?? "").split(",").map((part) => (part.trim() === "" ? NaN : Number(part)));
  return Array.from({ length: n }, (_, i) =>
    Number.isFinite(parts[i]) && parts[i] >= 0 && parts[i] <= 2 ? parts[i] : 1,
  );
}

/** 2-D view of the first two axes, with click to select and drag to brush. */
function SimilarityView({
  space,
  selected,
  near,
  brushed,
  colourOf,
  nameOf,
  onPick,
  onBrush,
  axisLabels,
}: {
  space: PointSpace;
  selected: string | null;
  near: Set<string>;
  brushed: Set<string>;
  colourOf: (id: string) => string;
  nameOf: (id: string) => string;
  onPick: (id: string) => void;
  onBrush: (ids: string[]) => void;
  axisLabels: [string, string];
}) {
  const width = 440;
  const height = 360;
  const pad = 18;
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [drag, setDrag] = useState<{ x0: number; y0: number; x1: number; y1: number } | null>(null);
  const xs = space.vectors.map((v) => v[0]);
  const ys = space.vectors.map((v) => v[1] ?? 0);
  const [minX, maxX, minY, maxY] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const sx = (v: number) => pad + ((v - minX) / (maxX - minX || 1)) * (width - 2 * pad);
  const sy = (v: number) => height - pad - ((v - minY) / (maxY - minY || 1)) * (height - 2 * pad);
  const local = (event: React.PointerEvent) => {
    const box = svgRef.current?.getBoundingClientRect();
    if (!box) {
      return { x: 0, y: 0 };
    }
    return {
      x: ((event.clientX - box.left) / box.width) * width,
      y: ((event.clientY - box.top) / box.height) * height,
    };
  };
  const rank = (id: string) => (id === selected ? 3 : brushed.has(id) ? 2 : near.has(id) ? 1 : 0);
  const order = space.ids.map((id, i) => ({ id, i })).sort((a, b) => rank(a.id) - rank(b.id));
  return (
    <svg
      ref={svgRef}
      className="space-view"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={`DS divisions on the first two axes (${axisLabels[0]}; ${axisLabels[1]}). A flat view: distances use all axes.`}
      onPointerDown={(event) => {
        if ((event.target as Element).tagName === "circle") {
          return;
        }
        const p = local(event);
        (event.currentTarget as Element).setPointerCapture(event.pointerId);
        setDrag({ x0: p.x, y0: p.y, x1: p.x, y1: p.y });
      }}
      onPointerMove={(event) => {
        if (drag) {
          const p = local(event);
          setDrag({ ...drag, x1: p.x, y1: p.y });
        }
      }}
      onPointerUp={() => {
        if (!drag) {
          return;
        }
        const [x0, x1] = [Math.min(drag.x0, drag.x1), Math.max(drag.x0, drag.x1)];
        const [y0, y1] = [Math.min(drag.y0, drag.y1), Math.max(drag.y0, drag.y1)];
        setDrag(null);
        if (x1 - x0 < 4 && y1 - y0 < 4) {
          onBrush([]);
          return;
        }
        onBrush(
          space.ids.filter((_, i) => {
            const x = sx(space.vectors[i][0]);
            const y = sy(space.vectors[i][1] ?? 0);
            return x >= x0 && x <= x1 && y >= y0 && y <= y1;
          }),
        );
      }}
    >
      <line className="scatter-zero" x1={sx(0)} x2={sx(0)} y1={0} y2={height} />
      <line className="scatter-zero" x1={0} x2={width} y1={sy(0)} y2={sy(0)} />
      {order.map(({ id, i }) => {
        const r = rank(id);
        return (
          <circle
            key={id}
            data-id={id}
            className={`space-dot ${r === 3 ? "is-selected" : r === 2 ? "is-brushed" : r === 1 ? "is-near" : ""}`}
            cx={sx(space.vectors[i][0])}
            cy={sy(space.vectors[i][1] ?? 0)}
            r={r === 3 ? 6 : r ? 4.5 : 3}
            fill={colourOf(id)}
            onClick={() => onPick(id)}
          >
            <title>{nameOf(id)}</title>
          </circle>
        );
      })}
      {drag ? (
        <rect
          className="space-brush"
          x={Math.min(drag.x0, drag.x1)}
          y={Math.min(drag.y0, drag.y1)}
          width={Math.abs(drag.x1 - drag.x0)}
          height={Math.abs(drag.y1 - drag.y0)}
        />
      ) : null}
    </svg>
  );
}

export default function SpaceExplorer({ spaces }: { spaces: Flags }) {
  const params = useSearchParams();
  const theme = useTheme();
  const mapRef = useRef<AtlasMapHandle | null>(null);
  const units = useLoaded(loadUnits, "units");
  const adjacency = useLoaded(loadAdjacency, "adjacency");
  const typology = useLoaded(
    spaces.typology ? () => loadSpace<TypologyFile>("typology") : null,
    "typology",
  );
  const composite = useLoaded(
    spaces.composite ? () => loadSpace<CompositeFile>("composite") : null,
    "composite",
  );
  const trajectory = useLoaded(
    spaces.trajectory ? () => loadSpace<TrajectoryFile>("trajectory") : null,
    "trajectory",
  );

  const [initial] = useState(() => ({
    place: params.get("place"),
    space: (params.get("space") === "trajectory" && spaces.trajectory ? "trajectory" : "profile") as SpaceName,
    question: (QUESTIONS.some((q) => q.id === params.get("q")) ? params.get("q") : "like") as Question,
    weights: params.get("w"),
    colour: params.get("colour") === "distance" ? "distance" : "type",
  }));
  const [selected, setSelected] = useState<string | null>(initial.place);
  const [spaceName, setSpaceName] = useState<SpaceName>(initial.space);
  const [question, setQuestion] = useState<Question>(initial.question);
  const [colourBy, setColourBy] = useState<"type" | "distance">(initial.colour as "type" | "distance");
  const [weightsText, setWeightsText] = useState<string | null>(initial.weights);
  const [brushed, setBrushed] = useState<Set<string>>(new Set());
  const [compare, setCompare] = useState<string | null>(null);
  const [mapError, setMapError] = useState<string | null>(null);

  const weights = useMemo(
    () => parseWeights(weightsText, composite?.blocks.length ?? 3),
    [composite, weightsText],
  );
  const nameOf = useCallback((id: string) => units?.[id]?.n ?? id, [units]);
  const parentOf = useCallback((id: string) => units?.[id]?.p ?? null, [units]);

  const space = useMemo<PointSpace | null>(() => {
    if (spaceName === "trajectory") {
      return trajectory ? pointSpace(trajectory.ids, trajectory.vectors) : null;
    }
    return composite ? pointSpace(composite.ids, compositeVectors(composite, weights)) : null;
  }, [composite, spaceName, trajectory, weights]);

  const typeOf = useMemo(
    () => new Map((typology?.ids ?? []).map((id, i) => [id, typology!.type_of[i]])),
    [typology],
  );
  const subject = selected && space?.row.has(selected) ? selected : null;

  const labelPoints = useMemo(() => {
    const out = new Map<string, [number, number]>();
    for (const [id, unit] of Object.entries(units ?? {})) {
      if (unit.l === 3 && unit.c) {
        out.set(id, unit.c);
      }
    }
    return out;
  }, [units]);

  // The answer to the chosen question: a list of places with a distance and a note.
  const answer = useMemo<{ id: string; distance: number; note?: string }[]>(() => {
    if (!space || !subject) {
      return [];
    }
    if (question === "like") {
      return nearestIn(space, subject, K);
    }
    if (question === "far_like") {
      return farAlike(space, subject, labelPoints, FAR_KM, K).map((item) => ({
        ...item,
        note: `${Math.round(item.km)} km away`,
      }));
    }
    if (question === "near_unlike") {
      const all = distancesIn(space, subject);
      return (adjacency?.ds?.[subject] ?? [])
        .filter(([id]) => all.has(id))
        .map(([id, kind]) => ({
          id,
          distance: all.get(id) ?? 0,
          note: kind === 1 ? "nearest, no shared border" : "shares a border",
        }))
        .sort((a, b) => b.distance - a.distance);
    }
    return [];
  }, [adjacency, labelPoints, question, space, subject]);

  const unusual = useMemo(() => {
    if (!space || !subject) {
      return null;
    }
    const dims = space.vectors[0]?.length ?? 0;
    const centre = new Array<number>(dims).fill(0);
    for (const v of space.vectors) {
      v.forEach((x, i) => (centre[i] += x / space.vectors.length));
    }
    const fromCentre = space.vectors.map((v) => Math.hypot(...v.map((x, i) => x - centre[i])));
    const own = fromCentre[space.row.get(subject) ?? 0];
    const below = fromCentre.filter((d) => d < own).length;
    return { distance: own, percentile: (below / fromCentre.length) * 100 };
  }, [space, subject]);

  const near = useMemo(() => new Set(answer.map((item) => item.id)), [answer]);

  const colours = useMemo(() => {
    const map = new Map<string, string>();
    if (colourBy === "distance" && space && subject) {
      const ramp = rampFor(PROXIMITY, theme);
      const all = distancesIn(space, subject);
      const breaks = quantileBreaks([...all.values()], 5);
      for (const [id, d] of all) {
        map.set(id, ramp[Math.min(classIndex(d, breaks), 4)]);
      }
      map.set(subject, theme === "dark" ? "#8da6ff" : "#1c3fae");
      return map;
    }
    for (const [id, type] of typeOf) {
      map.set(id, TYPE_COLOURS[(type - 1) % TYPE_COLOURS.length]);
    }
    return map;
  }, [colourBy, space, subject, theme, typeOf]);

  const colourOf = useCallback((id: string) => colours.get(id) ?? "#9aa0ad", [colours]);

  // Every view has a URL.
  useEffect(() => {
    const query = new URLSearchParams();
    if (selected) {
      query.set("place", selected);
    }
    if (spaceName !== "profile") {
      query.set("space", spaceName);
    }
    if (question !== "like") {
      query.set("q", question);
    }
    if (weights.some((w) => w !== 1) && spaceName === "profile") {
      query.set("w", weights.join(","));
    }
    if (colourBy !== "type") {
      query.set("colour", colourBy);
    }
    const text = query.toString();
    window.history.replaceState(null, "", text ? `/explore/space?${text}` : "/explore/space");
  }, [colourBy, question, selected, spaceName, weights]);

  const pick = useCallback((id: string | null) => {
    setSelected(id);
    setCompare(null);
  }, []);

  const highlight = useMemo(() => [...new Set([...near, ...brushed])], [brushed, near]);

  const reasons = useMemo(() => {
    if (!subject || !compare || !space) {
      return null;
    }
    if (spaceName === "profile" && composite) {
      return { kind: "profile" as const, shares: blockShares(composite, weights, subject, compare) };
    }
    return { kind: "trajectory" as const, shares: axisShares(space, subject, compare) };
  }, [compare, composite, space, spaceName, subject, weights]);

  const axisNames: [string, string] =
    spaceName === "trajectory"
      ? [trajectory?.axes[0]?.label ?? "axis 1", trajectory?.axes[1]?.label ?? "axis 2"]
      : [composite?.axes[0]?.draft_label ?? "axis 1", composite?.axes[1]?.draft_label ?? "axis 2"];
  const version =
    spaceName === "trajectory"
      ? `trajectory v${trajectory?.space_version ?? ""}`
      : `composite v${composite?.space_version ?? ""} (profile v${composite?.base.space_version ?? ""}${weights.some((w) => w !== 1) ? ", reweighted" : ""})`;

  return (
    <div className="space-explorer">
      <div className="space-controls" role="group" aria-label="Space and question">
        <label>
          <span>Space</span>
          <select value={spaceName} onChange={(e) => setSpaceName(e.target.value as SpaceName)}>
            <option value="profile">Profile: what places are like (2024)</option>
            {spaces.trajectory ? (
              <option value="trajectory">Trajectory: how places changed, 2012–2024 (private)</option>
            ) : null}
          </select>
        </label>
        <label>
          <span>Colour by</span>
          <select value={colourBy} onChange={(e) => setColourBy(e.target.value as "type" | "distance")}>
            <option value="type">Type (machine-drafted groups)</option>
            <option value="distance">Distance from the selected place</option>
          </select>
        </label>
        <div className="space-questions" role="group" aria-label="Question">
          {QUESTIONS.map((q) => (
            <button
              key={q.id}
              type="button"
              aria-pressed={question === q.id}
              className={question === q.id ? "is-active" : ""}
              onClick={() => setQuestion(q.id)}
            >
              {q.label}
            </button>
          ))}
        </div>
      </div>

      {spaceName === "profile" && composite ? (
        <fieldset className="space-weights">
          <legend>Weights (composite space): how much each block counts</legend>
          {composite.blocks.map((block, b) => (
            <label key={block.id}>
              <span>
                {block.label} <small>({block.inputs} inputs)</small>
              </span>
              <input
                type="range"
                min={0}
                max={2}
                step={0.25}
                value={weights[b]}
                aria-valuetext={`${weights[b]}`}
                onChange={(e) => {
                  const next = [...weights];
                  next[b] = Number(e.target.value);
                  setWeightsText(next.join(","));
                }}
              />
              <output>{weights[b].toFixed(2)}</output>
            </label>
          ))}
          <button type="button" onClick={() => setWeightsText(null)} disabled={weights.every((w) => w === 1)}>
            Equal weights (profile v{composite.base.space_version})
          </button>
        </fieldset>
      ) : null}
      {spaceName === "trajectory" && trajectory ? (
        <p className="notice">
          {trajectory.note} {trajectory.excluded.length} divisions are not in this space (no
          one-to-one 2012 predecessor); {trajectory.comparison.filter((c) => c === "approximate").length}{" "}
          of {trajectory.ids.length} comparisons are approximate.
        </p>
      ) : null}

      <div className="space-split">
        <section className="space-map" aria-label="Geography">
          <h2 className="visually-hidden">Geography</h2>
          <div className="space-map-box">
            <AtlasMap
              ref={mapRef}
              theme={theme}
              level="ds"
              colors={colours}
              selected={subject ? { id: subject, level: "ds" } : null}
              dimOutside={false}
              highlight={highlight}
              units={units}
              edLabels={null}
              nameOf={nameOf}
              parentOf={parentOf}
              tooltip={(id) => ({
                title: nameOf(id),
                detail: typeOf.has(id) ? `type ${typeOf.get(id)}` : null,
              })}
              inset={{ right: 0, bottom: 0 }}
              onReady={() => undefined}
              onZoom={() => undefined}
              onSelect={(id) => pick(id)}
              onError={setMapError}
            />
          </div>
          {mapError ? <p className="muted small">{mapError} The table below has the same answer.</p> : null}
        </section>
        <section className="space-similarity" aria-label="Similarity">
          <h2 className="visually-hidden">Similarity</h2>
          {space ? (
            <SimilarityView
              space={space}
              selected={subject}
              near={near}
              brushed={brushed}
              colourOf={colourOf}
              nameOf={nameOf}
              onPick={(id) => pick(id)}
              onBrush={(ids) => setBrushed(new Set(ids))}
              axisLabels={axisNames}
            />
          ) : (
            <p className="muted">Loading the space…</p>
          )}
          <p className="small muted">
            {spaceName === "trajectory"
              ? `Across: ${axisNames[0]}. Up: ${axisNames[1]}. Both axes of the space, standardised.`
              : `Across: axis 1 (${axisNames[0]}). Up: axis 2 (${axisNames[1]}). A flat view of ${composite?.axes.length ?? 0} axes; distances use all of them.`}{" "}
            Drag to select a group; it is ringed on the map.
          </p>
        </section>
      </div>

      {spaceName === "profile" && typology ? (
        <section className="space-types" aria-label="Types">
          <h2>Types of DS division</h2>
          <p className="small muted">
            {typology.k} groups from {typology.method.toLowerCase()} Names are machine drafts
            ({typology.types[0]?.label_status.replaceAll("_", " ")}), awaiting review. Numbered
            by size; the order is not a ranking.
          </p>
          <ul className="space-type-list">
            {typology.types.map((t) => (
              <li key={t.type}>
                <span className="space-swatch" style={{ background: TYPE_COLOURS[(t.type - 1) % TYPE_COLOURS.length] }} />
                <strong>Type {t.type}</strong> · {t.size} divisions · {t.draft_name}{" "}
                <small>(typical: {t.typical.map(nameOf).join(", ")}; stability {pct(t.mean_agreement)})</small>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="space-answer" aria-label="Answer">
        <h2>
          {subject ? nameOf(subject) : "Select a DS division on the map or in the similarity view"}
          {subject && typeOf.has(subject) && spaceName === "profile" ? (
            <small> · type {typeOf.get(subject)}</small>
          ) : null}
        </h2>
        <p className="small muted">
          Space: {version}. {spaceName === "trajectory" ? "Private, local build (D-038)." : null}
        </p>
        {selected && !subject ? (
          <p className="muted">This division is not in the {spaceName} space.</p>
        ) : null}
        {subject && question === "unusual" && unusual ? (
          <p>
            Distance from the centre of the space: {unusual.distance.toFixed(2)}, farther than{" "}
            {Math.round(unusual.percentile)}% of divisions. Unusual means unlike the average
            division, not better or worse.
          </p>
        ) : null}
        {subject && question !== "unusual" ? (
          <div className="table-scroll">
            <table className="space-table">
              <caption>
                {QUESTIONS.find((q) => q.id === question)?.label}: {answer.length} divisions
              </caption>
              <thead>
                <tr>
                  <th scope="col">Division</th>
                  <th scope="col">Distance</th>
                  {spaceName === "profile" ? <th scope="col">Type</th> : <th scope="col">Comparison</th>}
                  <th scope="col">Note</th>
                  <th scope="col">Why</th>
                </tr>
              </thead>
              <tbody>
                {answer.map((item) => (
                  <tr key={item.id} className={compare === item.id ? "is-active" : ""}>
                    <th scope="row">
                      <button type="button" className="link-button" onClick={() => pick(item.id)}>
                        {nameOf(item.id)}
                      </button>
                    </th>
                    <td>{item.distance.toFixed(3)}</td>
                    <td>
                      {spaceName === "profile"
                        ? (typeOf.get(item.id) ?? "–")
                        : (trajectory?.comparison[trajectory.ids.indexOf(item.id)] ?? "–")}
                    </td>
                    <td>{item.note ?? ""}</td>
                    <td>
                      <button type="button" className="link-button" onClick={() => setCompare(item.id)}>
                        Explain
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        {reasons && compare && subject ? (
          <div className="space-reasons">
            <h3>
              Why {nameOf(subject)} and {nameOf(compare)} are this far apart
            </h3>
            {reasons.kind === "profile" && reasons.shares ? (
              <>
                <p className="small">Share of the squared distance, exact (sums to 100%):</p>
                <ul>
                  {composite!.blocks.map((block, b) => (
                    <li key={block.id}>
                      {block.label}: {pct(reasons.shares!.block[b])}
                    </li>
                  ))}
                </ul>
                <ul className="small muted">
                  {composite!.axes.map((axis, i) => (
                    <li key={axis.axis}>
                      Axis {axis.axis} ({axis.draft_label}, machine draft): {pct(reasons.shares!.axis[i])}
                    </li>
                  ))}
                </ul>
              </>
            ) : null}
            {reasons.kind === "trajectory" && reasons.shares ? (
              <ul>
                {trajectory!.axes.map((axis, i) => (
                  <li key={axis.id}>
                    {axis.label}: {pct(reasons.shares![i])}
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}
        {brushed.size > 0 ? (
          <p className="small">
            Selected group ({brushed.size}): {[...brushed].map(nameOf).sort().join(", ")}.{" "}
            <button type="button" className="link-button" onClick={() => setBrushed(new Set())}>
              Clear
            </button>
          </p>
        ) : null}
      </section>
    </div>
  );
}
