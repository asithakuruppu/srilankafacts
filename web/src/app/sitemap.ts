import type { MetadataRoute } from "next";

import { getGeographies, getIndicators } from "@/lib/release";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export async function generateSitemaps() {
  return [{ id: 0 }, { id: 1 }, { id: 2 }, { id: 3 }, { id: 4 }, { id: 5 }];
}

export default async function sitemap(props: {
  id: Promise<string>;
}): Promise<MetadataRoute.Sitemap> {
  const id = Number(await props.id);
  if (id === 5) {
    const indicators = getIndicators().map((indicator) => ({
      url: `${BASE_URL}/indicator/${indicator.id}`,
      changeFrequency: "yearly" as const,
      priority: 0.7,
    }));
    return [
      { url: BASE_URL, changeFrequency: "monthly", priority: 1 },
      { url: `${BASE_URL}/explore`, changeFrequency: "monthly", priority: 0.9 },
      { url: `${BASE_URL}/indicators`, changeFrequency: "yearly", priority: 0.8 },
      { url: `${BASE_URL}/data`, changeFrequency: "yearly", priority: 0.6 },
      { url: `${BASE_URL}/methods`, changeFrequency: "yearly", priority: 0.6 },
      { url: `${BASE_URL}/corrections`, changeFrequency: "monthly", priority: 0.5 },
      ...indicators,
    ];
  }
  return getGeographies()
    .filter((geo) => geo.level === id)
    .map((geo) => ({
      url: `${BASE_URL}/place/${geo.geography_id}`,
      changeFrequency: "yearly" as const,
      priority: id === 0 ? 1 : id === 1 ? 0.8 : id === 2 ? 0.7 : 0.5,
    }));
}
