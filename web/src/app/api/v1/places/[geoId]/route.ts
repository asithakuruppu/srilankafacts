import fs from "node:fs";
import path from "node:path";

import { releaseRoot } from "@/lib/release";

export async function GET(
  _request: Request,
  context: { params: Promise<{ geoId: string }> },
) {
  const raw = (await context.params).geoId;
  const geoId = raw.replace(/\.json$/, "");
  if (!/^[A-Za-z0-9_-]+$/.test(geoId)) {
    return Response.json({ error: "invalid geography id" }, { status: 400 });
  }
  const file = path.join(releaseRoot(), "api/v1/places", `${geoId}.json`);
  if (!fs.existsSync(file)) {
    return Response.json({ error: "not found" }, { status: 404 });
  }
  return new Response(fs.readFileSync(file), {
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "public, max-age=300",
      "access-control-allow-origin": "*",
    },
  });
}
