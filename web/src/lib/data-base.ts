// Where the browser reads the release's static API and files.
// Unset (local `pnpm dev` / `pnpm start`): this site's own /api/v1 route handlers.
// Static deploy: the data site's origin, for example https://data.example.org (docs/ops/deploy.md).
export const DATA_BASE = (process.env.NEXT_PUBLIC_DATA_BASE ?? "").replace(/\/+$/, "");

/** URL of a release path such as `/api/v1/places/LK.json`. */
export function dataUrl(path: string): string {
  return `${DATA_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}
