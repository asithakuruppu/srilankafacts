import type { Metadata } from "next";

import GnPlace from "@/components/gn-place";
import { dataUrl } from "@/lib/data-base";

export const metadata: Metadata = {
  title: "Grama Niladhari division",
  robots: { index: false, follow: true },
};

/** Static-host GN page: `/place/LK…` for a GN id is served from here (docs/ops/deploy.md). */
export default function GnPlacePage() {
  return (
    <>
      <noscript>
        <div className="shell section">
          <p className="notice">
            GN pages on this site need JavaScript. Every value is also in the place&apos;s API
            file, <code>{dataUrl("/api/v1/places/{GN id}.json")}</code>, with its source.
          </p>
        </div>
      </noscript>
      <GnPlace />
    </>
  );
}
