"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import AtlasMap, { type AtlasMapHandle } from "@/components/atlas/atlas-map";
import ElectionPanel from "@/components/atlas/election-panel";
import PlacePanel from "@/components/atlas/place-panel";
import { classIndex, divergingBreaks, quantileBreaks, type ValueMap } from "@/lib/atlas/context";
import {
  loadAdjacency,
  loadChange,
  loadElectoral,
  loadJson,
  loadFeatures,
  loadLandscapeIndex,
  loadLandscapeValues,
  loadLevelValues,
  loadProfile,
  loadUnits,
} from "@/lib/atlas/data";
import { ELECTION_MEASURES, formatTotal, indexElectoral, measureValues } from "@/lib/atlas/elections";
import { distancesFrom, indexProfile, nearest } from "@/lib/atlas/profile";
import {
  DETAIL_ZOOM,
  DIVERGING,
  LEVEL_MIN_ZOOM,
  MAP_LEVELS,
  PROXIMITY,
  SCHEMES,
  SEQUENTIAL,
  childLevel,
  levelForZoom,
  rampFor,
  zoomBand,
  type AdminMapLevel,
  type MapLevel,
} from "@/lib/atlas/scale";
import {
  LENSES,
  LEVELS,
  LEVEL_PLURAL,
  LEVEL_PLURAL_TEXT,
  LEVEL_SHORT,
  type AtlasIndicator,
  type LandscapeIndicator,
  type AtlasMeta,
  type ElectionTotals,
  type Lens,
  type LevelName,
} from "@/lib/atlas/types";
import { useLoaded } from "@/lib/atlas/use-loaded";
import { formatValue } from "@/lib/format";
import { buildHierarchy, type HierarchyRow } from "@/lib/hierarchy";
import { useTheme } from "@/lib/atlas/use-theme";

