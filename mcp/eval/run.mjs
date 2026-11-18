#!/usr/bin/env node
// Score the MCP server on an A02 evaluation set: each question is answered through the tools,
// deterministically, and scored as correct (exact, or within tolerance) and cited.
// Usage: node eval/run.mjs <eval.jsonl> <release dir> [report.md]
import fs from "node:fs";

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const [setPath, root, reportPath] = process.argv.slice(2);
const items = fs.readFileSync(setPath, "utf8").trim().split("\n").map((line) => JSON.parse(line));
const client = new Client({ name: "a02-harness", version: "0" });
await client.connect(new StdioClientTransport({ command: "node", args: ["dist/index.js"], env: { ...process.env, SLF_API_ROOT: root } }));
const call = async (name, args) => (await client.callTool({ name, arguments: args })).structuredContent;

const UNANSWERABLE_QUERY = [
  [/GDP/i, "gdp"],
  [/own a car/i, "vehicle"],
  [/income/i, "income"],
  [/local elections/i, "local authority election"],
];

async function answer(item) {
  switch (item.category) {
    case "lookup": {
      const out = await call("get_place_profile", { geography_id: item.geography_id, indicators: [item.indicator_id] });
      const value = out.values?.[0];
      return { got: value?.value ?? "not available", cited: Boolean(out.citation && value?.source_locator) };
    }
    case "comparison": {
      const out = await call("compare_places", { indicator_id: item.indicator_id, geography_ids: item.geography_ids });
      const [a, b] = out.places;
      return { got: a.value > b.value ? a.geography_id : b.geography_id, cited: out.places.every((p) => p.citation && p.source_locator) };
    }
    case "aggregation": {
      const out = await call("get_indicator", { indicator_id: item.indicator_id, level: "gn", within: item.geography_id, top: 500 });
      return { got: out.total_of_values ?? "not available", cited: Boolean(out.citation) };
    }
    case "definition": {
      const out = await call("list_indicators", { query: item.indicator_id });
      const found = out.indicators?.find((i) => i.indicator_id === item.indicator_id);
      return { got: found?.definition ?? "not available", cited: Boolean(out.release) };
    }
    case "unanswerable": {
      if (/in 1950/.test(item.question)) {
        const out = await call("get_place_profile", { geography_id: item.geography_id });
        const any1950 = (out.values ?? []).some((v) => v.period === "1950");
        return { got: any1950 ? "a value" : "not available", cited: true };
      }
      const query = UNANSWERABLE_QUERY.find(([pattern]) => pattern.test(item.question))?.[1] ?? item.question;
      const out = await call("list_indicators", { query });
      return { got: out.available === false ? "not available" : "an indicator", cited: true };
    }
    default:
      return { got: null, cited: false };
  }
}

const scores = {};
const failures = [];
for (const item of items) {
  const { got, cited } = await answer(item);
  const correct =
    typeof item.expected === "number"
      ? typeof got === "number" && Math.abs(got - item.expected) <= (item.tolerance ?? 0)
      : got === item.expected;
  const score = (scores[item.category] ??= { items: 0, correct: 0, cited: 0 });
  score.items += 1;
  score.correct += correct ? 1 : 0;
  score.cited += cited ? 1 : 0;
  if (!correct || !cited) {
    failures.push({ id: item.id, category: item.category, question: item.question, expected: item.expected, got, cited });
  }
}
await client.close();

const total = Object.values(scores).reduce((a, s) => ({ items: a.items + s.items, correct: a.correct + s.correct, cited: a.cited + s.cited }), { items: 0, correct: 0, cited: 0 });
const lines = [
  `# A02 evaluation: MCP server, ${items[0]?.release}`,
  "",
  `Run ${new Date().toISOString().slice(0, 10)} with \`node eval/run.mjs\` (deterministic tool calls, no language model).`,
  "",
  "| Category | Items | Correct | Cited |",
  "|---|---:|---:|---:|",
  ...Object.entries(scores).map(([name, s]) => `| ${name} | ${s.items} | ${s.correct} | ${s.cited} |`),
  `| **all** | ${total.items} | ${total.correct} | ${total.cited} |`,
  "",
  failures.length ? "## Failures" : "No failures.",
  ...failures.map((f) => `- ${f.id} (${f.category}): expected ${JSON.stringify(f.expected).slice(0, 80)}, got ${JSON.stringify(f.got).slice(0, 80)}, cited ${f.cited}`),
  "",
];
console.log(lines.join("\n"));
if (reportPath) {
  fs.writeFileSync(reportPath, lines.join("\n"));
}
