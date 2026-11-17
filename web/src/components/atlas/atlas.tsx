"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import AtlasMap, { type AtlasMapHandle } from "@/components/atlas/atlas-map";
import PlacePanel from "@/components/atlas/place-panel";
import { classIndex, divergingBreaks, quantileBreaks, type ValueMap } from "@/lib/atlas/context";
import {
  loadAdjacency,
  loadChange,
  loadJson,
  loadLevelValues,
  loadProfile,
  loadUnits,
} from "@/lib/atlas/data";
import { distancesFrom, indexProfile, nearest } from "@/lib/atlas/profile";
import {
  DETAIL_ZOOM,
  DIVERGING,
  LEVEL_MIN_ZOOM,
  MAP_LEVELS,
  PROXIMITY,
  SEQUENTIAL,
  childLevel,
  levelForZoom,
  rampFor,
  zoomBand,
  type MapLevel,
} from "@/lib/atlas/scale";
import {
  LENSES,
  LEVELS,
  LEVEL_PLURAL,
  LEVEL_PLURAL_TEXT,
  LEVEL_SHORT,
  type AtlasIndicator,
  type AtlasMeta,
  type Lens,
  type LevelName,
} from "@/lib/atlas/types";
import { useLoaded } from "@/lib/atlas/use-loaded";
import { formatValue } from "@/lib/format";
import { buildHierarchy, type HierarchyRow } from "@/lib/hierarchy";

export type LegendEntry = { color: string; label: string };
export type Legend = { title: string; note: string; entries: LegendEntry[] };

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

function useViewport(): { wide: boolean; height: number } {
  // Read at first render in the browser: the map needs the right insets when it is created.
  const [viewport, setViewport] = useState(() =>
    typeof window === "undefined"
      ? { wide: true, height: 800 }
      : { wide: window.innerWidth >= 900, height: window.innerHeight },
  );
  useEffect(() => {
    const read = () => setViewport({ wide: window.innerWidth >= 900, height: window.innerHeight });
    window.addEventListener("resize", read);
    return () => window.removeEventListener("resize", read);
  }, []);
  return viewport;
}

const LENS_IDS = LENSES.map((lens) => lens.id);

