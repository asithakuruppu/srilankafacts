# Live data, movement, events, elections and conflicting sources

Status: **proposed** · 2026-11-07 · Decisions: D-019, D-020 in [decision-log.md](../decisions/decision-log.md) · Builds on [footprint-model.md](footprint-model.md) · Ideas: OPP-07, OPP-41 to OPP-52 in [opportunities-register.md](../ideas/opportunities-register.md)

Legend: ✅ verified directly · 🟡 from secondary sources or vendor documentation not checked in detail · ❓ assumption or estimate · ❌ not found.

---

## 1. Summary

All five of the lead's additions fit the footprint model (where × when × what). Two of them are core and should come early. The rest are later layers.

| Addition | Fit | Verdict | When |
|---|---|---|---|
| **Comparing conflicting sources** | A core rule of the data model, not a feature | **Do now** (D-019) | Stage 0 schema, Stage 1 UI |
| **Election results** | Polling-division footprint, event-like time footprint | Yes, high interest; neutral presentation essential | Stage 2 |
| **Live and historical feeds (weather and more)** | Time series on cells and stations | Yes, as a separate stage, "scheduled near-real-time" not streaming (D-020) | Stage 3 |
| **Movement (traffic, bus, train, aircraft)** | Moving points with uncertain positions | Partly: estimated train positions from timetables and aircraft from open feeds are feasible; buses and road traffic mostly aren't free | Stage 4 |
| **News geotagging** | Event points with text-derived places | Yes, reuse GDELT first; build a Sri Lankan layer only if it adds value | Stage 3 experiment |
| **Social media "vibe" and mood** | Location-tagged opinion | **Park.** Data access is expensive or closed, geotags are rare, and mood maps by place carry real risks in Sri Lanka | Research only, after an ethics review |

---

## 2. Comparing multiple conflicting sources (core, D-019)

Sri Lanka has many cases where sources disagree: DS division counts (331, 332, 339, 340), GN counts, population estimates, boundaries. Today most platforms quietly pick one. The footprint model makes disagreement **visible and measurable** instead.

**Model: every value is a claim.**
- Each observation is a **claim** by one source about one footprint, time footprint and indicator. Several claims can coexist for the same box.
- A **preferred claim** may be marked for default display, with a written reason (for example "official final census figure"). The others stay visible.
- **Disagreement is a dimension:** spread (max − min), relative spread, number of sources, and whether the claims overlap within their stated uncertainty.
- Reconciliation, when possible, is a documented override (D03), never a silent edit.

**What users see:**
- A "sources disagree" badge on any value where claims differ beyond tolerance.
- A side-by-side panel: each source's value, footprint, time footprint, method, date and licence.
- A "disagreement map": where sources diverge most, which is often where the data is weakest.

**In vector terms:** the distance between two sources' versions of the same place is a measure of disagreement, and a "source-agreement space" can show which sources usually agree with which.

This also turns the platform's biggest weakness (messy official data) into a feature: **a transparent referee**, consistent with the neutral, non-accusatory tone of the errata idea (OPP-15).

---

## 3. Election results

- **Footprint:** polling division (160) and electoral district (22) ✅ (unit counts from the landscape doc); local authority wards for local elections ❓. Postal votes are reported per electoral district rather than per polling division 🟡. Their footprint is the electoral district, never pushed down.
- **Time footprint:** `snapshot` on election day; series across presidential, parliamentary, provincial and local elections.
- **What:** registered electors, votes cast, valid and rejected votes, votes per party or candidate, turnout.
- **Sources:** the Election Commission (primary); nuuuwan's `elections-lk-nuuuwan` package, which describes its data as sourced from the Election Commission and DCS 🟡 (cross-check, licence to confirm).
- **Joins:** polling divisions don't nest in DS divisions. Linking results to census profiles goes through GN composition with weights (D-004, G05). This lets users compare results with places' profiles, which is powerful and sensitive.
- **Rules:** strictly neutral presentation (AGENTS rule 12); no party-favourable colour choices; no inference about how individuals or groups voted (ecological fallacy, labelled); polling-division boundaries need clear provenance first (R01/R02).

---

## 4. Live and historical feeds (Stage 3, D-020)

