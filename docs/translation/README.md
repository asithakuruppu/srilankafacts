# Translation workflow (W07)

Status: **framework built, no locale reviewed** · 2026-11-18 · Decisions: D-012 (Accepted), D-050 (Proposed)

## What exists

- The interface string catalogue `web/src/lib/i18n/messages.ts`: English source and Sinhala and Tamil **machine drafts** (`draft-machine`) for the navigation, the atlas lens tabs and the place panel's headings (25 strings).
- An opt-in language switch in the header. English is the default. Choosing සිංහල or தமிழ் shows the drafts under a banner in that language and in English saying they are machine drafts, not reviewed. The choice is stored in the visitor's browser only.
- Place names in Sinhala and Tamil come from the geography spine (official sources), never from machine translation (D-012). Sinhala names exist for every level; Tamil names for every level above GN.
- A missing-key test (`web/tests/unit/i18n.test.ts`) fails if a Sinhala or Tamil key is missing.

## For translators

1. Open `request-si.csv` or `request-ta.csv`. Each row has the key, the English, where it appears, and a machine draft.
2. Fill `reviewed_translation` (keep the draft if it is right), `reviewer` (a name or initials; private names can stay outside the repository) and `reviewed_on`.
3. Return the file. An agent copies the reviewed text into `messages.ts`, sets the locale's status to `reviewed` and records the reviewer in the table below.

Regenerate the request files after adding strings: `node scripts/translation-requests.mjs` (in `web/`).

## Reviews

| Locale | Strings | Reviewer | Date |
|---|---:|---|---|
| si | 25 | none yet | – |
| ta | 25 | none yet | – |

## Not done

- `/si/…` and `/ta/…` routes with `hreflang` (W07 step 1): needs an i18n routing library, so a decision first; the opt-in switch covers the preview.
- Indicator names and definitions in Sinhala and Tamil (`name_si`, `name_ta` in `catalog/indicators/`).
- Body text, methods, numbers and dates per locale; Lighthouse per locale; font checks in every component.