export default function Atlas({
  indicators,
  meta,
  release,
}: {
  indicators: AtlasIndicator[];
  meta: AtlasMeta;
  release: string;
}) {
  const params = useSearchParams();
  const mapRef = useRef<AtlasMapHandle | null>(null);
  const theme = useTheme();
  const viewport = useViewport();

  const defaultIndicator =
    indicators.find((item) => item.id === "population_density")?.id ?? indicators[0]?.id ?? "";
  const [initial] = useState(() => ({
    place: params.get("place"),
    lens: LENS_IDS.includes(params.get("lens") as Lens) ? (params.get("lens") as Lens) : "geography",
    indicator: indicators.some((item) => item.id === params.get("ind"))
      ? (params.get("ind") as string)
      : defaultIndicator,
    level: MAP_LEVELS.includes(params.get("level") as MapLevel)
      ? (params.get("level") as MapLevel)
      : null,
    compare: params.get("cmp"),
  }));

  const [selectedId, setSelectedId] = useState<string | null>(initial.place);
  const [lens, setLens] = useState<Lens>(initial.lens);
  const [indicatorId, setIndicatorId] = useState(initial.indicator);
  const [pinned, setPinned] = useState<MapLevel | null>(initial.level);
  const [compareId, setCompareId] = useState<string | null>(initial.compare);
  const [zoom, setZoom] = useState(6.5);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickerQuery, setPickerQuery] = useState("");
  const [sheetOpen, setSheetOpen] = useState(true);
  const [mapError, setMapError] = useState<string | null>(null);
  const [mapReady, setMapReady] = useState(false);
  /** A request to move the map to a place; handled once the place can be located. */
  const [flyRequest, setFlyRequest] = useState<{ id: string } | null>(
    initial.place ? { id: initial.place } : null,
  );
  const handledFly = useRef<{ id: string } | null>(null);

  const units = useLoaded(loadUnits, "units");
  const adjacency = useLoaded(loadAdjacency, "adjacency");
  const hierarchyRows = useLoaded(
    () => loadJson<HierarchyRow[]>("/release/hierarchy.json"),
    "hierarchy",
  );
  const hierarchy = useMemo(() => (hierarchyRows ? buildHierarchy(hierarchyRows) : null), [hierarchyRows]);
  const profileFile = useLoaded(meta.profile ? loadProfile : null, "profile");
  const profile = useMemo(() => (profileFile ? indexProfile(profileFile) : null), [profileFile]);
  const change = useLoaded(meta.change && lens === "change" ? loadChange : null, "change");

  const indicator = indicators.find((item) => item.id === indicatorId) ?? indicators[0];

  const nameOf = useCallback(
    (id: string) => units?.[id]?.n ?? hierarchy?.nodes.get(id)?.name ?? id,
    [hierarchy, units],
  );
  const parentOf = useCallback(
    (id: string) => units?.[id]?.p ?? hierarchy?.nodes.get(id)?.parentId ?? null,
    [hierarchy, units],
  );
  const levelOf = useCallback(
    (id: string): LevelName => {
      const unit = units?.[id];
      if (unit) {
        return LEVELS[unit.l] ?? "gn";
      }
      return LEVELS[hierarchy?.nodes.get(id)?.level ?? 4] ?? "gn";
    },
    [hierarchy, units],
  );

  const subject = selectedId ?? "LK";
  const subjectLevel = levelOf(subject);
  const known = selectedId === null || Boolean(units?.[subject] ?? hierarchy?.nodes.get(subject));

  // Levels the map can show for this lens.
  const available = useMemo<MapLevel[]>(() => {
    if (lens === "profile" || lens === "change") {
      return ["ds"];
    }
    if (lens === "landscape") {
      return MAP_LEVELS;
    }
    return MAP_LEVELS.filter((level) => indicator?.levels.includes(level));
  }, [indicator, lens]);

  const autoLevel = levelForZoom(zoom, available);
  const level: MapLevel =
    pinned && available.includes(pinned) && !(pinned === "gn" && zoom < DETAIL_ZOOM)
      ? pinned
      : autoLevel;

  // Values of the indicator, per level, loaded when a level is needed.
  const need = (name: LevelName) =>
    lens === "geography" &&
    Boolean(indicator?.levels.includes(name)) &&
    (name !== "gn" || level === "gn" || subjectLevel === "ds" || subjectLevel === "gn");
  const country = useLoaded(
    need("country") ? () => loadLevelValues(indicatorId, "country") : null,
    `${indicatorId}|country|${need("country")}`,
  );
  const province = useLoaded(
    need("province") ? () => loadLevelValues(indicatorId, "province") : null,
    `${indicatorId}|province|${need("province")}`,
  );
  const district = useLoaded(
    need("district") ? () => loadLevelValues(indicatorId, "district") : null,
    `${indicatorId}|district|${need("district")}`,
  );
  const ds = useLoaded(
    need("ds") ? () => loadLevelValues(indicatorId, "ds") : null,
    `${indicatorId}|ds|${need("ds")}`,
  );
  const gn = useLoaded(
    need("gn") ? () => loadLevelValues(indicatorId, "gn") : null,
    `${indicatorId}|gn|${need("gn")}`,
  );
  const values = useMemo<Partial<Record<LevelName, ValueMap>>>(
    () => ({
      ...(country ? { country } : {}),
      ...(province ? { province } : {}),
      ...(district ? { district } : {}),
      ...(ds ? { ds } : {}),
      ...(gn ? { gn } : {}),
    }),
    [country, district, ds, gn, province],
  );

  // The DS division the profile lens is about: the selected DS, or a selected GN's DS.
  const profileSubject = useMemo(() => {
    if (!profile) {
      return null;
    }
    const candidate = subjectLevel === "gn" ? parentOf(subject) : subject;
    return candidate && profile.row.has(candidate) ? candidate : null;
  }, [parentOf, profile, subject, subjectLevel]);

  const similar = useMemo(
    () => (profile && profileSubject ? nearest(profile, profileSubject, 10) : []),
    [profile, profileSubject],
  );

  const changeById = useMemo(
    () => new Map((change?.ds ?? []).map((row) => [row.id, row])),
    [change],
  );

  // Map colours and legend for the lens in view.
  const { colors, legend } = useMemo<{ colors: Map<string, string> | null; legend: Legend }>(() => {
    const scope = `${LEVEL_PLURAL[level]}`;
    if (lens === "geography") {
      const map = values[level];
      if (!indicator || !map) {
        return {
          colors: null,
          legend: { title: indicator?.short ?? "", note: `Loading ${LEVEL_PLURAL_TEXT[level]}…`, entries: [] },
        };
      }
      const ramp = rampFor(SEQUENTIAL, theme);
      const breaks = quantileBreaks([...map.values()], 5);
      const palette =
        breaks.length === 4 ? ramp : ramp.filter((_, i) => i % 2 === 0).slice(0, breaks.length + 1);
      const colours = new Map<string, string>();
      for (const [id, value] of map) {
        colours.set(id, palette[Math.min(classIndex(value, breaks), palette.length - 1)]);
      }
      const fmt = (value: number) => formatValue(value, indicator.unit, indicator.decimals);
      const entries = palette.slice(0, breaks.length + 1).map((color, i) => ({
        color,
        label:
          breaks.length === 0
            ? "all equal"
            : i === 0
              ? `under ${fmt(breaks[0])}`
              : i === breaks.length
                ? `${fmt(breaks[i - 1])} and over`
                : `${fmt(breaks[i - 1])} – ${fmt(breaks[i])}`,
      }));
      return {
        colors: colours,
        legend: {
          title: indicator.short,
          note: `${scope} · Census 2024 · ${map.size.toLocaleString("en-LK")} with a value · classes are fifths of the values`,
          entries,
        },
      };
    }
    if (lens === "profile") {
      if (!profile) {
        return {
          colors: null,
          legend: { title: "Profile", note: meta.profile ? "Loading the profile space…" : "No profile space in this build.", entries: [] },
        };
      }
      const ramp = rampFor(PROXIMITY, theme);
      const version = `profile space v${profile.file.space_version}`;
      if (profileSubject) {
        const distances = distancesFrom(profile, profileSubject) ?? new Map<string, number>();
        const breaks = quantileBreaks([...distances.values()], 5);
        const colours = new Map<string, string>();
        for (const [id, value] of distances) {
          colours.set(id, ramp[Math.min(classIndex(value, breaks), 4)]);
        }
        colours.set(profileSubject, theme === "dark" ? "#8da6ff" : "#1c3fae");
        return {
          colors: colours,
          legend: {
            title: `Like ${nameOf(profileSubject)}`,
            note: `DS divisions by distance from ${nameOf(profileSubject)} in ${version}. A distance is a similarity statement, not a fact.`,
            entries: ["closest fifth", "", "middle", "", "farthest fifth"].map((label, i) => ({
              color: ramp[i],
              label,
            })),
          },
        };
      }
      const sequential = rampFor(SEQUENTIAL, theme);
      const colours = new Map<string, string>();
      profile.file.ids.forEach((id, i) => {
        const percentile = profile.file.percentile[i];
        if (percentile !== null) {
          colours.set(id, sequential[Math.min(4, Math.floor(percentile / 20))]);
        }
      });
      return {
        colors: colours,
        legend: {
          title: "How unusual",
          note: `DS divisions by distance from the national centre of ${version}. Farther means less like the average division, not better or worse.`,
          entries: ["nearest the centre", "", "", "", "farthest"].map((label, i) => ({
            color: sequential[i],
            label,
          })),
        },
      };
    }
    if (lens === "change") {
      if (!change) {
        return {
          colors: null,
          legend: { title: "Change", note: meta.change ? "Loading census change…" : "No census history in this build.", entries: [] },
        };
      }
      const ramp = rampFor(DIVERGING, theme);
      const growth = change.ds.map((row) => row.growth_pct).filter((v): v is number => v !== null);
      const breaks = divergingBreaks(growth);
      const colours = new Map<string, string>();
      for (const row of change.ds) {
        if (row.growth_pct !== null) {
          colours.set(row.id, ramp[classIndex(row.growth_pct, breaks)] ?? ramp[2]);
        }
      }
      const pct = (value: number) => `${value > 0 ? "+" : ""}${value}%`;
      return {
        colors: colours,
        legend: {
          title: "Population change, 2012 to 2024",
          note: "DS divisions · DCS censuses of 2012 and 2024 · local build, not in a release. Some comparisons are approximate; select a division to see which.",
          entries:
            breaks.length === 4
              ? [
                  { color: ramp[0], label: `under ${pct(breaks[0])}` },
                  { color: ramp[1], label: `${pct(breaks[0])} – ${pct(breaks[1])}` },
                  { color: ramp[2], label: `${pct(breaks[1])} – ${pct(breaks[2])}` },
                  { color: ramp[3], label: `${pct(breaks[2])} – ${pct(breaks[3])}` },
                  { color: ramp[4], label: `${pct(breaks[3])} and over` },
                ]
              : [],
        },
      };
    }
    return {
      colors: null,
      legend: {
        title: "Landscape",
        note: "No landscape dataset is in this release. The map shows boundaries only.",
        entries: [],
      },
    };
  }, [change, indicator, lens, level, meta.change, meta.profile, nameOf, profile, profileSubject, theme, values]);

  const flyTo = useCallback(
    (id: string) => {
      if (!units) {
        return;
      }
      const placeLevel = levelOf(id);
      if (lens === "profile" || lens === "change") {
        // These lenses compare DS divisions across the country: keep the whole island in view.
        const whole = units.LK?.b;
        if (whole) {
          mapRef.current?.fit(whole);
        }
        return;
      }
      const boxOwner = placeLevel === "gn" ? parentOf(id) : id;
      const box = boxOwner ? units[boxOwner]?.b : null;
      if (!box) {
        return;
      }
      if (placeLevel === "country") {
        mapRef.current?.fit(box);
        return;
      }
      const next = placeLevel === "gn" ? "gn" : childLevel(placeLevel);
      const drill = !pinned && next && available.includes(next) ? zoomBand(next) : undefined;
      mapRef.current?.fit(box, drill);
    },
    [available, lens, levelOf, parentOf, pinned, units],
  );

  const select = useCallback(
    (id: string | null, options: { fly?: boolean } = {}) => {
      setSelectedId(id);
      setCompareId(null);
      setSheetOpen(true);
      if (options.fly) {
        setFlyRequest({ id: id ?? "LK" });
      }
    },
    [],
  );

  // Fly once the data needed to locate the place has arrived.
  useEffect(() => {
    if (flyRequest && flyRequest !== handledFly.current && units && hierarchy && mapReady) {
      handledFly.current = flyRequest;
      flyTo(flyRequest.id);
    }
  }, [flyRequest, flyTo, hierarchy, mapReady, units]);

  // The header search links to /?place=…; follow it when the URL changes from outside.
  const urlPlace = params.get("place");
  const [seenUrlPlace, setSeenUrlPlace] = useState(urlPlace);
  if (urlPlace !== seenUrlPlace) {
    setSeenUrlPlace(urlPlace);
    if (urlPlace !== selectedId) {
      setSelectedId(urlPlace);
      setCompareId(null);
      setSheetOpen(true);
      setFlyRequest({ id: urlPlace ?? "LK" });
    }
  }

  // Every view has a URL.
  useEffect(() => {
    const query = new URLSearchParams();
    if (selectedId) {
      query.set("place", selectedId);
    }
    if (lens !== "geography") {
      query.set("lens", lens);
    }
    if (indicatorId !== defaultIndicator) {
      query.set("ind", indicatorId);
    }
    if (pinned) {
      query.set("level", pinned);
    }
    if (compareId) {
      query.set("cmp", compareId);
    }
    const text = query.toString();
    window.history.replaceState(null, "", text ? `/?${text}` : "/");
  }, [compareId, defaultIndicator, indicatorId, lens, pinned, selectedId]);

  const tooltip = useCallback(
    (id: string) => {
      const title = nameOf(id);
      if (lens === "geography" && indicator) {
        const value = values[level]?.get(id);
        return {
          title,
          detail:
            value === undefined
              ? "no value"
              : formatValue(value, indicator.unit, indicator.decimals),
        };
      }
      if (lens === "change") {
        const row = changeById.get(id);
        return {
          title,
          detail:
            row?.growth_pct === null || row === undefined
              ? "no comparison"
              : `${row.growth_pct > 0 ? "+" : ""}${row.growth_pct}% · ${row.comparison}`,
        };
      }
      if (lens === "profile" && profile && profileSubject && id !== profileSubject) {
        const row = profile.row.get(id);
        const origin = profile.row.get(profileSubject);
        if (row !== undefined && origin !== undefined) {
          const distance = Math.hypot(
            ...profile.file.vectors[row].map((v, i) => v - profile.file.vectors[origin][i]),
          );
          return { title, detail: `distance ${distance.toFixed(2)}` };
        }
      }
      return { title, detail: LEVEL_SHORT[level] };
    },
    [changeById, indicator, lens, level, nameOf, profile, profileSubject, values],
  );

  const highlight = useMemo(() => {
    if (lens !== "profile") {
      return [];
    }
    const ids = similar.map((item) => item.id);
    return compareId && !ids.includes(compareId) && profile?.row.has(compareId)
      ? [...ids, compareId]
      : ids;
  }, [compareId, lens, profile, similar]);

  const inset = useMemo(
    () =>
      viewport.wide
        ? { right: 424, bottom: 0 }
        : { right: 0, bottom: sheetOpen ? Math.round(viewport.height * 0.42) : 64 },
    [sheetOpen, viewport.height, viewport.wide],
  );

  const selected = useMemo(
    () => (selectedId && known ? { id: selectedId, level: subjectLevel } : null),
    [known, selectedId, subjectLevel],
  );
  const dimOutside =
    (lens === "geography" || lens === "landscape") &&
    selected !== null &&
    LEVELS.indexOf(selected.level) < LEVELS.indexOf(level);

  const grouped = useMemo(() => {
    const query = pickerQuery.trim().toLowerCase();
    const groups = new Map<string, AtlasIndicator[]>();
    for (const item of indicators) {
      if (query && !item.name.toLowerCase().includes(query)) {
        continue;
      }
      const group = groups.get(item.group);
      if (group) {
        group.push(item);
      } else {
        groups.set(item.group, [item]);
      }
    }
    return [...groups.entries()];
  }, [indicators, pickerQuery]);

  const pinLevel = (next: MapLevel | null) => {
    setPinned(next);
    if (next === "gn" && zoom < LEVEL_MIN_ZOOM.gn) {
      mapRef.current?.zoomTo(LEVEL_MIN_ZOOM.gn + 0.1);
    }
  };

  return (
    <div className={`atlas atlas-lens-${lens} ${sheetOpen ? "is-sheet-open" : ""}`}>
      <AtlasMap
        ref={mapRef}
        theme={theme}
        level={level}
        colors={colors}
        selected={selected}
        dimOutside={dimOutside}
        highlight={highlight}
        units={units}
        nameOf={nameOf}
        parentOf={parentOf}
        tooltip={tooltip}
        inset={inset}
        onReady={() => setMapReady(true)}
        onZoom={setZoom}
        onSelect={(id) => {
          if (id !== selectedId) {
            select(id, { fly: id !== null && (lens === "geography" || lens === "landscape") });
          }
        }}
        onError={setMapError}
      />

      {mapError ? (
        <p className="atlas-error" role="alert">
          {mapError} The same values are in the <Link href="/explore">tables</Link>.
        </p>
      ) : null}

      <div className="atlas-top">
        <div className="atlas-lenses" role="tablist" aria-label="Lens">
          {LENSES.map((item) => (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={lens === item.id}
              title={item.hint}
              className={lens === item.id ? "is-active" : ""}
              onClick={() => {
                setLens(item.id);
                setCompareId(null);
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
        {lens === "geography" && indicator ? (
          <div className="atlas-picker">
            <button
              type="button"
              className="atlas-picker-button"
              aria-expanded={pickerOpen}
              aria-controls="atlas-indicator-list"
              onClick={() => setPickerOpen((open) => !open)}
            >
              <span className="atlas-kicker">Indicator</span>
              <span className="atlas-picker-name">{indicator.short}</span>
              <span aria-hidden="true" className="atlas-caret">
                {pickerOpen ? "–" : "+"}
              </span>
            </button>
            {pickerOpen ? (
              <div className="atlas-picker-list" id="atlas-indicator-list">
                <label className="visually-hidden" htmlFor="atlas-indicator-filter">
                  Filter indicators
                </label>
                <input
                  id="atlas-indicator-filter"
                  type="search"
                  placeholder={`Filter ${indicators.length} indicators…`}
                  value={pickerQuery}
                  autoFocus
                  onChange={(event) => setPickerQuery(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Escape") {
                      setPickerOpen(false);
                    }
                  }}
                />
                <div className="atlas-picker-scroll">
                  {grouped.length === 0 ? <p className="atlas-empty">No indicator matches.</p> : null}
                  {grouped.map(([group, items]) => (
                    <section key={group}>
                      <h3>{group}</h3>
                      <ul>
                        {items.map((item) => (
                          <li key={item.id}>
                            <button
                              type="button"
                              className={item.id === indicatorId ? "is-active" : ""}
                              onClick={() => {
                                setIndicatorId(item.id);
                                setPickerOpen(false);
                                setPickerQuery("");
                              }}
                            >
                              <span>{item.name}</span>
                              <small>{item.levels.includes("gn") ? "to GN" : "to DS"}</small>
                            </button>
                          </li>
                        ))}
                      </ul>
                    </section>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>

      <div className="atlas-bottom">
        <div className="atlas-legend" aria-label="Map legend">
          <p className="atlas-legend-title">{legend.title}</p>
          {legend.entries.length > 0 ? (
            <ul className="atlas-ramp">
              {legend.entries.map((entry, i) => (
                <li key={i}>
                  <span className="atlas-swatch" style={{ background: entry.color }} />
                  <span>{entry.label}</span>
                </li>
              ))}
            </ul>
          ) : null}
          <p className="atlas-legend-note">{legend.note}</p>
        </div>

        <div className="atlas-scale" role="group" aria-label="Geographic scale">
          <button
            type="button"
            className={pinned === null ? "is-active" : ""}
            aria-pressed={pinned === null}
            title="The level follows the zoom"
            onClick={() => pinLevel(null)}
          >
            Auto
          </button>
          {MAP_LEVELS.map((item) => (
            <button
              key={item}
              type="button"
              disabled={!available.includes(item)}
              aria-pressed={pinned === item}
              className={`${level === item ? "is-current" : ""} ${pinned === item ? "is-active" : ""}`}
              title={
                available.includes(item)
                  ? `Show ${LEVEL_PLURAL_TEXT[item]}`
                  : `Not published for ${LEVEL_PLURAL_TEXT[item]} in this view`
              }
              onClick={() => pinLevel(pinned === item ? null : item)}
            >
              {LEVEL_SHORT[item].replace(" division", "")}
            </button>
          ))}
          <span className="atlas-scale-floor" title="Buildings, trees and landmarks are not in this release. The finest unit with data is the GN division.">
            Features: none yet
          </span>
        </div>

        <div className="atlas-zoom" role="group" aria-label="Zoom">
          <button type="button" aria-label="Zoom in" onClick={() => mapRef.current?.zoomBy(1)}>
            +
          </button>
          <button type="button" aria-label="Zoom out" onClick={() => mapRef.current?.zoomBy(-1)}>
            −
          </button>
          <button
            type="button"
            aria-label="Whole country"
            title="Whole country"
            onClick={() => select(null, { fly: true })}
          >
            ◻
          </button>
        </div>
      </div>

      <PlacePanel
        release={release}
        meta={meta}
        lens={lens}
        subject={subject}
        subjectLevel={subjectLevel}
        known={known}
        indicator={indicator}
        indicators={indicators}
        values={values}
        units={units}
        hierarchy={hierarchy}
        adjacency={adjacency}
        profile={profile}
        profileSubject={profileSubject}
        similar={similar}
        change={change}
        compareId={compareId}
        nameOf={nameOf}
        parentOf={parentOf}
        levelOf={levelOf}
        onSelect={(id) => select(id, { fly: lens === "geography" || lens === "landscape" })}
        onCompare={setCompareId}
        onLens={setLens}
        sheetOpen={sheetOpen}
        onSheet={setSheetOpen}
      />
    </div>
  );
}
