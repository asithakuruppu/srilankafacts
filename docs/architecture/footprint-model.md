# Footprint model: every value has a where, a when and a what

Status: **proposed** · 2026-11-07 · Decision: D-018 in [decision-log.md](../decisions/decision-log.md) · Refines [multi-scale-features.md](multi-scale-features.md) §2 and [spatial-first-analytics.md](spatial-first-analytics.md) §3–4 · Related: [vector-space-model.md](vector-space-model.md), [data-model.md](data-model.md)

Legend: ✅ verified directly · 🟡 from secondary sources · ❓ assumption or estimate.

---

## 1. The lead's proposal

Every piece of data is stored as **a point coordinate plus a polygon around it that shows the resolution of the data**. That footprint, not a fixed grid, is the spatial model, and the multi-dimensional (vector) model uses it for better analytics.

## 2. Verdict

**I agree: point plus footprint should be the core representation, and it's better than making a grid the source of truth.** It keeps each value exactly as precise as it really is, no more and no less. A grid either throws detail away (a building squeezed into a 100 m cell) or invents it (a GN total spread over 100 m cells).

Three refinements make it work:

1. **Two different things look like "a polygon around a point". Keep them apart.**
   - **Area footprint:** the value describes the *whole* area. "This GN: 4,210 people" (illustrative number) is a total over the GN polygon, not a point somewhere inside it.
   - **Location uncertainty:** the value describes *one place*, but we only know roughly where. "A school, located to within 500 m" means the school is at one spot inside that circle.

   These need different maths. Area totals are summed or apportioned. Uncertain locations are handled as probabilities. Mixing them gives wrong answers, so every value records its **support type**.
2. **Use the real shape, not a circle.** A GN's footprint is the GN boundary. A WorldPop value's footprint is its 100 m square. A building's is its outline. Circles (or ellipses) are only for location uncertainty.
3. **Keep the grid, as an index rather than the truth.** To combine two datasets with different footprints you need a common basis anyway: intersect the shapes, or count shared cells. Intersecting millions of polygons for every question is slow. A grid makes it fast. Each footprint is therefore *also* stored as the set of ~100 m H3 cells it covers, with coverage fractions. Exact geometry is used where precision matters; the cell cover is used for speed.

So the model is **footprint-first, grid-indexed**. The atom is the **observation with its footprint**. The 100 m cell is the common index, not the atom.

---

## 3. The model

Every value, whatever its source, has:

| Field | Meaning | Example: census count | Example: WorldPop pixel | Example: geocoded school | Example: building |
|---|---|---|---|---|---|
| `point` | Representative point for indexing, labels and the `geo` space (guaranteed inside the footprint, not a centroid that might fall outside) | Point inside the GN | Pixel centre | Best-known location | Point inside the outline |
| `footprint` | The area the value is stated for | GN polygon (by reference to the spine) | 100 m square (implicit from the grid) | — | Building outline |
| `support_type` | How to read the footprint | `area_total` | `area_total` | `location_uncertain` | `object_extent` |
| `uncertainty` | For uncertain locations: radius or ellipse in metres | — | — | 500 m | — |
| `information_footprint` | Where the information really comes from (the "information floor") | Same GN | **The 2012 GN** the pixel was modelled from ✅ | — | — |
| `cell_cover` | H3 resolution 10 cells covered, with fractions | ~cells in the GN | 1–2 cells | Cells within the circle, weighted | 1–few cells |

Support types:

| `support_type` | Meaning | Combine by |
|---|---|---|
| `area_total` | A count or total over the whole footprint | Sum; apportion by weights; never "locate" it |
| `area_mean` | A rate, share, mean or density over the footprint | Recompute from components; area- or population-weighted means |
| `location_uncertain` | One place, position known within the footprint | Probability of falling in each cell or unit; flag ambiguous assignments |
| `object_extent` | A physical object occupying the footprint | Overlay; count, length, area |
| `field_sample` | A measurement at a point that represents its surroundings (a weather station, a water-quality sample) | Interpolate with stated method; never sum |

### 3.1 Time has a footprint too

Every value also has a **time footprint**, and the same logic applies. "Dengue cases in 2024" is a total over a year; "population on census night" is a snapshot; "rainfall on 15 July" is one day; "building seen in 2019 imagery" is roughly when it was observed.

