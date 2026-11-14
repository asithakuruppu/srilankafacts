import fs from "node:fs";
import lighthouse from "lighthouse";
import * as chromeLauncher from "chrome-launcher";

const [base, out, chromePath] = process.argv.slice(2);
const routes = ["/", "/explore", "/place/LK", "/place/LK11", "/place/LK1103", "/place/LK1103005",
  "/indicator/population_total", "/indicators", "/data", "/methods"];
const results = {};
for (const route of routes) {
  results[route] = [];
  for (let run = 0; run < 3; run++) {
    const chrome = await chromeLauncher.launch({ chromePath, chromeFlags: ["--headless=new"] });
    const r = await lighthouse(base + route, { port: chrome.port, output: "json", logLevel: "error",
      onlyCategories: ["performance"] });
    await chrome.kill();
    const a = r.lhr.audits;
    const js = (a["resource-summary"]?.details?.items ?? []).find((i) => i.resourceType === "script");
    const fetchKb = (a["network-requests"]?.details?.items ?? [])
      .filter((i) => i.resourceType === "Fetch" || i.resourceType === "XHR")
      .reduce((s, i) => s + (i.transferSize ?? 0), 0) / 1024;
    results[route].push({
      perf: Math.round(r.lhr.categories.performance.score * 100),
      lcp: a["largest-contentful-paint"].numericValue / 1000,
      tbt: a["total-blocking-time"].numericValue,
      cls: a["cumulative-layout-shift"].numericValue,
      jsKb: (js?.transferSize ?? 0) / 1024,
      dataKb: fetchKb,
    });
  }
  const med = (k) => results[route].map((x) => x[k]).sort((p, q) => p - q)[1];
  console.log(`${route}\t${med("perf")}\t${med("lcp").toFixed(2)}\t${Math.round(med("tbt"))}\t${med("cls").toFixed(3)}\t${Math.round(med("jsKb"))}\t${Math.round(med("dataKb"))}`);
}
fs.writeFileSync(out, JSON.stringify(results, null, 1));
