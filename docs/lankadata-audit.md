# Audit of lankadata.net (Lanka Data Net, "LDN") — for Sri Lanka Facts

Audit date: 2026-11-07. Method: direct HTTP fetches of pages, page source/JS, the site's own JSON endpoints, GitHub and Hugging Face public APIs. Raw captures were kept in a scratch folder.
**Legend:** ✅ independently verified (I fetched it / saw it in code or live response) · 🟡 claimed by the site, not verified · ❌ not found.
Not done: I did not run AI chat queries (no way to judge quality without burning their rate limit), did not test authenticated areas, did not load-test, and did not browse every registry page's search function.

## 0. Summary

LankaData is a **WordPress marketing site** (WP 7.1.4, theme "data-science-specialist", Yoast, Jetpack, Wordfence, WP Statistics, Site Kit) fronting a **custom PHP backend (`/legal-search.php`)** that provides document search, "latest documents", PDF summarisation and a RAG chat. Its real asset is a **crawled document archive** (judgments, gazettes, CBSL/CSE/DMC/police/ministry releases, etc.) plus **registry-style directories**. It is a *document and registry search* product with an AI layer, **not a statistical/number-centric platform like USAFacts**. Several headline claims (api.lankadata.net, "100+ endpoints", "99.9% availability", "1B+ records") are unsupported by anything I could find.

## 1. Features and services

| # | Finding | Evidence | Source | Verified | Implication for Sri Lanka Facts |
|---|---|---|---|---|---|
| 1.1 | **Unified document search** across ~40 categories (courts, legislation, gazettes, Cabinet decisions, CBSL, CSE, customs tariffs, tax, Hansards, police/ministry news, DMC disaster/weather) with category filter, pagination, "top 500 matches" cap | Search response for `q=tax` returned `total: 2728`, `per_page: 20`, notice "Showing the top 500 matches" | `/legal-search.php?action=search&q=tax&type=all&page=1` | ✅ | The document-search space is covered. Don't compete on "search PDFs"; compete on structure and numbers. |
| 1.2 | **"Latest documents" feed**, 500 items, grouped Government/Legal/Economy/Business/Tax/Climate, refreshed by a generator (`generated_at` timestamp) | `count: 500`; 40 `ds_id` values (e.g. `cse_reports`, `sc_judgements`, `dmc_situation_reports`, `cbsl_stats_daily_price`) | `/legal-search.php?action=latest` | ✅ | Gives a concrete list of the sources they ingest, and shows ingest runs near-daily. A useful source-coverage checklist. |
| 1.3 | **Seven registries**: IP (trademarks/patents/designs), Customs tariff/HS codes, NMRA medicines, Ayurvedic medicines, EROC registered companies, CSE listed companies, EDB exporters | Registry hub page; registry pages call the same `legal-search.php?action=search` | `/registries/`, `/registered-companies-in-sri-lanka/` | ✅ (pages exist and use shared search endpoint); record counts 🟡 | Registries are a strong utility draw (due diligence). Worth matching with better entity pages and cross-linking. |
| 1.4 | **Public-sector directory** (ministries, departments, provincial councils, statutory boards, public companies, municipal/urban councils, pradeshiya sabhas) | Ministries page lists names only | `/ministries/` | ✅ list exists; no data depth seen (no budgets, staff, contacts evident in the extract I read) | Thin directory. Linking each body to budgets, audits, procurement and spending would leapfrog it. |
| 1.5 | **Per-document AI summary** and **chat with a document / uploaded PDF or image** | JS: `action=summarize&pdf_url=…`, chat payload fields `pdf_url`, `pdf_hashes`, `image_hashes`, `pdf_text`; summaries cached in `localStorage` | Inline JS on homepage and `/dashboard/` | ✅ (code); output quality ❌ untested | Document-level Q&A is table stakes. Citations to the exact passage matter more than having the feature. |
| 1.6 | **"Chat2Find" assistant with domain experts**: LankaLaw, LankaTax, LankaBIZ, NewsDive, ExamPazz, Cheap2Find | Expert models page; chat2find.com model picker lists LankaBIZ/LankaTax/ExamPazz/NewsDive/Cheap2Find; guest limit "5 left" | `/expert-models/`, https://chat2find.com | ✅ (UI exists); accuracy ❌ | The AI product is really Chat2Find (a separate consumer chat app). LDN is its data supplier. |
| 1.7 | **Dark mode, GA4 analytics** | WP Dark Mode plugin config; `gtag('config','G-0P315G5CZ8')` | Homepage source | ✅ | Minor. |
| 1.8 | Pages exist for **citizen-services categories** (health, housing, environment, employment, etc.) | Entries in page sitemap | `/page-sitemap.xml` | ✅ URLs exist; content not reviewed | Likely link directories; not reviewed in depth. |