| Field | Meaning | Examples |
|---|---|---|
| `period` | Label in our period format (unchanged) | `2024`, `2024-Q3`, `2024-07-15`, `2024/25-maha` |
| `time_start`, `time_end` | The interval the value covers | 2024-01-01 → 2024-12-31 |
| `time_support` | How to read it: `instant`, `interval_total` (cases in a year), `interval_mean` (average price in a month), `snapshot` (census reference date), `observed_around` (imagery date, uncertain) | |
| `time_uncertainty` | For `observed_around`: plus or minus days | Canopy map imagery "nominally 2018–2020" 🟡 → wide |
| `boundary_vintage` | Which version of the geography the value was published on | `2024`, `2012` |
| `release` and `published_at` | **When we knew it.** A value can be revised (provisional → final) without overwriting history | `v2027.03.1` |

Keeping both *when it was true* (`time_start`/`time_end`) and *when we knew it* (`release`) lets the platform answer "what did the official figure say on 1 March?", show revisions honestly, and reproduce any past chart exactly.

The combination rule from §6 applies to time as well: a result is only as fine as the **coarser time footprint** of its inputs. Annual cases divided by a census-night population is an annual figure on census-night denominators, and the label says so.

### 3.2 So every data point is a box in space, time and meaning

| Part | What | Fields |
|---|---|---|
| **Where** | Spatial footprint | `point`, `footprint`, `support_type`, `uncertainty`, `information_footprint`, `cell_cover` |
| **When** | Time footprint | `period`, `time_start`, `time_end`, `time_support`, `time_uncertainty`, `boundary_vintage` |
| **What** | Meaning dimensions | `indicator_id`, `breakdown` (sex, age, sector…), `unit` |
| **Value** | The number | `value`, `value_status`, uncertainty bounds |
| **How sure and from where** | Trust | `data_nature`, `verification`, dataset, snapshot hash, source locator, `release` |

In the vector spaces (D-016), where and when become dimensions alongside the indicator dimensions. Distance in space, time and profile are measured in different units, so they're never added together silently. A `composite` distance always states its weights, for example "1 km counts the same as one year counts the same as one standard deviation of profile".

### 3.3 Storage stays cheap

The model is conceptual. Footprints aren't copied onto every row:

- **Area data:** the footprint is a reference (`geography_id` + vintage). The geometry is stored once in the spine.
- **Grids:** the footprint is implicit in the cell or pixel ID. No polygons are materialised for millions of pixels.
- **Uncertain points:** point plus radius; the circle is implicit.
- **Features:** their own geometry, already stored.
- **Cell covers:** one table per footprint family (for example GN 2024 → cells), shared by every dataset on that geography.

---

## 4. What it does for analytics

### 4.1 Honest "what do we know here?"

Click anywhere in Sri Lanka and get **every value whose footprint covers that spot**, sorted from finest to coarsest: the building, the 100 m land-cover cell, the GN census figures, the DS, the district, each with its footprint shown on the map and its information floor stated. Users see at once how much is really known about a place, and at what resolution. I don't know of a public platform that does this ❓, and it follows directly from your model.

### 4.2 Resolution-aware combination

When two datasets meet, the result can only be as fine as the **coarser** footprint, and the platform can compute that automatically. "Dengue cases (MOH area) per 1,000 people (100 m grid)" is labelled at MOH resolution, because that's the coarser information.

### 4.3 Uncertainty that propagates

A school known only to within 2 km near a GN border is assigned to *both* GNs with probabilities, instead of being silently put in one. Counts of schools per GN become ranges where location is uncertain. This matters for facility lists geocoded from addresses, and for any survey that publishes displaced locations ❓.

### 4.4 Footprints in the vector spaces

Your instinct that footprints improve the multi-dimensional model is right. Concretely:

- **Scale becomes a dimension.** Each entity's vector can carry its footprint size (log area) and information-floor size. Similarity searches can then be restricted to entities of comparable scale. It makes no sense to call a 100 m cell "similar" to a whole district.
- **Distance between footprints, not just points.** Several measures are useful, and the platform should name which one it uses:
  - centroid distance (fast; fine for small footprints);
  - nearest-edge distance ("how close does this GN come to the coast?");
  - expected distance between random points in the two footprints (honest for large or uncertain footprints);
  - overlap (shared area as a share of each).
