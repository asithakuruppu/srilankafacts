// End-to-end: start the built server over stdio and call each tool once.
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const root = process.argv[2];
const transport = new StdioClientTransport({ command: "node", args: ["dist/index.js"], env: { ...process.env, SLF_API_ROOT: root } });
const client = new Client({ name: "e2e", version: "0" });
await client.connect(transport);
const calls = [
  ["search_places", { query: "Nuwara Eliya", limit: 3 }],
  ["get_place_profile", { geography_id: "LK23", indicators: ["population_total", "households_total"] }],
  ["list_indicators", { query: "lighting electricity" }],
  ["get_indicator", { indicator_id: "population_density", level: "district", top: 3 }],
  ["get_sources", { dataset_id: "census-2024-gnd-tables" }],
  ["compare_places", { indicator_id: "population_total", geography_ids: ["LK11", "LK23", "LK45"] }],
  ["get_place_profile", { geography_id: "LK0000" }],
];
for (const [name, args] of calls) {
  const out = (await client.callTool({ name, arguments: args })).structuredContent;
  const text = JSON.stringify(out);
  console.log(`> ${name} ${JSON.stringify(args)}\n< ${text.length > 700 ? text.slice(0, 700) + " …" : text}\n`);
}
await client.close();
