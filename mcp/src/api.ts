/** Reads the Sri Lanka Facts static API (a release's `api/v1/` folder or its base URL). */

import fs from "node:fs/promises";
import path from "node:path";

export type Geography = {
  geography_id: string;
  level: number;
  level_name: string;
  name_en: string | null;
  name_si: string | null;
  name_ta: string | null;
  parent_id: string | null;
  status: string;
};

export type Value = {
  indicator_id: string;
  value: number | null;
  unit: string;
  period: string;
  value_status: string;
  verification: string;
  dataset_id: string;
  snapshot_sha256: string;
  source_locator: string;
  support_type?: string;
  information_footprint_ref?: string;
};

export type Dataset = {
  dataset_id: string;
  title: string;
  source_name: string | null;
  source_homepage: string | null;
  licence: string | null;
  commercial_reuse: string;
  attribution: string | null;
  notice: string | null;
  publication_decision: string | null;
  rights_status: string;
};

export type Place = {
  citation: string;
  release: string;
  publishable: boolean;
  use?: string;
  geography: Geography;
  datasets: Dataset[];
  values: Value[];
  profile?: {
    space_id?: string;
    space_version?: string;
    similar?: { geography_id: string; distance: number }[];
  } | null;
};

export type IndicatorMeta = {
  id: string;
  name: string;
  short_name?: string;
  unit: string;
  decimals: number;
  measure_type: string;
  definition: string;
  levels: string[];
  topic?: string[] | string;
  period?: string;
  distribution?: string;
};

/** A static API reader with an in-process cache (files are immutable per release). */
export class StaticApi {
  private cache = new Map<string, Promise<unknown>>();

  constructor(
    /** A folder holding `api/v1/` (local release) or an http(s) base URL of the site. */
    readonly root: string,
    /** Public base URL used in citations, for example https://example.org. */
    readonly siteUrl: string | null = null,
  ) {}

  private read<T>(relative: string): Promise<T> {
    const cached = this.cache.get(relative);
    if (cached) {
      return cached as Promise<T>;
    }
    const request = (async () => {
      if (/^https?:\/\//.test(this.root)) {
        const response = await fetch(new URL(`api/v1/${relative}`, this.root.endsWith("/") ? this.root : `${this.root}/`));
        if (!response.ok) {
          throw new NotFound(relative);
        }
        return (await response.json()) as T;
      }
      try {
        return JSON.parse(await fs.readFile(path.join(this.root, "api", "v1", relative), "utf8")) as T;
      } catch {
        throw new NotFound(relative);
      }
    })();
    this.cache.set(relative, request);
    request.catch(() => this.cache.delete(relative));
    return request;
  }

  geographies() {
    return this.read<{ geographies: Geography[]; release: string; citation: string }>("geographies/admin.json");
  }

  place(id: string) {
    if (!/^[A-Za-z0-9-]+$/.test(id)) {
      return Promise.reject(new NotFound(id));
    }
    return this.read<Place>(`places/${id}.json`);
  }

  indicators() {
    return this.read<{ indicators: IndicatorMeta[]; release: string; citation: string }>("indicators.json");
  }

  indicatorLevel(id: string, level: string) {
    if (!/^[a-z0-9_]+$/.test(id) || !/^[a-z-]+$/.test(level)) {
      return Promise.reject(new NotFound(`${id}/${level}`));
    }
    return this.read<{
      release: string;
      citation: string;
      values: { geography_id: string; value: number | null; unit: string; period: string; value_status: string }[];
    }>(`indicators/${id}/${level}.json`);
  }

  latest() {
    return this.read<{ release: string; citation: string; publishable: boolean; datasets: Dataset[] }>(
      "releases/latest.json",
    );
  }

  placeUrl(id: string): string | null {
    return this.siteUrl ? `${this.siteUrl.replace(/\/$/, "")}/place/${id}` : null;
  }
}

export class NotFound extends Error {
  constructor(what: string) {
    super(`not available: ${what}`);
  }
}

/** Accent- and case-insensitive name key for search. */
export function fold(text: string): string {
  return text
    .normalize("NFKD")
    .replace(/\p{M}/gu, "")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim();
}
