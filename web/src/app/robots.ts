import type { MetadataRoute } from "next";

import { getLatest } from "@/lib/release";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export default function robots(): MetadataRoute.Robots {
  const latest = getLatest();
  if (!latest.publishable) {
    return {
      rules: [{ userAgent: "*", disallow: "/" }],
      sitemap: `${BASE_URL}/sitemap.xml`,
    };
  }
  return {
    rules: [{ userAgent: "*", allow: "/" }],
    sitemap: `${BASE_URL}/sitemap.xml`,
  };
}