## 2. Data sources and collection methods

- **Claimed sources:** Government Printer's Dept, Supreme Court, Court of Appeal, Parliament, Education ministry, CSE, CBSL, Registrar of Companies, NMRA, Customs, Inland Revenue, "other official public authorities". 🟡 (homepage). The latest-feed `link` fields point at original publisher URLs (e.g. police.lk, dmc.gov.lk, documents.gov.lk, customs.gov.lk), which ✅ confirms the **crawl-and-link-back** model for many items.
- **Method:** "OpenPIN" backend harvester that "continuously indexes websites, records, publications, and open datasets". The OpenPIN page has a "Code" heading but **no repository link and no technical detail** that I could find. ❌ unverified beyond marketing text. Source: `/openpin/`.
- **Mixed hosting of files:** some PDFs are linked to LDN-controlled domains (e.g. `lankalaw.net/wp-content/uploads/ca_judgements/...`) — so they **mirror** at least some documents. ✅ Source: search response.
- **AI-derived fields:** court records include generated "Summary" and subject-tag strings ("Related Action"). ✅ Search response. These are machine-generated overlays; the site does not visibly label them as such in the sample JSON.
- **Implication:** there is no evidence of per-dataset methodology, update schedule, or provenance metadata. Sri Lanka Facts can lead with a visible provenance record per series (publisher, URL, retrieval date, licence, transform).

## 3. Datasets, documents and repositories

- **Claims vs. evidence of scale.** Homepage says "over one billion datasets"; the infrastructure section says "10+ billion data point corpus"; the Intelligent-Layer text says "90,000+ public documents"; the API box says "1B+ data records". These are inconsistent with each other and unitless. Only the **90,000-documents** figure is plausible for a PDF archive. 🟡 none verified. Search total of 2,728 hits for "tax" is the only count I observed. ✅
- **Public repositories:** GitHub org `Lanka-Data-Net` (created 2026-05-24) has **2 public repos**: `Data-Archive` (folders "Economic Data", "Legal Data" showing size 0 in the contents API, plus a README) and `Lanka-Law` (README only). No licence, 0 stars. ✅ Source: https://github.com/Lanka-Data-Net, GitHub API.
  - So the "open data archive" on GitHub was **not populated with data files at audit time** (README-only / empty folders as far as the contents API shows). ✅
- **Hugging Face (`LDNet`):** two datasets, `Chat2Find-Corpus` (~255M tokens, ~279k records, MIT in metadata, 47 downloads) and `Chat2Find-Instruct-Reasoning-Sample` (5k-record sample, MIT, 17 downloads). The full 279k/1.8 GB set is **gated and sold** via Stripe under a "commercial/advanced research license" (hosted under a different HF org, `Chat2Find`). ✅ Source: https://huggingface.co/LDNet and dataset cards. Note: these are chat-log-derived AI training data, not public-statistics data. The site presents them under "Open Source Data Sets", which is misleading.
- **Implication:** the "open data" story is thin: the public repos are placeholders, the real archive is accessible only through the website's search. A genuinely downloadable, versioned, machine-readable open dataset (CSV/Parquet + manifest) would be a clear differentiator.

## 4. API infrastructure

| Finding | Evidence | Verified | Implication |
|---|---|---|---|
| Homepage advertises "Lanka Data API", `api.lankadata.net/v1`, "100+ API Endpoints", "99.9% Availability", example `GET /companies?name=Dialog`, `GET /stock/JKH`, "Get API Key" and "Documentation" buttons | Homepage text | 🟡 claim | — |
| **`api.lankadata.net` does not resolve in DNS; `https://api.lankadata.net/v1/companies?name=Dialog` fails to connect** | `dig +short api.lankadata.net` empty; curl status 000 | ✅ | The advertised public API **did not exist/was not reachable** at audit time. Treat "100+ endpoints" and "99.9%" as unsupported. |
| `/documentation/`, `/api/` pages → 404; no OpenAPI/Swagger found; no `llms.txt` | HTTP 404s | ✅ (for the URLs tried) | No developer docs. A documented, versioned, keyless-read API is a clear opening. |
| **De facto API is `/legal-search.php?action={latest,search,chat,summarize}`** — undocumented, used by the front end, returns JSON, **`Access-Control-Allow-Origin: *`**, no key required for `latest` and `search` | Live responses and headers | ✅ | It works, but it is private-by-obscurity, unversioned, and capped (500 results). Note: not offered as a public API, so I would not build on or scrape it; the terms (below) also restrict commercial use. |
| Chat endpoint has rate limiting (`status: rate_limited`, HTTP 429) and sets a `lankadata_chat_token` cookie (HttpOnly, 1 year) | Front-end JS; `Set-Cookie` header | ✅ | Per-visitor throttling exists. |
| WordPress REST API is open (`/wp-json/`, namespaces include jetpack, wordfence, yoast, wp-statistics, site-kit, wp/v2); `/wp/v2/users` returns 401 | `/wp-json/` | ✅ | Standard WP exposure; users endpoint locked. Not a data API. |

