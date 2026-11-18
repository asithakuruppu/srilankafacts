/**
 * The Sri Lanka Facts MCP server (A01): read-only tools over the static API. Every answer
 * carries units, period, verification, dataset, source locator and a citation, and says
 * "not available" instead of guessing.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

import { fold, NotFound, StaticApi, type Dataset, type Value } from "./api.js";

const GUIDANCE =
  "Quote values with their unit and period, name the source, and give the citation. " +
  "If a tool says 'not available', say the data is not available; do not estimate.";

type Json = Record<string, unknown>;

function result(payload: Json) {
  return {
    content: [{ type: "text" as const, text: JSON.stringify(payload, null, 2) }],
    structuredContent: payload,
  };
}

function unavailable(what: string, hint: string) {
  return result({ available: false, message: `Not available: ${what}. ${hint}`, guidance: GUIDANCE });
}

function cite(value: Value, datasets: Dataset[]) {
  const dataset = datasets.find((item) => item.dataset_id === value.dataset_id);
  return {
    indicator_id: value.indicator_id,
    value: value.value,
    unit: value.unit,
    period: value.period,
    value_status: value.value_status,
    verification: value.verification,
    data_nature: value.verification === "machine_extracted" ? "official statistic, machine-extracted" : value.verification,
    dataset_id: value.dataset_id,
    source: dataset?.source_name ?? null,
    source_locator: value.source_locator,
    snapshot_sha256: value.snapshot_sha256,
  };
}

export function createServer(api: StaticApi): McpServer {
  const server = new McpServer(
    { name: "srilankafacts", version: "0.1.0" },
    { instructions: `Sri Lanka Facts: every place in Sri Lanka, every number about it, with its source. ${GUIDANCE}` },
  );

  server.registerTool(
    "search_places",
    {
      title: "Search places",
      description:
        "Find Sri Lankan places (country, province, district, DS division, GN division) by name in English, Sinhala or Tamil. Returns ids to use with the other tools.",
      inputSchema: {
        query: z.string().min(1).describe("A place name, for example 'Kandy' or 'Nuwara Eliya'."),
        level: z
          .enum(["country", "province", "district", "ds", "gn"])
          .optional()
          .describe("Restrict to one level."),
        limit: z.number().int().min(1).max(25).optional(),
      },
      annotations: { readOnlyHint: true, openWorldHint: false },
    },
    async ({ query, level, limit }) => {
      const { geographies, release } = await api.geographies();
      const needle = fold(query);
      const scored = geographies
        .filter((g) => !level || g.level_name === level)
        .map((g) => {
          const names = [g.name_en, g.name_si, g.name_ta].filter(Boolean).map((n) => fold(n as string));
          const score = names.some((n) => n === needle) ? 0 : names.some((n) => n.startsWith(needle)) ? 1 : names.some((n) => n.includes(needle)) ? 2 : 9;
          return { g, score };
        })
        .filter((item) => item.score < 9)
        .sort((a, b) => a.score - b.score || a.g.level - b.g.level || (a.g.name_en ?? "").localeCompare(b.g.name_en ?? ""))
        .slice(0, limit ?? 10);
      if (scored.length === 0) {
        return unavailable(`no place named '${query}'`, "Try another spelling or a larger area.");
      }
      const parents = new Map(geographies.map((g) => [g.geography_id, g]));
      return result({
        release,
        places: scored.map(({ g }) => ({
          geography_id: g.geography_id,
          name_en: g.name_en,
          name_si: g.name_si,
          name_ta: g.name_ta,
          level: g.level_name,
          parent: g.parent_id ? { geography_id: g.parent_id, name_en: parents.get(g.parent_id)?.name_en ?? null } : null,
        })),
      });
    },
  );

  server.registerTool(
    "get_place_profile",
    {
      title: "Place profile",
      description:
        "Census values for one place, each with unit, period, verification, dataset and source locator, plus the citation and the reuse notice. Optionally limit to some indicator ids.",
      inputSchema: {
        geography_id: z.string().describe("An id from search_places, for example 'LK11' or 'LK1103005'."),
        indicators: z.array(z.string()).optional().describe("Indicator ids to return; all if omitted."),
      },
      annotations: { readOnlyHint: true, openWorldHint: false },
    },
    async ({ geography_id, indicators }) => {
      try {
        const place = await api.place(geography_id);
        const wanted = indicators ? new Set(indicators) : null;
        const values = place.values.filter((v) => !wanted || wanted.has(v.indicator_id));
        const missing = indicators?.filter((id) => !values.some((v) => v.indicator_id === id)) ?? [];
        return result({
          release: place.release,
          publishable: place.publishable,
          use: place.use ?? null,
          geography: place.geography,
          values: values.map((v) => cite(v, place.datasets)),
          not_available: missing,
          similar_places: place.profile?.similar?.slice(0, 10) ?? null,
          similarity_space: place.profile?.space_id ? `${place.profile.space_id} v${place.profile.space_version}` : null,
          citation: place.citation,
          url: api.placeUrl(geography_id),
          notices: place.datasets.map((d) => ({ dataset_id: d.dataset_id, attribution: d.attribution, notice: d.notice })),
          guidance: GUIDANCE,
        });
      } catch (error) {
        if (error instanceof NotFound) {
          return unavailable(`no place with id '${geography_id}'`, "Use search_places to find the id.");
        }
        throw error;
      }
    },
  );

  server.registerTool(
    "list_indicators",
    {
      title: "List indicators",
      description: "The indicators in the release, with unit, definition and the levels they are published for. Filter by words in the name.",
      inputSchema: {
        query: z.string().optional().describe("Words to look for in indicator names, for example 'household' or 'age'."),
      },
      annotations: { readOnlyHint: true, openWorldHint: false },
    },
    async ({ query }) => {
      const { indicators, release } = await api.indicators();
      const needle = query ? fold(query) : null;
      const found = indicators.filter((i) => !needle || fold(`${i.name} ${i.id}`).includes(needle));
      if (found.length === 0) {
        return unavailable(`no indicator matching '${query}'`, "Call list_indicators without a query to see all.");
      }
      return result({
        release,
        count: found.length,
        indicators: found.slice(0, 100).map((i) => ({
          indicator_id: i.id,
          name: i.name,
          unit: i.unit,
          measure_type: i.measure_type,
          levels: i.levels,
          definition: i.definition,
        })),
        truncated: found.length > 100,
      });
    },
  );

  server.registerTool(
    "get_indicator",
    {
      title: "Indicator values at one level",
      description:
        "Every published value of one indicator at one level (province, district, ds or gn), sorted from highest to lowest, with the citation. Ranks are positions, not judgements.",
      inputSchema: {
        indicator_id: z.string(),
        level: z.enum(["country", "province", "district", "ds", "gn"]),
        top: z.number().int().min(1).max(500).optional().describe("Return only the first N values."),
        within: z
          .string()
          .optional()
          .describe("Only places inside this area, for example the GN divisions of DS division 'LK1103'."),
      },
      annotations: { readOnlyHint: true, openWorldHint: false },
    },
    async ({ indicator_id, level, top, within }) => {
      const { indicators } = await api.indicators();
      const meta = indicators.find((i) => i.id === indicator_id);
      if (!meta) {
        return unavailable(`no indicator '${indicator_id}'`, "Use list_indicators.");
      }
      if (!meta.levels.includes(level)) {
        return unavailable(`'${indicator_id}' is not published for level '${level}'`, `It is published for: ${meta.levels.join(", ")}.`);
      }
      try {
        const file = await api.indicatorLevel(indicator_id, level);
        const { geographies } = await api.geographies();
        const names = new Map(geographies.map((g) => [g.geography_id, g.name_en]));
        const parentOf = new Map(geographies.map((g) => [g.geography_id, g.parent_id]));
        const inside = (id: string) => {
          let current: string | null | undefined = parentOf.get(id);
          while (current) {
            if (current === within) {
              return true;
            }
            current = parentOf.get(current);
          }
          return false;
        };
        const scoped = file.values.filter((v) => v.value !== null && (!within || inside(v.geography_id)));
        const rows = scoped
          .sort((a, b) => (b.value as number) - (a.value as number))
          .slice(0, top ?? 50)
          .map((v, index) => ({ position: index + 1, geography_id: v.geography_id, name_en: names.get(v.geography_id) ?? null, value: v.value, unit: v.unit, period: v.period, value_status: v.value_status }));
        return result({
          release: file.release,
          indicator: { indicator_id, name: meta.name, unit: meta.unit, definition: meta.definition },
          level,
          within: within ?? null,
          values_published: scoped.length,
          total_of_values: meta.measure_type === "count" ? scoped.reduce((sum, v) => sum + (v.value as number), 0) : null,
          values: rows,
          citation: file.citation,
          guidance: GUIDANCE,
        });
      } catch (error) {
        if (error instanceof NotFound) {
          return unavailable(`values of '${indicator_id}' at '${level}'`, "This release has no file for it.");
        }
        throw error;
      }
    },
  );

  server.registerTool(
    "get_sources",
    {
      title: "Sources and reuse terms",
      description: "Where the release's data come from, each dataset's licence or rights status, attribution and reuse notice.",
      inputSchema: { dataset_id: z.string().optional().describe("One dataset id; all if omitted.") },
      annotations: { readOnlyHint: true, openWorldHint: false },
    },
    async ({ dataset_id }) => {
      const latest = await api.latest();
      const datasets = latest.datasets.filter((d) => !dataset_id || d.dataset_id === dataset_id);
      if (datasets.length === 0) {
        return unavailable(`no dataset '${dataset_id}' in release ${latest.release}`, "Call get_sources without an id.");
      }
      return result({
        release: latest.release,
        publishable: latest.publishable,
        citation: latest.citation,
        datasets: datasets.map((d) => ({
          dataset_id: d.dataset_id,
          title: d.title,
          source: d.source_name,
          homepage: d.source_homepage,
          rights_status: d.rights_status,
          licence: d.licence,
          commercial_reuse: d.commercial_reuse,
          attribution: d.attribution,
          notice: d.notice,
          decision: d.publication_decision,
        })),
      });
    },
  );

  server.registerTool(
    "compare_places",
    {
      title: "Compare places",
      description: "One indicator for two to ten places side by side, each value with its unit, period and source locator.",
      inputSchema: {
        indicator_id: z.string(),
        geography_ids: z.array(z.string()).min(2).max(10),
      },
      annotations: { readOnlyHint: true, openWorldHint: false },
    },
    async ({ indicator_id, geography_ids }) => {
      const rows = await Promise.all(
        geography_ids.map(async (id) => {
          try {
            const place = await api.place(id);
            const value = place.values.find((v) => v.indicator_id === indicator_id);
            return {
              geography_id: id,
              name_en: place.geography.name_en,
              level: place.geography.level_name,
              ...(value ? cite(value, place.datasets) : { value: null, not_available: true }),
              citation: place.citation,
            };
          } catch {
            return { geography_id: id, not_available: true, message: "no place with this id" };
          }
        }),
      );
      return result({ indicator_id, places: rows, guidance: GUIDANCE });
    },
  );

  return server;
}
