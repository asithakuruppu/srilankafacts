# Source dossier: Election Commission of Sri Lanka

Prompt R01 · checked 2026-11-15 · catalogue: `catalog/sources/election-commission.yaml`, `catalog/datasets/election-results.yaml`

Why: Stage 2 election atlas ([development strategy §3, Stage 2 item 3](../../roadmap/development-strategy.md); [live-events-and-sources §3](../../architecture/live-events-and-sources.md#3-election-results)). Results by electoral district (ED, 22) and polling division (PD, 160), linked to census profiles through GN composition (G05).

## Findings

| Finding | Status | Evidence |
|---|---|---|
| Official site is `https://elections.gov.lk`. The root page is a language chooser; English content is under `indexEn.html` and `en/…` | ✅ | U1, U2 |
| Results pages per election type: presidential (`en/elections/results_pre_E.html`), parliamentary (`results_pe_E.html`), provincial (`results_pc_E.html`), local authorities (`results_lae_E.html`) | ✅ | U3 (links on U2) |
| Presidential results 1982–2019 are linked as PDFs: one PDF per election up to 2015, and one per ED plus all-island in 2019 | ✅ | U3 |
| **2024 presidential election (21 Sep 2024):** a separate results page (linked from the Sinhala results page) lists **232 PDF links**: 160 PD files and 22 postal-vote files named `<ED>_<PD letter>.pdf` / `<ED>_PV.pdf` (182 in all), 22 district files, 22 district preference-count files, 3 all-island files, two `XXX…` placeholders (not fetched) and one unrelated link (232 links in all) | ✅ | U4; counts from the snapshot |
| PD file names do not always equal the PD letter (`1_AA.pdf` is Colombo North "A"; `15_DJ`, `19_ED`, `20_BD`, `22_CD` also exist). The letter is read from inside each PDF, never from the file name | ✅ | U4; PDF headers |
| Each PD/postal PDF is a 2-page signed result sheet: candidate number, name, party abbreviation, votes, percentage; then valid, rejected, polled and registered electors | ✅ | U5, U6 |
| **Some PDFs are scans with no text layer** (e.g. `1_PV.pdf`, Colombo postal votes); others carry an OCR text layer with errors (e.g. `1_B.pdf` reads party code `IND10` as `INDIO`, and candidate 4's row is missing from the text layer) | ✅ | U5, U6, PDFKit text extraction |
| Postal votes are a separate result per ED (`<ED>_PV.pdf`), not allocated to PDs | ✅ | U4, U5 |
| **Register of electors by PD, 2016–2025** (22 pages, one per ED): PD letter, PD name and the number of registered electors per year. This is the official list of the 22 EDs and 160 PDs used here | ✅ | U7 |
| The register lists PD "K Kilinochchi" under ED 10 Jaffna | ✅ | U7 p.10 |
| A 2023 "polling-division-wise" register PDF linked from the home page returns 404 | ❌ | U8 |
| `results.elections.gov.lk` (the live results site; search results show per-PD PDFs under `/pre2024/results/`) could not be reached: connection refused from two networks | ❌ | U9 |
| `wp-content/uploads/openData/` returns 403 (no directory listing) | ✅ | U10 |
| **No terms of use, copyright notice, licence or reuse statement** found on any page fetched | ✅ (absence on the pages fetched; not proof that none exists) | U1–U4, U11–U12: HTML searched for "copyright", "©", "terms", "disclaimer", "reproduc", "all rights" |
| Polling divisions are not published with boundaries by the Commission (no GIS files linked on any page fetched) | ✅ (on pages fetched) | U2–U4, U11–U12 |
| A 2017 extraordinary gazette (No. 2046/12) appears to list polling stations or districts with DS and GN divisions | 🟡 search-result snippet only; not read | U13 (unreachable) |
| Contact: the site has a contact page for the Commission and an information officers (RTI) page | ✅ links exist; content not read | U2 links `en/contactus/contactus_election_commission_E.html`, `en/contactus/contactus_information_officers_E.html` |

## Community extractions (cross-check only)

| Repository | What | Licence | Status |
|---|---|---|---|
| `nuuuwan/lk_elections` | Results TSVs per election, e.g. `public/data/elections/government-elections-presidential.regions-ec.2024.tsv` (204 rows: 22 ED, 160 PD, 22 postal "PD" `EC-NNP`, `LK`; columns valid, rejected, polled, electors and one column per party code). Last push 2024-11-19 | **None** (GitHub reports no licence) | ✅ |
| `nuuuwan/gig-data` | `ents/gnd.tsv` (14,021 GN rows, each with `ed_id` and `pd_id`), `ents/pd.tsv` (160), `ents/ed.tsv` (22), `geo/pd/*.json` (160) and `geo/ed/*.json` (22) geometries. Last push 2026-08-02 | **None**; geometry and membership source not stated | ✅ |
| `nuuuwan/elections_lk` | Package of the same author | Not checked (GitHub API unreachable at the time) | ❓ |

The Commission's IDs in nuuuwan's files (`EC-01`, `EC-01A`) are the ED number plus PD letter, the same codes the Commission prints (`1 - Colombo`, `B - Colombo Central`). ✅

## URLs checked (2026-11-15)

| # | URL | HTTP | Note |
|---|---|---|---|
| U1 | `https://elections.gov.lk/` | 200 | language chooser |
| U2 | `https://elections.gov.lk/indexEn.html` | 200 | English home |
| U3 | `https://elections.gov.lk/en/elections/results_pre_E.html` | 200 | presidential results (to 2019) |
| U4 | `https://elections.gov.lk/si/elections/PRE_2024_Results.html` | 200 | 2024 presidential results page; snapshotted |
| U5 | `…/wp-content/uploads/2024/09/PRE_2024_Results/1_PV.pdf` | 200 | scan, no text layer |
| U6 | `…/wp-content/uploads/2024/09/PRE_2024_Results/1_B.pdf` | 200 | OCR text layer with errors |
| U7 | `…/wp-content/uploads/2026/10/All_District_Registered_Electores_2016_2025.pdf` | 200 | 22 pages; snapshotted |
| U8 | `…/wp-content/uploads/pdf/statistics/electoral_reg_2023_PollingDivisionWise.pdf` | 404 | |
| U9 | `https://results.elections.gov.lk/pre2024/` | none | connection refused / timed out |
| U10 | `…/wp-content/uploads/openData/` | 403 | |
| U11 | `https://elections.gov.lk/en/download/publications_E.html` | 200 | |
| U12 | `https://elections.gov.lk/en/voters/voters_statistics_E.html` | 200 | links U7 |
| U13 | `https://www.documents.gov.lk/view/extra-gazettes/2017/11/2046-12_E.pdf` | none | connection dropped (two attempts, two routes) |

## Notes on access

- Python's default certificate store on the lead's machine rejects `elections.gov.lk` (its chain ends at a Sectigo R46 root). The pipeline verifies it with the `certifi` bundle instead; verification is never turned off.
- Downloads are paced at one request per second; the 2024 set is about 230 files.

## Open questions

1. Reuse terms for the results and the register (letter drafted: [`docs/outreach/2026-11-15-election-commission-results-and-gn-lists.md`](../../outreach/2026-11-15-election-commission-results-and-gn-lists.md)).
2. Does the Commission hold an official list of GN divisions per polling division (it maintains the register by GN division)? Can it be shared?
3. Are machine-readable results (CSV/JSON) available, as `results.elections.gov.lk` seems to serve on election night?