## 5. Search and AI

- **Search:** server-side search over an indexed corpus with type filter and pagination; hard cap of top-500 matches. No facets for date/publisher/language visible in the code I read; ranking method unknown. ✅ (behaviour) / ❌ (internals).
- **AI:** RAG with "domain expert routing" and a "fine-tuned Chat2Find LLM", claimed trilingual (Sinhala/Tamil/English). 🟡 The base model, vendor, retrieval stack and evaluation are **not disclosed**. A "Chat2Find can make mistakes. Verify important legal or factual information." disclaimer appears on chat2find.com ✅.
- **Disclaimers:** the data policy says AI responses are informational and not professional advice, with no completeness/accuracy guarantee ✅ (`/data-policy/`).
- **Not tested:** answer quality, citation accuracy, hallucination rate, Sinhala/Tamil quality.
- **Implication:** no published benchmark for any of this. Publishing an evaluation set (e.g. questions answerable from CBSL/DCS tables with exact citations) would set Sri Lanka Facts apart on trust.

## 6. Geographic and mapping capabilities

- The page named **"Lanka Data Map"** (`/lanka-data-map/`) is **not a geographic map**: it is a conceptual diagram/description of "citizen-centric data infrastructure", OpenPIN and datasets. ✅ No tile layers, GeoJSON, iframes or map libraries found on it (no iframes; no map endpoint in its source). ✅
- No evidence of boundary data (district/DS division/GN), choropleths, or geocoded registries.
- **Implication:** geography is an open lane: district/DS-level indicators, boundary files, and map-based exploration are not offered here.

## 7. Technology stack (publicly identifiable)

- WordPress 7.1.4, theme `data-science-specialist` 1.3.3, plugins: Yoast SEO, Google Site Kit 1.191, Jetpack (+Boost, My Jetpack), Wordfence, WP Mail SMTP, WP Dark Mode 5.3.21, WP Statistics ✅ (HTML/REST namespaces).
- Apache web server ✅; PHP backend (`legal-search.php`) ✅; PDF.js 3.11.174 from cdnjs (client-side PDF text extraction used before chat) ✅.
- Nameservers `ns1/ns2.lankatax.net`, A record 184.94.215.151 ✅ — indicates a shared operator across LankaLaw/LankaTax-type properties (inference).
- Analytics: GA4 (`G-0P315G5CZ8`) and WP Statistics ✅.
- Search engine, database, LLM provider, vector store: **not identifiable**.
- **Implication:** it is a lightweight stack; data volume and API ambitions exceed what plain WordPress+PHP shows. No sign of a data warehouse or a modern API layer.

## 8. Open-source and GitHub

Covered in §3. Net: 2 public repos, created May 2026, README-level content; OpenPIN code not published ✅ (not found in the org). HF datasets licensed MIT in metadata but with a paid gated tier.

## 9. Business model, pricing, commercial services

- **Free web access** to search/registries. ✅
- **API:** "Get API Key" CTA but no pricing page found and no live API ✅/❌.
- **Paid data licence:** the Chat2Find instruction dataset is sold via a Stripe link ✅ (pricing not stated in the card text I read).
- **Chat2Find:** free guest tier (5 messages), then account sign-in "for unlimited chatting" ✅; an AIMart mobile app (Google Play) is said to host the expert models 🟡.
- **Contact:** Colombo address, email, phone listed on `/contact-us/` ✅. No named team or leadership found in the pages I read.
- **Implication:** monetisation is early-stage and AI-data centric. A public-interest, openly licensed alternative has room.

## 10. Licensing and redistribution

