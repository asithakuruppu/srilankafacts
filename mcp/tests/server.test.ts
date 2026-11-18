import path from "node:path";

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { beforeAll, describe, expect, it } from "vitest";

import { StaticApi } from "../src/api.js";
import { createServer } from "../src/server.js";

const FIXTURE = path.resolve(__dirname, "../../web/fixtures/preview");
let client: Client;

async function call(name: string, args: Record<string, unknown>) {
  const response = await client.callTool({ name, arguments: args });
  return response.structuredContent as Record<string, any>;
}

beforeAll(async () => {
  const server = createServer(new StaticApi(FIXTURE, "https://example.org"));
  const [clientSide, serverSide] = InMemoryTransport.createLinkedPair();
  client = new Client({ name: "test", version: "0" });
  await Promise.all([server.connect(serverSide), client.connect(clientSide)]);
});

describe("MCP tools over the fixture release", () => {
  it("lists six read-only tools", async () => {
    const { tools } = await client.listTools();
    expect(tools.map((t) => t.name).sort()).toEqual([
      "compare_places",
      "get_indicator",
      "get_place_profile",
      "get_sources",
      "list_indicators",
      "search_places",
    ]);
    expect(tools.every((t) => t.annotations?.readOnlyHint)).toBe(true);
  });

  it("finds Colombo and returns its id and level", async () => {
    const out = await call("search_places", { query: "colombo" });
    expect(out.places[0].geography_id).toBe("LK11");
  });

  it("never returns a bare number: values carry unit, period, source and citation", async () => {
    const out = await call("get_place_profile", { geography_id: "LK11", indicators: ["population_total"] });
    const value = out.values[0];
    expect(value.value).toBe(2375415);
    expect(value).toMatchObject({ unit: "persons", period: "2024", dataset_id: "census-2024-gnd-tables" });
    expect(value.source_locator).toBeTruthy();
    expect(out.citation).toContain("Sri Lanka Facts");
    expect(out.url).toBe("https://example.org/place/LK11");
  });

  it("says not available instead of guessing", async () => {
    expect((await call("get_place_profile", { geography_id: "LK99" })).available).toBe(false);
    expect((await call("search_places", { query: "Atlantis" })).available).toBe(false);
    const missing = await call("get_place_profile", { geography_id: "LK11", indicators: ["gdp_per_capita"] });
    expect(missing.not_available).toEqual(["gdp_per_capita"]);
  });

  it("ranks an indicator and reports levels it is not published for", async () => {
    const ranked = await call("get_indicator", { indicator_id: "population_total", level: "district", top: 3 });
    expect(ranked.values[0].position).toBe(1);
    expect(ranked.citation).toBeTruthy();
    const none = await call("list_indicators", { query: "zzzz" });
    expect(none.available).toBe(false);
  });

  it("gives reuse terms and compares places", async () => {
    const sources = await call("get_sources", {});
    expect(sources.datasets.length).toBeGreaterThan(0);
    expect(sources.datasets[0]).toHaveProperty("notice");
    const compared = await call("compare_places", { indicator_id: "population_total", geography_ids: ["LK11", "LK1"] });
    expect(compared.places).toHaveLength(2);
  });
});