### 4.1 Architecture: scheduled, not streaming

Most useful Sri Lankan feeds update hourly, daily or weekly. That doesn't need a streaming server:

- **Historical archives** are ingested once and extended on a schedule.
- **"Live" feeds** run as scheduled jobs (every 15–60 minutes for weather, daily for others) that write new time slices as static files, plus a small "latest" file per feed.
- The release model (D-003) gains a **rolling partition** for fast-changing feeds: immutable daily partitions, with the current day mutable until closed. Provenance is per fetch, as now.
- **True streaming** (positions every few seconds) is deferred to Stage 4 and needs a small server. It's the first real break from static-first, so it waits for clear demand.

### 4.2 Candidate free feeds (to check one by one with R01/R02)

| Domain | Candidate sources | Terms as far as known | Footprint |
|---|---|---|---|
| Weather (forecast and recent) | Open-Meteo | Data CC BY 4.0, but the **free API is for non-commercial use**; commercial use needs a subscription 🟡 | cell |
| Weather (historical) | ERA5 reanalysis (Copernicus) | Copernicus licence, commercial use allowed with attribution 🟡 | ~30 km cells |
| Rainfall | CHIRPS; GPM IMERG | free 🟡 | ~5–10 km cells |
| Official observations | Department of Meteorology | access and terms ❓ | stations |
| Air quality | OpenAQ; low-cost sensor networks | ❓ | stations |
| Fires and hotspots | NASA FIRMS | free 🟡 | points |
| Floods | GloFAS; DMC situation reports (nuuuwan scrapes DMC reports ✅ per landscape doc) | ❓ | rivers, DS |
| Reservoir and river levels | Irrigation Department (nuuuwan has an irrigation repository ✅ per landscape doc) | ❓ | points |
| Disease | Epidemiology Unit weekly reports (dengue and other notifiable diseases) | ❓ | district, MOH |
| Prices | HARTI daily food commodity prices ❓; DCS price indices; fuel price notices | ❓ | markets, national |
| Night lights | VIIRS monthly | free 🟡 | ~500 m cells |
| Land change alerts | forest-loss alert products ❓ | ❓ | cells |

"Free of charge" isn't the same as "free to reuse": several free APIs restrict commercial use. Every feed needs a rights entry before it enters a release (AGENTS rule 4), and the business model (services) counts as commercial.

---

## 5. Movement: traffic, buses, trains, aircraft (Stage 4)

Moving things fit the model as **points with a time footprint of an instant and a `location_uncertain` footprint**. The radius is small for GPS positions and large for estimates, so real and estimated positions sit in the same model, clearly labelled.

| Mode | What seems feasible | Status |
|---|---|---|
| **Trains** | Estimated positions interpolated from published timetables, as an existing third-party tracker already does ("timetable interpolation", delays not reflected 🟡). Official timetables are on railway.gov.lk 🟡; no official GTFS feed found ❌ | Feasible as **estimates**; label "scheduled position, not live" |
| **Buses** | A developer reports a GTFS and GTFS-Realtime pipeline built from Colombo's LMT-Go system 🟡 (self-reported; authorisation unclear). No national bus GTFS found ❌ | Explore a partnership; don't scrape without permission |
| **Aircraft** | OpenSky Network: free for research and non-commercial use; commercial use requires contacting OpenSky 🟡 | Feasible for a public non-commercial layer; check terms |
| **Road traffic** | Commercial providers (paid); municipal partner programmes ❓ | Not free. Could be estimated from road class and time of day, but such estimates are weak and should be labelled heavily |
| **Ships** | AIS data is mostly paid; community exchanges exist ❓ | Later, if ever |

Estimated positions are `modelled_estimate` with a wide uncertainty radius. A real position from a live feed is `observed` with a GPS-scale radius. The UI shows the difference.

---

## 6. News geotagging and social "vibe"

### 6.1 News (Stage 3 experiment)

