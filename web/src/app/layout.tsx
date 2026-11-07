import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sri Lanka Facts",
  description: "Every place in Sri Lanka, every number about it, with its source.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