- Data policy: use allowed for "personal, academic, research, and non-commercial purposes"; attribution to "LankaData Network" required; **no reproduction, distribution, sale or derivatives for commercial purposes without written consent**; LDN claims IP in "databases, compilations … and the organisation and presentation of data", while carving out "underlying public-source materials". ✅ Source: `/data-policy/`.
- No machine-readable licence per dataset; no open-data licence (CC-BY/ODbL) on the site. ✅ (none found)
- Privacy policy (effective 1 Jan 2026) says they do not sell personal data ✅.
- **Implication:** don't copy or bulk-mirror LDN's compiled archive or AI summaries. Go to the original publishers. Open licensing (e.g. CC-BY for what Sri Lanka Facts produces) is itself a differentiator.

## 11. Limitations, gaps, weaknesses

1. **Advertised API not reachable**; no docs; no pricing (§4). ✅
2. **Inconsistent, unsubstantiated scale claims** (1B vs 10B vs 90k) (§3). ✅ that they conflict.
3. **No visible provenance/methodology/freshness per dataset**; AI summaries unlabelled in raw output. ✅/🟡
4. **Document-centric, not number-centric**: no charts, time series, indicator pages or downloadable tables seen. The homepage dashboard is a search UI. (Observed from the pages fetched; I did not click through every page.) ✅/🟡
5. **No real geographic layer** (§6). ✅
6. **Open-source claims thin**: placeholder repos, no OpenPIN code, "open source" label applied to a partly paid dataset (§3). ✅
7. **Undocumented endpoint with wildcard CORS** and 500-result cap. ✅
8. **Typos/polish** in public copy ("Infrastruture", "Havestor", "Infrastrcture") and an inconsistent URL structure (`/index.php/about-us/`, duplicate `/registries//`). ✅
9. **Conflict of roles:** the same org describes itself as neutral public-data infrastructure while feeding and being tied to a commercial chat product. 🟡 (inference from the repos/pages).
10. Not verified either way: update frequency beyond the latest-feed timestamps, uptime, accessibility, Sinhala/Tamil UI, answer accuracy.

## 12. Competitor assessment

| Dimension | LankaData | USAFacts (reference model) | Sri Lanka Facts opportunity |
|---|---|---|---|
| Core unit | Documents & registry records | Standardised statistics with narrative | Standardised indicators + stories |
| Provenance | Link-back, little metadata | Source cited per figure | Per-series provenance record |
| Open data | README-level repos, restrictive terms | Free to explore | Open licence + bulk download |
| API | Advertised, unreachable | — | Documented, versioned, keyless read |
| Geography | None (concept page) | State/county views | District/DS-level maps |
| AI | RAG chat, undisclosed models | — | Cited answers + public eval |
| Trust | Disclaimers, unverified counts | Editorial standards | Methodology and corrections log |

**Strengths to respect:** wide crawl of Sri Lankan government PDFs, near-daily freshness in the feed, registries with real utility, Sinhala/Tamil ambition, legal summaries.

## 13. Recommendations for differentiation

1. **Be number-first.** Build clean, harmonised time series (CBSL, DCS, Customs, Treasury, CSE) with definitions, units, revisions. LankaData indexes the PDF; you publish the table.
2. **Provenance on everything:** publisher, original URL, retrieval date, transform notes, licence, checksum. Show it on each chart.
3. **Open by default:** CC-BY (or equivalent) for derived data; CSV/Parquet + JSON manifest + versioned releases; keep attribution to the original publishers.
4. **Ship a real, documented API early** (OpenAPI spec, stable IDs, no key for reads, polite rate limits). Their advertised API is a gap you can fill in credibility alone.
5. **Geography:** district/DS division/GN boundaries, choropleths, per-area profiles. Nobody here does this.
6. **Trustworthy AI:** answers that quote the series and link the source cell/page; publish a small evaluation set and results; trilingual from the start; always label AI-generated text.
7. **Explain, not just list:** "what changed and why" stories on inflation, debt, trade, so non-experts benefit; LDN offers none visibly.
8. **Don't copy their archive or endpoints.** Their terms forbid commercial reuse and the endpoint is undocumented; go to the primary publishers directly and check each publisher's reuse terms.
9. **Consider partnering rather than competing** on legal/registry document search (cite, don't rebuild).

## Open questions worth a follow-up
- Re-test `api.lankadata.net` periodically; it may launch.
- Sample 20–30 AI answers across languages for accuracy.
- Check each registry's real record counts and update dates.
- Verify what the HF full-dataset licence costs and permits.
