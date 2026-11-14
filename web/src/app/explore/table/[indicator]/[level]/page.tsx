import type { Metadata } from "next";
import { notFound } from "next/navigation";

import ExploreStatic from "@/components/explore-static";
import { exploreCombos, exploreLevels } from "@/lib/explore-server";
import { getIndicator } from "@/lib/release";

export function generateStaticParams() {
  return exploreCombos();
}

function known(indicator: string, level: string): boolean {
  return exploreCombos().some((c) => c.indicator === indicator && c.level === level);
}

export async function generateMetadata({
  params,
}: PageProps<"/explore/table/[indicator]/[level]">): Promise<Metadata> {
  const { indicator, level } = await params;
  const meta = getIndicator(indicator);
  const levelMeta = exploreLevels().find((item) => item.name === level);
  if (!meta || !levelMeta || !known(indicator, level)) {
    return { title: "Table not found" };
  }
  return {
    title: `${meta.name} by ${levelMeta.singular}`,
    description: `${meta.name} for every ${levelMeta.singular} in Sri Lanka, Census 2024, as a table.`,
    alternates: { canonical: `/explore/table/${indicator}/${level}` },
  };
}

// Read params at the top, not inside <Suspense>: Suspense would stream the content into a hidden
// block that needs JavaScript to show (D-027: pages must read without JavaScript). The route may
// therefore block on navigation, which instant = false allows.
export const instant = false;

export default async function ExploreTablePage({
  params,
}: PageProps<"/explore/table/[indicator]/[level]">) {
  const { indicator, level } = await params;
  if (!known(indicator, level)) {
    notFound();
  }
  return <ExploreStatic indicatorId={indicator} levelName={level} />;
}
