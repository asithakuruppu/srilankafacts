# Organisation, business model and partnerships

Status: **recommendation** · 2026-11-07 · Builds on brainstorm §11, §13 and §17 · Legend: ✅ verified · 🟡 secondary · ❓ assumption

---

## 1. Recommendation in brief

- **Model:** a *services-funded open platform*. The public platform is free and openly licensed. Revenue in years 1–2 comes from **commissioned analysis, GIS and data work** that uses the same spine and pipeline. Products (API service levels, tools, data packages) follow once repeat demand is proven.
- **Entity:** start with **one small legal entity** suited to taking paid work (a sole proprietorship or private limited company, decided with a Sri Lankan lawyer ❓). Publish the governance principles now. Revisit a non-profit arm only when grant funding or partnerships require it.
- **Brand:** one brand, "Sri Lanka Facts" (subject to name checks). Drop the four sub-brands until there are teams behind them.
- **Licence:** CC BY 4.0 for what we produce (where inputs allow), ODbL for OSM-derived databases, open-source code (Apache-2.0). Don't sell the data itself. Sell convenience, analysis, guarantees and expertise.

---

## 2. Why not the freemium-subscription model (for now)

The brainstorm's tiers (Public / Professional / Enterprise) are sensible in shape, but:

1. **The market for individual data subscriptions in Sri Lanka is probably small** ❓. Prices that work in USD markets are steep locally, and free alternatives exist for national data (CBSL, Advocata, World Bank).
2. **Subscriptions need features you can't build yet**: accounts, billing, saved views, quotas, support. That is months of work before the first rupee.
3. **Services earn money sooner and teach you what to productise.** Every commissioned analysis tells you what customers will pay for.
4. **Open data plus paid services is a proven pattern**, used for example by social businesses in development data, such as the one behind Nepal in Data 🟡.

Keep the Professional and Enterprise tiers as a **Stage 4 hypothesis**, to be validated by what clients actually ask for.

---

## 3. Revenue ladder

| Rung | Offer | Who pays | Starts | Built on |
|---|---|---|---|---|
| 1 | **Commissioned analysis and maps:** district or DS profiles for proposals, programme targeting, baseline reports | NGOs, development agencies, researchers | Stage 1 | Spine + census |
| 2 | **Sampling frames:** GN-level frames with population and households, stratified urban/rural/estate, PPS selection, maps for field teams | Market research firms, NGOs, academic survey teams | Stage 1–2 | GN census + spine |
| 3 | **Catchment and market sizing:** population and households within X km or Y minutes of a site; competitor and site screening | Retail, FMCG, banks, microfinance, insurers | Stage 2 | Spine + OSM roads |
| 4 | **Training and workshops:** using Sri Lankan public data, maps and QGIS for newsrooms, universities, NGOs | Media organisations, universities, NGOs | Stage 2 | Platform as teaching tool |
| 5 | **Resolver / data API with SLA:** coordinates or address → GN/DS/LA/MOH/PD IDs, profiles, bulk lookups | Fintech (KYC), logistics, delivery, apps | Stage 3–4 | Spine + dynamic API |
| 6 | **Custom dashboards / white-label embeds** | Organisations wanting maps of their own data on our spine | Stage 4 | Map shell |
| 7 | **Grants and sponsorship** of specific public datasets (disclosed) | Foundations, development partners, CSR | When there is a track record | Public platform |

**Never:** advertising, selling personal data, paywalling basic public statistics, selling favourable rankings or changes to public findings.

**Pricing:** no prices are set here. Discover willingness to pay through 8–10 conversations in Stage 1 (prompt R05) and one paid pilot in Stage 2. Price projects by scope rather than by the hour once you know your delivery time.

---

## 4. Managing the public/commercial tension

The brainstorm's governance principles (§11) are good and should be published on day one, almost unchanged:

- No political party ownership or editorial control.
- No sale of favourable rankings or manipulated statistics.
- Every published figure has a traceable source.
- Commercial customers cannot buy changes to public findings.
- Corrections are documented publicly.
- Methodologies are open to independent scrutiny.
- Sponsored research is disclosed, and funders do not control findings.

**Operational rules to add:**
- Commissioned work uses only data whose rights allow it (`commercial_reuse: yes`).
- If commissioned work finds an error in public data, the fix goes to the public platform for everyone.
- Clients may keep their analysis private. They can never make public data private.
- A public "funding and clients" page lists funders and categories of clients, with names where clients consent.

---

