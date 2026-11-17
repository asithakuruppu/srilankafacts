import fs from "node:fs";
import path from "node:path";

import { getAtlasMeta } from "@/lib/release";
import type { ElectoralFile } from "@/lib/atlas/types";

/** Election results from the atlas bundle, or null when this build has none (say so, never fake). */
export function getElectoral(): ElectoralFile | null {
  const meta = getAtlasMeta();
  if (!meta?.electoral) {
    return null;
  }
  const file = path.resolve(process.cwd(), "public/release/atlas/electoral.json");
  if (!fs.existsSync(file)) {
    return null;
  }
  return JSON.parse(fs.readFileSync(file, "utf8")) as ElectoralFile;
}
