# Rights memo: election-results (Election Commission) and electoral geography

Reviewed 2026-11-15 · Prompt R02 · **Not legal advice.**

Covers three things the election atlas needs:
(A) the Election Commission's published results and register of electors;
(B) boundaries of electoral districts (ED) and polling divisions (PD);
(C) a list of GN divisions per PD (the "membership list" that G05 prefers over any overlay).

## Evidence

| # | Source | Where | Finding |
|---|---|---|---|
| E1 | Election Commission website | `https://elections.gov.lk/indexEn.html`, `en/elections/results_pre_E.html`, `si/elections/PRE_2024_Results.html`, `en/download/publications_E.html`, `en/voters/voters_statistics_E.html` (fetched 2026-11-15) | No terms of use, copyright notice, licence or reuse statement on any of these pages ✅ (HTML searched for "copyright", "©", "terms", "disclaimer", "reproduc", "all rights") |
| E2 | Result PDFs | e.g. `…/PRE_2024_Results/1_B.pdf`, `1_PV.pdf` | Headed "OFFICIAL RESULTS", "ELECTION COMMISSION", signed "on behalf of Election Commission". No copyright or reuse notice on either page ✅ (two files read; the rest not read for notices) |
| E3 | Register of electors by PD 2016–2025 | `…/2026/10/All_District_Registered_Electores_2016_2025.pdf` | Header names the Commission and the Elections Secretariat; no copyright or reuse notice ✅ (pages 1 and 22 read) |
| E4 | `nuuuwan/lk_elections` | GitHub repository metadata | No licence ✅. Under default copyright, no licence means no permission to reuse the repository's own content ❓ (general rule; not checked for Sri Lanka) |
| E5 | `nuuuwan/gig-data` | GitHub repository metadata; files `ents/gnd.tsv`, `geo/pd/*.json` | No licence ✅; the origin of the PD geometries and of each GN's `pd_id` is not stated anywhere in the repository files listed ✅ (also recorded in [ecosystem-landscape.md](../ecosystem-landscape.md)) |
| E6 | Other PD boundary sources | Web search 2026-11-15 ("polling division boundaries shapefile"); HDX COD-AB (admin only, [cod-ab-lka](cod-ab-lka.md)); NSDI service layers ([nsdi-admin-boundaries](nsdi-admin-boundaries.md)) | **No public PD boundary file from an official source found** ✅ (absence in search is not proof). COD-AB and NSDI carry admin levels only |
| E7 | Sri Lanka Intellectual Property Act No. 36 of 2003 | not read | Whether election results (facts reported by a public body) are protected, or fall under an exclusion for official texts, is a question for a lawyer ❓ |

## Uses

### (A) Results and register of electors

| Use | Classification | Note |
|---|---|---|
| Ingest, check and keep internally | Not addressed | What this task does. Nothing is published |
| Display on the website (counts, shares, turnout, by ED and PD) | **Not addressed** | Needs a recorded lead decision, as D-030 did for DCS (proposed: D-035) |
| Redistribute the original PDFs | Not addressed | Not planned: link to the Commission's page instead (as D-030 does for DCS files) |
| Redistribute derived tables (downloads, API) | Not addressed | Same decision as display |
| Commercial use | Not addressed → **not allowed** | data-model §2.4: only with `commercial_reuse: yes` |
| Modification | Not addressed | We re-tabulate, never alter values; corrections go to `overrides/` |
| Share-alike | None stated | — |
| Compatibility with CC BY 4.0 outputs | Unclear | Depends on the Commission's answer |

### (B) ED and PD boundaries

| Option | Classification | Note |
|---|---|---|
| ED = admin districts (Jaffna ED = Jaffna + Kilinochchi districts; Vanni ED = Mannar + Vavuniya + Mullaitivu) | No boundary file needed | ED geometry is the union of COD-AB districts (CC BY-IGO, [cod-ab-lka](cod-ab-lka.md)). The district grouping is evidenced by the register (E3) only for Kilinochchi ✅; the Vanni grouping is 🟡 (PD names Mannar, Vavuniya, Mullaitivu under ED 11 in E3, not a legal text). Checked against nuuuwan's GN → ED assignment in QA |
| PD geometry from `nuuuwan/gig-data` | **Not permitted to redistribute** (no licence, E5) | Internal comparison only, never in a release or in Git |
| PD geometry from any official source | Not available (E6) | Ask the Commission and the Survey Department |

### (C) GN membership of PDs

| Option | Classification | Note |
|---|---|---|
| Official list from the Commission | Not available publicly (E1, E6) | Asked for in the drafted letter |
| `nuuuwan/gig-data` `ents/gnd.tsv` (`pd_id` per GN) | **Not permitted to redistribute** (no licence, origin unknown, E5) | Used **only inside the local build** to test G05's checks (weight sums, coverage, IoU, denominators). Never committed to `catalog/`, never in a release |
| Overlay of PD geometry on GN geometry | Blocked | Needs PD geometry with rights (B) |

## Catalogue changes

- `catalog/sources/election-commission.yaml`: homepage recorded; `rights.status: unclear`, `commercial_reuse: unknown`, evidence E1–E3.
- `catalog/datasets/election-results.yaml`: `rights: inherit`; no `publication` block (proposed D-035 must be Accepted first; the catalogue validator refuses a publication block that names a non-Accepted decision).
- `catalog/sources/nuuuwan.yaml`: notes extended (E4, E5); stays `unclear`.

## Attribution (proposed, if publication is allowed)

"Source: Election Commission of Sri Lanka, Presidential Election 2024, official results by polling division and postal votes by electoral district (elections.gov.lk)."

## Questions for the publisher (feed R04)

In the drafted letter [`docs/outreach/2026-11-15-election-commission-results-and-gn-lists.md`](../../outreach/2026-11-15-election-commission-results-and-gn-lists.md):

1. May the published results and register of electors be reproduced, with attribution, on a website and in downloadable tables, including commercially?
2. Does the Commission hold a list of GN divisions in each polling division (for the 2024 register)? Can it be shared, and on what terms?
3. Are PD boundary files held by the Commission or the Survey Department, and on what terms?
4. Are the 2024 results available in a machine-readable format (CSV, Excel, JSON)?

## For a lawyer

Whether official election results are protected by copyright in Sri Lanka at all (E7), and if so whether a non-commercial publication with attribution is a reasonable risk position, as the lead took for DCS tables in D-030.
