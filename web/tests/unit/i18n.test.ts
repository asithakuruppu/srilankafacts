import { describe, expect, it } from "vitest";

import { EN, LOCALES, MESSAGES, translate } from "@/lib/i18n/messages";

describe("interface strings", () => {
  it("has every English key in each locale (missing-key report)", () => {
    const report = LOCALES.filter((locale) => locale.id !== "en").map((locale) => ({
      locale: locale.id,
      missing: Object.keys(EN).filter((key) => !(key in MESSAGES[locale.id])),
    }));
    expect(report).toEqual([
      { locale: "si", missing: [] },
      { locale: "ta", missing: [] },
    ]);
  });

  it("marks unreviewed locales as machine drafts and falls back to English", () => {
    expect(LOCALES.find((l) => l.id === "si")?.status).toBe("draft-machine");
    expect(translate("en", "panel.compared")).toBe("Compared to where?");
    expect(translate("ta", "nav.atlas")).not.toBe(EN["nav.atlas"]);
  });
});