- **Comparisons at a common support.** Before computing profile similarity between places, all inputs are brought to the same footprint level. Otherwise a place with fine data looks artificially "different" from one with coarse data.

---

## 5. Point-with-radius versus grid, side by side

| | Point + footprint (recommended as truth) | Grid as truth |
|---|---|---|
| Keeps true precision | ✅ exactly | ❌ coarsens or invents |
| Handles any source (tables, rasters, points, objects) | ✅ | Only after conversion, with loss |
| Shows uncertainty | ✅ explicit | ❌ hidden in cell assignment |
| Fast joins and neighbours | ❌ polygon maths is slow at scale | ✅ |
| Simple in the browser | ❌ heavier geometry | ✅ IDs only |
| Stable across boundary changes | Needs crosswalks | ✅ cells never change |

The two columns are complementary, so use both: **footprints as the truth, cells as the index**. Every footprint gets a cell cover; fast queries run on cells; exact answers, labels and provenance come from footprints.

---

## 6. Rules

- Every value has a `support_type`. A value without one doesn't enter a release.
- Never treat an `area_total` as a point (for example, don't draw a GN's population as a dot at its centroid without saying so).
- Never assign an uncertain location to a single unit when its uncertainty overlaps a boundary. Use probabilities, or flag it.
- Combined results take the **coarser** footprint and information floor of their inputs.
- People's statistics never get a footprint smaller than the cell (D-017).
- Every value has a time footprint (`time_start`, `time_end`, `time_support`). Revisions create a new release row; they never overwrite.

---

## 7. Staging

| Stage | Footprint work |
|---|---|
| 0 | `support_type`, footprint and time-footprint fields in catalogue and observation schemas (F02); representative points with the spine (G01) |
| 1 | Census values as `area_total` / `area_mean` on GN footprints; "information floor" shown on every value |
| 2 | Cell covers for every footprint family (G07); "what do we know here?" point query; resolution-aware combination |
| 3 | Uncertain locations for geocoded facilities and events; footprint-aware distances and scale dimensions in the vector spaces |

---

## 8. Dimension catalogue: what else every data point can carry

*Added 2026-11-07 in answer to "what other dimensions can we add?"*

Dimensions come in two kinds, and keeping them apart matters:

- **Facets** describe the data point itself: what it is, how it was made, how far to trust it. They're mostly metadata, cheap to add, and they make comparisons valid.
- **Context dimensions** describe the *place and time* the footprint covers: terrain, climate, hazards, access, who governs it. They're derived from other layers by overlaying the footprint, and they become coordinates in the vector spaces.

### 8.1 Facets of every data point

| Dimension | Question it answers | Examples | Why it matters | Stage |
|---|---|---|---|---|
| Where, when, what | (§3) | | | 0 |
| **Universe** (unit of observation) | Who or what is counted? | persons, households, occupied housing units, establishments, hectares, vehicles; "persons aged 15+" | Stops invalid comparisons (households vs persons) and wrong denominators | 0 |
| **Breakdown dimensions** | For which group? | sex, age band, residential sector (urban / rural / estate, the DCS classification 🟡), education, employment status, disability | The "who" inside a place. Ethnicity and religion are sensitive (see below) | 1 |
| **Collection method** | How was it gathered? | full enumeration, administrative register, sample survey (with sample size), satellite observation, model, crowd-mapped | Explains different numbers for the same thing | 0 |
| **Definition and classification version** | Which definition? | industry and occupation classification versions; changed poverty lines; changed boundaries | Decides whether a time series is comparable | 1 |
| **Comparability** | Comparable with what? | `comparable_with: [series…]`, breaks marked | Prevents false trends across definition changes | 1 |
| **Coverage of the universe** | How much of it was covered? | "OSM buildings ≈ 60% complete here" (illustrative); areas excluded from a survey | Missing ≠ zero | 1 |
| **Uncertainty** | How precise? | confidence interval, standard error, model error | Rankings and differences that aren't real | 1 |
| **Scale** | How big is the footprint and the information floor? | log area of the footprint and of the information floor | Compare like with like in vector spaces (§4.4) | 1 |
| **Vertical (z)** | How high or deep? | elevation, building height and floors, canopy height, flood depth | Sri Lanka's terrain matters (hill country, coast); buildings and trees are 3D | 3 |
| **Freshness and revision** | How old, and has it changed? | age of reference period, expected next update, provisional / final / revised | Users know when data is stale | 1 |
| **Sensitivity class** | How carefully must it be shown? | `public`, `sensitive_group` (ethnicity, religion), `small_cell` | Drives display rules, exclusion from default vectors (D-015), suppression | 0 |
| **Rights class** | What may be done with it? | CC BY, ODbL, non-commercial, unclear | Filters what can go into commercial work (AGENTS rule 4) | 0 |

