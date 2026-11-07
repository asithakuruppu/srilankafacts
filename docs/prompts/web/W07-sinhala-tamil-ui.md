# W07: Sinhala and Tamil interface

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 3 | Frontend / Localisation | 1 | 2026-11-07 | draft (refresh with M03 at Stage 3) |

## When to use
When core pages are stable and the lead has arranged human translators or reviewers (D-012).

## Read first
- `AGENTS.md`
- Decision D-012 (languages)
- W01 typography decisions; W03/W04 templates

## Inputs (fill in)
```
LOCALES:     si, ta
SCOPE:       e.g. home, place pages, indicator names/definitions, methods summary
REVIEWERS:   who reviews translations (names stay outside the repo if private)
```

## Task
1. Add i18n routing (`/si/...`, `/ta/...`) with an established library compatible with the App Router. Add language switching and `hreflang`.
2. Extract UI strings. Add translatable fields for indicator names, short names and definitions in the catalogue (`name_si`, `name_ta`, …).
3. Produce **translation request files** for the human translators, with context and screenshots. You may include AI draft translations clearly marked `draft-machine`, but **no machine translation ships without human review**.
4. Number and date formatting per locale; check font rendering and line-height for Sinhala and Tamil scripts in every component.
5. Fallback rules: show English with a notice if a translation is missing; never mix languages within a sentence.
6. Tests: every route renders in each locale; no missing keys in scope; visual check screenshots.

## Constraints
- Published translations must have a reviewer recorded.

## Verify (show real output)
Missing-key report; screenshots per locale; Lighthouse scores per locale.

## Deliverables
i18n setup, translation files, catalogue fields, tests, a translator workflow doc.

## Done when
Core pages read naturally in Sinhala and Tamil, as confirmed by reviewers.

Report using the format in `AGENTS.md`.