export type LegendEntry = { color: string; label: string };
export type Legend = { title: string; note: string; entries: LegendEntry[] };


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
const DEFAULT_LANDSCAPE = "land_cover_tree_share";

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
    level: MAP_LEVELS.includes(params.get("level") as AdminMapLevel)
      ? (params.get("level") as MapLevel)
      : null,
    measure: ELECTION_MEASURES.some((m) => m.id === params.get("m"))
      ? (params.get("m") as keyof ElectionTotals)
      : ("turnout" as keyof ElectionTotals),
    compare: params.get("cmp"),
    landscape: params.get("lind"),
  }));

  const [selectedId, setSelectedId] = useState<string | null>(initial.place);
  const [lens, setLens] = useState<Lens>(initial.lens);
  const [indicatorId, setIndicatorId] = useState(initial.indicator);
  const [landscapeId, setLandscapeId] = useState<string>(initial.landscape ?? DEFAULT_LANDSCAPE);
  const [pinned, setPinned] = useState<MapLevel | null>(initial.level);
  const [compareId, setCompareId] = useState<string | null>(initial.compare);
  const [measure, setMeasure] = useState<keyof ElectionTotals>(initial.measure);
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
  // Keep a file once loaded: the key changes only when the lens first needs it.
  const [wanted, setWanted] = useState<Set<Lens>>(() => new Set([initial.lens]));
  if (!wanted.has(lens)) {
    setWanted(new Set([...wanted, lens]));
  }
  const wantChange = Boolean(meta.change) && (wanted.has("change") || lens === "change");
  const wantElectoral = Boolean(meta.electoral) && (wanted.has("elections") || lens === "elections");
  const change = useLoaded(wantChange ? loadChange : null, `change|${wantChange}`);
  const electoralFile = useLoaded(
    wantElectoral ? loadElectoral : null,
    `electoral|${wantElectoral}`,
  );
  const election = useMemo(
    () => (electoralFile ? indexElectoral(electoralFile) : null),
    [electoralFile],
  );
  const edLabels = useMemo(
    () =>
      election
        ? Object.fromEntries(election.file.eds.map((ed) => [ed.id, ed.c ?? null]))
        : null,
    [election],
  );

  const wantLandscape = Boolean(meta.landscape) && (wanted.has("landscape") || lens === "landscape");
  const landscapeFile = useLoaded(
    wantLandscape ? loadLandscapeIndex : null,
    `landscape|${wantLandscape}`,
  );
  const isLandscape = lens === "landscape";
  const pool = useMemo<AtlasIndicator[]>(
    () => (isLandscape ? (landscapeFile?.indicators ?? []) : indicators),
    [indicators, isLandscape, landscapeFile],
  );
  const currentId = isLandscape ? landscapeId : indicatorId;
  const indicator = pool.find((item) => item.id === currentId) ?? pool[0];
  const landscapeIndicator = isLandscape ? (indicator as LandscapeIndicator | undefined) : undefined;
  const activeId = indicator?.id ?? "";

  const nameOf = useCallback(
    (id: string) =>
      units?.[id]?.n ?? hierarchy?.nodes.get(id)?.name ?? election?.byId.get(id)?.name ?? id,
    [election, hierarchy, units],
  );
  const parentOf = useCallback(
    (id: string) => units?.[id]?.p ?? hierarchy?.nodes.get(id)?.parentId ?? null,
    [hierarchy, units],
  );
  const levelOf = useCallback(
    (id: string): LevelName => {
      if (id.startsWith("LK-ED-")) {
        return "ed";
      }
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
  // The district whose named features are drawn: that of the selected DS or GN.
  const featureDistrict = useMemo(() => {
    if (!meta.features || (subjectLevel !== "ds" && subjectLevel !== "gn" && subjectLevel !== "district")) {
      return null;
    }
    let id: string | null = subject;
    while (id && levelOf(id) !== "district") {
      id = parentOf(id);
    }
    return id;
  }, [levelOf, meta.features, parentOf, subject, subjectLevel]);
  const featureFile = useLoaded(
    featureDistrict ? () => loadFeatures(featureDistrict) : null,
    `features|${featureDistrict}`,
  );
  const known =
    selectedId === null ||
    Boolean(units?.[subject] ?? hierarchy?.nodes.get(subject) ?? election?.byId.get(subject));

  // Levels the map can show for this lens.
  const available = useMemo<MapLevel[]>(() => {
    if (lens === "profile" || lens === "change") {
      return ["ds"];
    }
    if (lens === "elections") {
      return ["ed"];
    }
    if (lens === "landscape" && !indicator) {
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
  const load = (name: LevelName) =>
    isLandscape ? loadLandscapeValues(activeId, name) : loadLevelValues(activeId, name);
  const need = (name: LevelName) =>
    (lens === "geography" || lens === "landscape") &&
    Boolean(indicator?.levels.includes(name)) &&
    (name !== "gn" || level === "gn" || subjectLevel === "ds" || subjectLevel === "gn");
  const country = useLoaded(
    need("country") ? () => load("country") : null,
    `${lens === "landscape" ? "landscape" : "census"}|${activeId}|country|${need("country")}`,
  );
  const province = useLoaded(
    need("province") ? () => load("province") : null,
    `${lens === "landscape" ? "landscape" : "census"}|${activeId}|province|${need("province")}`,
  );
  const district = useLoaded(
    need("district") ? () => load("district") : null,
    `${lens === "landscape" ? "landscape" : "census"}|${activeId}|district|${need("district")}`,
  );
  const ds = useLoaded(
    need("ds") ? () => load("ds") : null,
    `${lens === "landscape" ? "landscape" : "census"}|${activeId}|ds|${need("ds")}`,
  );
  const gn = useLoaded(
    need("gn") ? () => load("gn") : null,
    `${lens === "landscape" ? "landscape" : "census"}|${activeId}|gn|${need("gn")}`,
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
    if (lens === "geography" || (lens === "landscape" && indicator)) {
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
          note: `${scope} · ${landscapeIndicator ? `${landscapeIndicator.period} · modelled estimate, ${landscapeIndicator.floor}` : "Census 2024"} · ${map.size.toLocaleString("en-LK")} with a value · classes are fifths of the values`,
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
    if (lens === "elections") {
      const chosen = ELECTION_MEASURES.find((m) => m.id === measure) ?? ELECTION_MEASURES[0];
      if (!election) {
        return {
          colors: null,
          legend: {
            title: chosen.label,
            note: meta.electoral
              ? "Loading election results…"
              : "No election results in this build.",
            entries: [],
          },
        };
      }
      const map = measureValues(election, chosen.id);
      const ramp = rampFor(SEQUENTIAL, theme);
      const breaks = quantileBreaks([...map.values()], 5);
      const palette =
        breaks.length === 4 ? ramp : ramp.filter((_, i) => i % 2 === 0).slice(0, breaks.length + 1);
      const colours = new Map<string, string>();
      for (const [id, value] of map) {
        colours.set(id, palette[Math.min(classIndex(value, breaks), palette.length - 1)]);
      }
      const fmt = (value: number) => formatTotal(chosen.id, value);
      return {
        colors: colours,
        legend: {
          title: `${chosen.label}, ${election.file.election.name}`,
          note: `${map.size} electoral districts · ${chosen.definition} Election Commission, machine-read, not yet checked by a person. Classes are fifths of the values; colour is not a judgement.`,
          entries: palette.slice(0, breaks.length + 1).map((color, i) => ({
            color,
            label:
              breaks.length === 0
                ? "all equal"
                : i === 0
                  ? `under ${fmt(breaks[0])}`
                  : i === breaks.length
                    ? `${fmt(breaks[i - 1])} and over`
                    : `${fmt(breaks[i - 1])} – ${fmt(breaks[i])}`,
          })),
        },
      };
    }
    return {
      colors: null,
      legend: {
        title: "Landscape",
        note: meta.landscape
          ? "Loading landscape layers…"
          : "No landscape build is in this bundle. The map shows boundaries only.",
        entries: [],
      },
    };
  }, [change, election, indicator, landscapeIndicator, lens, level, measure, meta.change, meta.electoral, meta.landscape, meta.profile, nameOf, profile, profileSubject, theme, values]);

  const flyTo = useCallback(
    (id: string) => {
      if (!units) {
        return;
      }
      const placeLevel = levelOf(id);
      if (lens === "profile" || lens === "change" || lens === "elections") {
        // These lenses compare units across the country: keep the whole island in view.
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
    if (lens === "landscape" && landscapeId !== DEFAULT_LANDSCAPE) {
      query.set("lind", landscapeId);
    }
    if (lens === "elections" && measure !== "turnout") {
      query.set("m", measure);
    }
    if (pinned) {
      query.set("level", pinned);
    }
    if (compareId) {
      query.set("cmp", compareId);
    }
    const text = query.toString();
    window.history.replaceState(null, "", text ? `/?${text}` : "/");
  }, [compareId, defaultIndicator, indicatorId, landscapeId, lens, measure, pinned, selectedId]);

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
      if (lens === "elections") {
        const ed = election?.byId.get(id);
        return {
          title,
          detail: ed ? formatTotal(measure, ed.values[measure]) : "no result",
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
    [changeById, election, indicator, lens, level, measure, nameOf, profile, profileSubject, values],
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
    for (const item of pool) {
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
  }, [pool, pickerQuery]);

  /** Change lens; a selection moves between the admin and ED schemes only through composition. */
  const switchLens = (next: Lens) => {
    setLens(next);
    setCompareId(null);
    if (selectedId && next !== "elections" && levelOf(selectedId) === "ed") {
      setSelectedId(null);
    }
  };

  // In the Elections lens an admin selection becomes the ED made of its district, once the
  // results have loaded (adjusting state during render, as for the URL place above).
  if (lens === "elections" && electoralFile && selectedId && levelOf(selectedId) !== "ed") {
    let id: string | null = selectedId;
    while (id && levelOf(id) !== "district") {
      id = parentOf(id);
    }
    const ed = id ? electoralFile.eds.find((item) => item.districts?.includes(id as string)) : null;
    setSelectedId(ed ? ed.id : null);
  }

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
        edLabels={lens === "elections" ? edLabels : null}
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
        points={featureFile?.points ?? null}
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
              onClick={() => switchLens(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
        {(lens === "geography" || lens === "landscape") && indicator ? (
          <div className="atlas-picker">
            <button
              type="button"
              className="atlas-picker-button"
              aria-expanded={pickerOpen}
              aria-controls="atlas-indicator-list"
              onClick={() => setPickerOpen((open) => !open)}
            >
              <span className="atlas-kicker">{isLandscape ? "Layer" : "Indicator"}</span>
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
                  placeholder={`Filter ${pool.length} ${isLandscape ? "layers" : "indicators"}…`}
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
                              className={item.id === currentId ? "is-active" : ""}
                              onClick={() => {
                                if (isLandscape) {
                                  setLandscapeId(item.id);
                                } else {
                                  setIndicatorId(item.id);
                                }
                                setPickerOpen(false);
                                setPickerQuery("");
                              }}
                            >
                              <span>{item.name}</span>
                              <small>
                                {isLandscape
                                  ? (item as LandscapeIndicator).period
                                  : item.levels.includes("gn")
                                    ? "to GN"
                                    : "to DS"}
                              </small>
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
          <span className="atlas-scale-sep" aria-hidden="true" />
          {SCHEMES.map((scheme) => {
            const drawable = scheme.drawable && (scheme.id !== "ed" || Boolean(meta.electoral));
            return (
              <button
                key={scheme.id}
                type="button"
                disabled={!drawable}
                aria-pressed={drawable && level === scheme.id}
                className={level === scheme.id ? "is-current is-active" : ""}
                title={
                  drawable
                    ? `${scheme.title}. Shown with the Elections lens.`
                    : scheme.id === "ed"
                      ? "Electoral districts: not in this build"
                      : scheme.title
                }
                onClick={() => switchLens(lens === "elections" ? "geography" : "elections")}
              >
                {scheme.label}
              </button>
            );
          })}
          <span
            className="atlas-scale-floor"
            title={
              meta.features
                ? "Schools, health facilities and named places, drawn from zoom 11 for the selected district. Local preview only; not in any release."
                : "Buildings, trees and landmarks are not in this release. The finest unit with data is the GN division."
            }
          >
            {meta.features
              ? featureFile
                ? `Features: ${featureFile.points.length.toLocaleString("en-LK")} named`
                : "Features: select a district"
              : "Features: none yet"}
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

      {lens === "elections" ? (
        <ElectionPanel
          available={Boolean(meta.electoral)}
          election={election}
          subject={selectedId && levelOf(selectedId) === "ed" ? selectedId : selectedId ? "__none__" : null}
          measure={measure}
          onMeasure={setMeasure}
          onSelect={(id) => select(id)}
          nameOf={nameOf}
          sheetOpen={sheetOpen}
          onSheet={setSheetOpen}
        />
      ) : (
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
        features={featureFile}
        change={change}
        compareId={compareId}
        nameOf={nameOf}
        parentOf={parentOf}
        levelOf={levelOf}
        onSelect={(id) => select(id, { fly: lens === "geography" || lens === "landscape" })}
        onCompare={setCompareId}
        onLens={switchLens}
        sheetOpen={sheetOpen}
        onSheet={setSheetOpen}
      />
      )}
    </div>
  );
}