### 8.2 Context dimensions for every footprint

Computed by overlaying each footprint (GN, cell, building) with other layers. Each becomes a block in the vector spaces and a filter in the explorer.

| Family | Example dimensions | Likely sources (to verify in R01/R02) | Stage |
|---|---|---|---|
| **Terrain** | elevation, slope, aspect, distance to coast | Copernicus DEM / SRTM 🟡; coastline from OSM | 2 |
| **Climate** | climatic zone (wet / intermediate / dry 🟡), rainfall normals, temperature, monsoon exposure | Department of Meteorology ❓; global climate grids ❓ | 2–3 |
| **Land and environment** | land cover shares, canopy cover, built-up share, water bodies, protected areas | ESA WorldCover 🟡; canopy map 🟡; protected-area data ❓ | 2 |
| **Hazards** | flood, landslide, drought, tsunami and coastal-erosion exposure | NBRO landslide hazard maps 🟡 (rights ❓); Disaster Management Centre ❓; global flood models ❓ | 3 |
| **Access** | travel time to nearest town, hospital, school, bank, bus or rail stop; road density | OSM roads; facility lists ❓ | 3 |
| **Jurisdiction** | every authority the footprint falls under: DS, GN, local authority, MOH, police, education zone, electorate, irrigation or Mahaweli system, plantation estate | the spine and non-admin schemes (G05) | 2 |
| **Built fabric** | building density, footprint sizes, building heights, landmarks by type | feature layer (G08) | 2 |
| **People profile** | the census profile vector of the containing GN (for cells and features, labelled as the GN's) | Census 2024 | 1 |
| **Neighbourhood** | the same dimensions averaged over neighbours (spatial lag) | derived | 1–2 |
| **Change** | rate of change and acceleration over time for any dimension | derived from time footprints | 2 |

### 8.3 Two new shapes of data worth planning for

- **Flows (two footprints per value).** Some data is about *between* places: migration (place of birth or previous residence → current residence, if published ❓), commuting, goods, remittances, phone or bus movements. A flow value has an **origin footprint and a destination footprint**. This is a genuine extension of the model, and flows are naturally vectors (direction and magnitude). Plan the schema now (`origin_ref`, `destination_ref`); ingest when a source appears.
- **Events (instant footprints).** Disasters, accidents, disease cases, elections. They're points or areas with an `instant` or short-interval time footprint, which makes "where and when did things cluster?" a space-time question.

### 8.4 Calendar dimensions for time

Time isn't only a number line in Sri Lanka. Useful calendar dimensions include agricultural seasons (Maha and Yala, already in our period format), monsoon periods, school terms, public holidays including Poya days, and festival periods. They let users ask "is this a seasonal pattern?" Sources: official calendars ❓.

### 8.5 How many dimensions is too many?

More dimensions don't automatically give better analytics. Each one adds collection and upkeep cost, and in the vector spaces many correlated dimensions blur distances (see [vector-space-model.md §3](vector-space-model.md#3-why-one-undifferentiated-space-doesnt-work)). Every dimension must pass the same admission test as feature layers: a clear question, a source with clear rights, measured quality and an update path. Vector spaces use **blocks** of dimensions with equal weight by default, so adding dimensions to one block doesn't drown out the others.

**Recommended order:**
1. **Stage 0–1, cheap and high-trust:** universe, collection method, sensitivity class, rights class, freshness and revision, uncertainty, residential sector breakdown.
2. **Stage 2, context:** terrain, land and environment, jurisdiction, built fabric, neighbourhood, change.
3. **Stage 3:** hazards, access, climate, vertical (z), flows.