## 5. Licensing strategy

| What | Licence | Reason |
|---|---|---|
| Our text, charts, explainers | CC BY 4.0 | Maximise reuse and citation |
| Our derived tables (where source rights allow) | CC BY 4.0 + source attribution | Contrast with LDF (non-commercial ✅) and LankaData (restrictive ✅) |
| OSM-derived databases (roads, POIs) | ODbL | Required by share-alike ✅ |
| Third-party data with unclear rights | Not redistributed; displayed with attribution and a link where permitted | Respect rights |
| Code (pipeline, web) | Apache-2.0 | Credibility, contributions, eligibility as a Digital Public Good ❓ |

**Isn't open licensing giving away the moat?** No. The moat is the *maintained, verified* spine, the speed of updates, the trust and the expertise. A copy goes stale; the service doesn't. Open licensing is also what makes newsrooms, researchers and AI assistants cite you.

---

## 6. Partnerships

### 6.1 Ecosystem (low cost, start in Stage 0)

| Partner | What we offer | What we ask |
|---|---|---|
| **Nuwan Senaratna (nuuuwan)** | Credit; bug reports; a place where his data becomes mapped and explained; possibly paid work | Permission and coordination for reuse; provenance of MOH/LG geometries |
| **Lanka Data Foundation** | Geography and indicators they don't do; links to their structure/archive products | Division of labour; linking; possibly shared RTI efforts |
| **Lanka Data Layer** | Bug reports with evidence (Ampara), validation results | Coordination; possible convergence on IDs |
| **Verité Research** | Place-based maps for their public-finance work | Links, shared methods for public finance by place |
| **Academics** (Dengue Atlas team, university geography and statistics departments) | Clean data, denominators, a publishing platform | Methods review, student projects, MOH geography |
| **Newsrooms** | Embeds, data support, training | Citations, feedback, distribution |

### 6.2 Institutions (staged)

1. **Stage 0:** narrow, answerable asks. DCS: reuse terms for published census tables. Survey Department/NSDI: boundary currency and terms.
2. **Stage 1–2:** demonstrate value. Share the QA findings (for example boundary inconsistencies) privately first, framed as help.
3. **Stage 2–3:** propose an **errata channel** and machine-readable feeds for specific tables.
4. **Stage 3+:** MoUs, co-branded releases, data-sharing agreements.

**RTI:** use it for specific, well-scoped data (for example GN lists per local authority or MOH area). Coordinate with LDF's RTI Tracker ✅ to avoid duplication, and publish request outcomes.

---

## 7. Legal and administrative checklist

| Item | Why | When |
|---|---|---|
| Business registration / company formation | To invoice clients | Before the first paid work |
| Name and trademark search (NIPO Sri Lanka), domain purchase | `srilankafacts.com` is parked with a domain-sales service ✅; `.org/.net/.lk` show no DNS ✅ (not proof of availability). "Sri Lanka Facts" is descriptive and may be hard to protect ❓ | Stage 0 |
| Data-rights opinion for DCS census tables, COD-AB, NSDI | The flagship depends on it | Stage 0–1 |
| Terms of use, privacy policy, cookie-free analytics | PDPA core provisions from 1 Jan 2027 🟡 | Before public beta |
| Online Safety Act status check | Publishing on sensitive topics; amendment or repeal pending 🟡 | Before public beta |
| OSM attribution and ODbL compliance | Basemap and derived layers | Stage 1 |
| Detailed-map publication rules | Whether publishing building-level and other detailed maps in Sri Lanka needs Survey Department approval ❓; handling of sensitive sites (D-017) | Before Stage 2 feature layers |
| Terms of free feeds | Many free APIs (weather, flights) forbid commercial use; the services model is commercial (D-020) | Before Stage 3 feeds |
| ODbL status of aggregates | Whether counts derived from OSM features (for example buildings per GN) are a derivative database ❓ | Before Stage 2 feature layers |
| Contracts template for commissioned work (IP, data rights, publication) | Protect the public/commercial firewall | Before the first paid work |
| Tax registration | Revenue | With registration |

---

## 8. If you later add a non-profit arm

Consider it when **(a)** a grant requires it, **(b)** an institutional partner prefers it, or **(c)** public-good work clearly exceeds what services can fund. Options to discuss with a lawyer ❓: a company limited by guarantee, a trust, or partnering with an existing non-profit as fiscal host. Until then, the governance principles plus a transparent funding page give most of the trust benefit without the overhead.
