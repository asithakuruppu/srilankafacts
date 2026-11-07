# W03: Place pages

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1 | Frontend / Content | 1 | 2026-11-07 | active |

## When to use
To build `/place/[geoId]` for every admin level (and later other schemes).

## Read first
- `AGENTS.md`
- `docs/vision/vision-and-strategy.md` §6 (flagship scope)
- `docs/architecture/data-model.md` §3, §6–§7 (names, badges, provenance)
- W01 components, W02 shell, release data layout

## Inputs (fill in)
```
RELEASE:        version to build from
HEADLINE_INDICATORS: ordered list per level (agree with the lead)
```

## Task
1. Server-rendered template: name (with Sinhala/Tamil where available), level label, breadcrumb up the hierarchy, child units list, key numbers (stat tiles with badges), age-sex pyramid, housing and amenities charts, a full indicator table with units and sources, a **"How to cite"** block (release, URL, access date), downloads for this place.
2. Comparisons: against the parent unit and national value. Rankings only for neutral, meaningful measures (for example density or amenities). **No rankings by ethnicity or religion.**
3. Metadata: `<title>`, description, canonical URL, JSON-LD (`Place`, `Dataset` with licence and creator), OpenGraph image (a pre-rendered map thumbnail generated at build).
4. **Build strategy:** measure the build time for SSG of all units (~14k GN) vs on-demand/ISR for GN pages. Report the numbers and recommend. Don't decide silently.
5. GN pages use a lighter template. Add an indexing rule (for example `noindex` if fewer than N indicators exist) and justify it.
6. Sitemap(s) split by level.
7. Tests: snapshot tests for a province, district, DS and GN page; a link checker over generated pages; accessibility check (axe) on each template.

## Constraints
- Every number on the page links to its provenance (a panel or the source page).
- Duplicate GN names within a parent exist ✅, so always show the parent context in titles.
- Neutral wording for sensitive topics (ethnicity, religion).

## Verify (show real output)
Build-time measurements; screenshots of each template (mobile and desktop); axe results; link-checker summary.

## Deliverables
Templates, data loaders, OG image generation, sitemaps, tests.

## Done when
Every admin unit has a fast, citable page whose numbers match the release.

Report using the format in `AGENTS.md`.
