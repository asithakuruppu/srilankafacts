import type { Metadata } from "next";
import { notFound } from "next/navigation";

import PlaceView from "@/components/place-view";
import { levelLabel } from "@/lib/format";
import {
  getBreadcrumb,
  getChildren,
  getGeographies,
  getGeography,
  getIndicators,
  getLatest,
  getNationalValues,
  getPlace,
  geographyLabel,
  placeValue,
} from "@/lib/release";
import type { Place } from "@/lib/types";

export function generateStaticParams() {
  return getGeographies()
    .filter((geo) => geo.level <= 3)
    .map((geo) => ({ geoId: geo.geography_id }));
}

export async function generateMetadata({
  params,
}: PageProps<"/place/[geoId]">): Promise<Metadata> {
  const { geoId } = await params;
  const place = getPlace(geoId);
  if (!place) {
    return { title: "Place not found" };
  }
  const geography = place.geography;
  const parent = geography.parent_id ? getGeography(geography.parent_id) : null;
  const description = `${geographyLabel(geography)}${
    parent ? `, ${geographyLabel(parent)}` : ""
  } in the Sri Lanka Facts Census Atlas 2024 preview: population, age structure, housing and density, each with its source.`;
  return {
    title: `${geographyLabel(geography)} (${levelLabel(geography.level_name)})`,
    description,
    alternates: { canonical: `/place/${geography.geography_id}` },
    robots: { index: geography.level_name !== "gn", follow: true },
    openGraph: { title: `${geographyLabel(geography)} · Sri Lanka Facts`, description },
  };
}

export default async function PlacePage({ params }: PageProps<"/place/[geoId]">) {
  const { geoId } = await params;
  return <PlaceContent geoId={geoId} />;
}

function PlaceContent({ geoId }: { geoId: string }) {
  const place = getPlace(geoId);
  if (!place) {
    notFound();
  }
  const geography = place.geography;
  const latest = getLatest();
  return (
    <PlaceView
      place={place}
      parent={geography.parent_id ? getPlace(geography.parent_id) : null}
      indicators={getIndicators()}
      breadcrumb={getBreadcrumb(geography.geography_id)}
      childUnits={getChildren(geography.geography_id).map((child) => ({
        geography: child,
        total: placeValue(getPlace(child.geography_id), "population_total"),
      }))}
      national={Object.fromEntries(getNationalValues())}
      release={latest.release}
      publishable={latest.publishable}
      populationRank={rank(place, "population_total")}
    />
  );
}

function rank(place: Place, indicatorId: string): string {
  const value = placeValue(place, indicatorId);
  if (value === null) {
    return "not available";
  }
  const siblings =
    place.geography.parent_id === null
      ? []
      : getChildren(place.geography.parent_id).filter((child) => child.level === place.geography.level);
  if (siblings.length === 0) {
    return "national total";
  }
  const values = siblings
    .map((child) => placeValue(getPlace(child.geography_id), indicatorId))
    .filter((item): item is number => item !== null)
    .sort((a, b) => b - a);
  const position = values.indexOf(value) + 1;
  return `${position} of ${values.length} in parent`;
}
