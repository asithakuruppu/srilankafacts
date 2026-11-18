#!/usr/bin/env node
// Write translator request files from the interface string catalogue (W07).
// Usage: node scripts/translation-requests.mjs  (from web/; writes ../docs/translation/*.csv)
import fs from "node:fs";
import path from "node:path";

const source = fs.readFileSync(path.resolve("src/lib/i18n/messages.ts"), "utf8");
function block(name) {
  const start = source.indexOf(`const ${name}`) >= 0 ? source.indexOf(`const ${name}`) : source.indexOf(`export const ${name}`);
  const open = source.indexOf("{", start) + 1;
  const body = source.slice(open, source.indexOf("\n}", open));
  const entries = {};
  for (const match of body.matchAll(/"([a-zA-Z.]+)":\s*\n?\s*"((?:[^"\\]|\\.)*)"/g)) {
    entries[match[1]] = match[2];
  }
  return entries;
}
const en = block("EN");
const context = (key) =>
  key.startsWith("nav.") ? "Main navigation link (one or two words)"
  : key.startsWith("lens.") ? "Atlas lens tab: a way of looking at the map (one word)"
  : key.startsWith("picker.") ? "Small label above the chosen map layer"
  : key.startsWith("panel.") ? "Heading in the place panel"
  : "Language switch and its notice";
const csv = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
for (const [locale, name] of [["si", "SI"], ["ta", "TA"]]) {
  const drafts = block(name);
  const lines = ["key,english,context,draft,draft_status,reviewed_translation,reviewer,reviewed_on"];
  for (const [key, english] of Object.entries(en)) {
    lines.push([key, english, context(key), drafts[key] ?? "", drafts[key] ? "draft-machine" : "missing", "", "", ""].map(csv).join(","));
  }
  const out = path.resolve(`../docs/translation/request-${locale}.csv`);
  fs.writeFileSync(out, lines.join("\n") + "\n");
  console.log(`${out}: ${Object.keys(en).length} strings`);
}
