import fs from "node:fs";
import { createRequire } from "node:module";
import lighthouse from "lighthouse";
import * as chromeLauncher from "chrome-launcher";

const [base, out, chromePath, playwrightDir] = process.argv.slice(2);
const require = createRequire(playwrightDir + "/");
const { chromium } = require("@playwright/test");
const axeSource = fs.readFileSync(new URL("./node_modules/axe-core/axe.min.js", import.meta.url), "utf8");
const routes = ["/", "/explore", "/place/LK", "/place/LK11", "/place/LK1103", "/place/LK1103005",
  "/indicator/population_total", "/indicators", "/data", "/methods"];
const result = { axe: {}, lighthouse: {} };
const browser = await chromium.launch({ executablePath: chromePath });
for (const scheme of ["light", "dark"]) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: scheme });
  const page = await context.newPage();
  for (const route of routes) {
    await page.goto(base + route, { waitUntil: "networkidle" });
    await page.addScriptTag({ content: axeSource });
    const r = await page.evaluate(() =>
      window.axe.run(document, { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] } }));
    result.axe[`${scheme} ${route}`] = r.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length,
      targets: v.nodes.slice(0, 5).map((n) => n.target.join(" ")) }));
    const n = r.violations.reduce((s, v) => s + v.nodes.length, 0);
    console.log(`axe ${scheme}\t${route}\t${r.violations.length} rules\t${n} nodes\t${r.violations.map((v) => v.id).join(",")}`);
  }
  await context.close();
}
await browser.close();
for (const route of routes) {
  const chrome = await chromeLauncher.launch({ chromePath, chromeFlags: ["--headless=new"] });
  const r = await lighthouse(base + route, { port: chrome.port, output: "json", logLevel: "error", onlyCategories: ["accessibility"] });
  await chrome.kill();
  const failing = Object.values(r.lhr.audits).filter((a) => a.score === 0 && a.scoreDisplayMode === "binary").map((a) => a.id);
  result.lighthouse[route] = { score: Math.round(r.lhr.categories.accessibility.score * 100), failing };
  console.log(`lighthouse\t${route}\t${result.lighthouse[route].score}\t${failing.join(",")}`);
}
fs.writeFileSync(out, JSON.stringify(result, null, 1));
