import type { Metadata } from "next";

import SiteFooter from "@/components/site-footer";
import SiteHeader from "@/components/site-header";
import { getLatest } from "@/lib/release";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "Sri Lanka Facts",
    template: "%s · Sri Lanka Facts",
  },
  description:
    "Every place in Sri Lanka, every number about it, with its source. A private preview of the Census Atlas 2024.",
  openGraph: {
    title: "Sri Lanka Facts",
    description:
      "Every place in Sri Lanka, every number about it, with its source. A private preview of the Census Atlas 2024.",
    type: "website",
    locale: "en_LK",
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  const latest = getLatest();
  return (
    <html lang="en">
      <body data-release={latest.release}>
        <SiteHeader />
        <main id="main" tabIndex={-1}>{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