- **Reuse first:** GDELT is free for any use including commercial, with citation and link 🟡, and georeferences events to city level, with tone scores 🟡. Pull Sri Lanka records and test their geocoding quality against our gazetteer before building anything.
- **Then, if valuable:** a Sri Lankan news layer from RSS feeds, with places extracted by a gazetteer-backed parser (our trilingual names are a real advantage here). Store only headline, link, date, outlet and extracted places and topics, **not full article text** (copyright).
- **Uses:** "what's being reported about this place?", event timelines per district, linking news to data ("flooding reported here; rainfall here was X").
- **Footprint honesty:** a place mentioned in an article isn't necessarily where the event happened. Location confidence is recorded.

### 6.2 Social media mood: park it, for four reasons

1. **Access:** X now charges per read for new developers, with no free read tier reported 🟡; Meta closed CrowdTangle in 2024 🟡 and offers research-only access ❓. Free, lawful, bulk access essentially isn't available.
2. **Location:** very few posts carry precise geotags ❓, so "mood by GN" would mostly be guesswork, given false precision by a map.
3. **Bias:** social users aren't representative, especially across age, language and region.
4. **Harm:** maps of "mood" or "anger" by place, in a country with a history of communal violence, can be misused, and could raise issues under the Online Safety Act 🟡 (status to check, see legal checklist).

If it's ever revisited: aggregate national or district-level signals only, from data obtained lawfully, after an ethics review, never at small-area level.

---

## 7. Other possibilities

Filtered for public value, feasibility and fit with the footprint model:

| Idea | What | Why interesting |
|---|---|---|
| **Gazette geotagging** | Places mentioned in government gazettes (land acquisitions, appointments, new administrative units) | Uses LDF's archive (licence permitting) and our gazetteer; links decisions to places |
| **Public projects and procurement by place** | Where public money is going | Accountability; partner with Verité |
| **"What changed here?" alerts** | Notify users when any data for their GN or DS changes | Retention; easy with releases |
| **Place timelines** | One timeline per place: census, elections, disasters, news, projects | The footprint model makes this nearly free |
| **Scenario layers** | "If sea level rises X", "if this road is built": what's exposed | Strong for planners; modelled, labelled |
| **Mobile coverage** | Cell tower locations from open community data ❓ | Digital-divide analysis |
| **Tourism footprint** | Arrivals, hotels, attractions by area | Commercial interest |
| **School and health facility profiles** | Every facility as a feature with its context | Planning, NGOs |
| **Historical maps** | Georeferenced old survey maps for change over a century | Unique cultural value; partner with Survey Dept |
| **Data-quality index by place** | How much is known, how fresh, how much sources agree | Shows where data investment is needed |
| **AI place briefings** | A cited, generated summary per place from the ledger only | Accessibility; strict citation rules (D-011) |

---

## 8. Recommended order

See [development-strategy.md](../roadmap/development-strategy.md) for the full staging. In short:

1. **Stage 0 (now):** decisions; repository; schemas including footprint, time footprint and **claims** (D-019); geography spine and crosswalk; rights letters.
2. **Stage 1:** Census Atlas 2024 with spatial context and profile vectors; the "sources disagree" panel for unit counts and census totals.
3. **Stage 2:** every geography over time: non-admin geographies, **elections**, 2012↔2024 comparison, feature layer v1, cell covers, "what do we know here?".
4. **Stage 3, "Living Sri Lanka":** scheduled feeds: weather history and forecast, rainfall, disasters, disease, reservoirs, prices, night lights; events layer; GDELT news experiment; place timelines.
5. **Stage 4, "Movement":** estimated train positions, aircraft, bus partnerships; the first streaming component.
6. **Research track:** social media signals only after an ethics review and lawful access.

---

## Sources

- [OpenSky API documentation](https://openskynetwork.github.io/opensky-api)
- [Open-Meteo](https://open-meteo.com/)
- [X API pricing overview (third party, 2026)](https://wearefounders.uk/post/the-x-api-price-hike-a-blow-to-indie-hackers)
- [Train tracking based on timetable interpolation (third party)](https://trainstracking.com/sri-lanka/live)
- [Sri Lanka Railways](https://www.railway.gov.lk/web/index.php)
- [GDELT on BigQuery (free access)](https://www.sitepoint.com/googles-bigquery-provides-free-access-gdelt/)
- [GDELT dataset description](https://baselight.app/u/gdelt/dataset/events_v2)
- [elections-lk-nuuuwan package](https://libraries.io/pypi/elections-lk-nuuuwan)
