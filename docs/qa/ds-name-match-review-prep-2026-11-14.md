# DS name-match review: preparation for the lead (2026-11-14)

**Status: preparation only. Nothing was decided or changed.** No match file, spine file, crosswalk or override was edited. Every recommendation below is an **agent recommendation** (AI-generated analysis, not a lead decision). One row per item is in [`ds-name-match-review-prep-2026-11-14.csv`](ds-name-match-review-prep-2026-11-14.csv); it has empty `lead_decision` and `lead_note` columns to fill in.

Tags: ✅ verified by me (recomputed or read) · 🟡 claimed by a source or a file, not independently checked · ❌ not found · ❓ assumption.

## 1. What is being reviewed

The DCS Census 2024 A-series tables (A6/A7 population, ethnicity and religion; A9–A12 housing structure and materials) list DS divisions **by name only, with no DS code**. The pipeline joins each name to a DCS DS code through two reviewed match files, never by name at build time, and each match must pass a numeric check (the DS total equals the GN sum for that DCS DS code):

- `catalog/geographies/name-matches/dcs-census2024-a-series-ds.csv` (A9–A12, D-032 step c)
- `catalog/geographies/name-matches/dcs-census2024-population-a-series-ds.csv` (A6/A7, D-032 step d)

Both have 340 rows and are marked `agent …; lead review pending`. The DCS DS code is then joined to a spine unit through the code crosswalk `catalog/geographies/codes/dcs-census2024.csv` (G02; DS level: 326 exact code, 12 name and parent, 1 manual, 1 unmatched). So a DS value reaches a place by two steps, and the lead's review covers both:

> table label → DCS DS code (name-match files) → spine ID (crosswalk)

The 340 rows are the same 340 DS in both files. They differ in one label only (A6/A7 "Padavisripura" vs A9–A12 "Padavisiripura", both → DCS 5303) ✅.

This is separate from the **GN** review queue (41 unmatched DCS GNs; [dating analysis](../research/geography/dcs-review-items-dating.md)). 13 DS have different GN counts in DCS and the spine; those are GN-level facts and are not re-opened here (column `gn_count_differs` in the CSV).

## 2. Summary: what needs the lead

| Group | Items | Persons (A6) | What it is | Recommendation |
|---|---:|---:|---|---|
| **A0** clean | 283 | 19,157,561 | Label = DCS name; same code in DCS and spine; spine name agrees | **Bulk approve** (high) |
| **A1** spine spelling differs | 25 | 973,843 | Label = DCS name; same code; spine spells it a little differently or drops a bracketed name | **Bulk approve** (high) |
| **A2** spine name is a shorter form | 3 | 269,899 | Label = DCS name; same code; spine name contains or is contained by it | **Bulk approve after a glance** (medium-high) |
| **B** spelling variants of the label | 15 | 586,117 | Label ≠ DCS name, matched by unique total | **Approve** (high) |
| **C** DCS code differs from spine code | 12 | 710,026 | Same name and district, different code; must never be joined by code | **Approve** (high; 2 Eravur units medium-high) |
| **D** already decided | 1 | 31,556 | DCS 5221 Kalmunai North Sub → `LK-ADM3-P0001` (lead, 2026-11-08, D-022) | Nothing to do |
| **H** hard case | 1 | 52,798 | DCS 5224 Kalmunai has no spine unit | **Lead decision** (§6) |
| Total | 340 | 21,781,800 | | |

Persons total 21,781,800 equals the national population in the Census 2024 QA reports ✅. So **338 of 340 items are recommended for approval** (311 in bulk: groups A0, A1, A2; 27 after a look at §4: groups B and C), **1 was already decided by you** (DCS 5221) and **1 needs a real decision** (DCS 5224). The tables in §3 to §6 are the evidence; the CSV carries it for every row.

## 3. What I checked, and how much it proves

For all 340 rows I recomputed, from the held snapshots and the local build (no network):

| Check | Result |
|---|---|
| A6 total (as recorded in the match file) equals the sum of DCS GN population for that DCS DS code (`GN_population.xlsx`) | 340 of 340 ✅ |
| That total equals `population_total` in the Census 2024 build at the mapped spine unit | 339 of 339 mapped ✅ (DS 5224 has no unit) |
| A9 housing-unit total equals `occupied_housing_units` at the mapped spine unit | 339 of 339 ✅ |
| Within a district, no two DS share the same A6 total or the same A9 total (so "the only DS with that total" is a real discriminator) | 0 duplicates ✅ |
| **GN-name test (independent of DS names):** the DCS GN names of a DS compared with the names of the GN children of the crosswalked spine unit; and the crosswalked unit compared with every other spine DS in the same district | In all 338 mapped DS (excluding the two Kalmunai rows) the crosswalked unit is also the best GN-name match in its district (a tie only for DCS 5221, which is the provisional unit). Coverage ranges from 0.67 to 1.00, median 1.00 ✅ |
| Source cells: I used the A6 and A9 totals as printed in the `evidence` column of the match files; I did **not** reopen the A6 or A9 sheets | 🟡 |

What this proves, and what it does not. The total check proves that the *label → DCS code* step picked the DS whose GNs sum to that table line ✅. It cannot prove the *DCS code → spine* step: the build computes the DS value from DCS GN rows by DCS code, so the value matches by construction. That second step is tested by the GN-name check, which is independent. Neither check judges whether DCS's own naming is right (❓ DCS is treated as the authority for its own tables).

Scripts were one-off (as for the dating analysis) and are not part of `slf`; they are copied to the shared notes folder of this session group for anyone who wants to rerun them.

## 4. Groups B and C: approve with a glance

### Group B: 15 spelling variants of the label

Each is the only DS in its district with the same A6 and A9 total, and in every case the DCS name is the best-matching leftover name (similarity 0.92–1.00; the next best 0.29–0.68, in the same district) ✅. Two more variants (Thalawakele, Kalthota) are in group C because their codes also differ.

| Item | District | Label in tables | DCS name | DCS code | Spine ID | Spine name | Persons (A6) | Spelling difference |
|---|---|---|---|---|---|---|---|---|
| DS-312 | Kandy | Delthota | Deltota | 2148 | LK2148 | Deltota | 31,904 | label Delthota vs DCS Deltota: "th" vs "t". |
| DS-313 | Nuwara Eliya | Ambagamuwa | Ambagamuwa Koralaya | 2315 | LK2315 | Ambagamuwa Korale | 42,538 | label "Ambagamuwa" is DCS "Ambagamuwa Koralaya" without the "Koralaya" suffix (a korale is a traditional division); spine "Ambagamuwa Korale". |
| DS-314 | Galle | Benthota | Bentota | 3103 | LK3103 | Bentota | 49,650 | label Benthota vs DCS Bentota: extra "h". |
| DS-315 | Matara | Weligam | Weligama | 3239 | LK3239 | Weligama | 76,136 | label Weligam vs DCS Weligama: final "a" missing (likely a truncated label). |
| DS-316 | Hambantota | Lunugamwehera | Lunugamvehera | 3306 | LK3306 | Lunugamwehera | 36,923 | label Lunugamwehera vs DCS Lunugamvehera: "w" vs "v". Spine uses the "w" spelling. |
| DS-317 | Jaffna | Valikamam North | Valikamam North (Tellipallai) | 4112 | LK4112 | Valikamam North (Thllippalai) | 44,914 | label omits the bracketed alternative name "(Tellipallai)"; spine has "(Thllippalai)". |
| DS-318 | Jaffna | Vadamaradchy South-West (Karaveddy) | Vadamaradchi South-West (Karaveddy) | 4121 | LK4121 | Vadamaradchchi South-West (Karaveddy) | 41,102 | "Vadamaradchy" vs "Vadamaradchi": "y" vs "i". Spine has "Vadamaradchchi". |
| DS-319 | Jaffna | Vadamaradchy East | Vadamaradchi East | 4124 | LK4124 | Vadamaradchchi East | 13,537 | "Vadamaradchy" vs "Vadamaradchi": "y" vs "i". Spine has "Vadamaradchchi". |
| DS-320 | Jaffna | Vadamaradchy North (Point Perdro) | Vadamaradchi North (Point Pedro) | 4127 | LK4127 | Vadamaradchi North (Point Pedro) | 43,369 | "Vadamaradchy"/"Vadamaradchi" and "Perdro" (typo) vs "Pedro". |
| DS-321 | Jaffna | Thenmaradchy (Chavakachcheri) | Thenmaradchi (Chavakachcheri) | 4130 | LK4130 | Thenmaradchi (Chavakachcheri) | 67,782 | "Thenmaradchy" vs "Thenmaradchi": "y" vs "i". |
| DS-322 | Mullaitivu | Puthukudiyiruppu | Puthukkudiyiruppu | 4409 | LK4409 | Puthukkudiyiruppu | 39,532 | label Puthukudiyiruppu vs DCS Puthukkudiyiruppu: one "k" vs two. |
| DS-323 | Mullaitivu | Oddusudan | Oddusuddan | 4412 | LK4412 | Oddusuddan | 18,149 | label Oddusudan vs DCS Oddusuddan: "dan" vs "ddan". |
| DS-324 | Batticaloa | Poratheevu Pattu | Porativu Pattu | 5133 | LK5133 | Porativu Pattu | 38,627 | label Poratheevu Pattu vs DCS Porativu Pattu: "theevu" vs "tivu" (Tamil transliteration variants of the same word, ❓ linguistic reading). |
| DS-325 | Ampara | Sainthamarathu | Sainthamaruthu | 5225 | LK5225 | Sainthamaruthu | 29,873 | label Sainthamarathu vs DCS Sainthamaruthu: "a" vs "u". |
| DS-326 | Trincomalee | Padavisiripura | Padavi Sri Pura | 5303 | LK5303 | Padavi Sri Pura | 12,081 | label Padavisiripura (A9-A12) or Padavisripura (A6/A7) vs DCS "Padavi Sri Pura": spacing and "siri"/"sri". The two A-series label spellings differ from each other; both are in the match files. |

**Agent recommendation: approve all 15 (high).** The labels look like typos or alternative romanisations of the DCS names (❓ linguistic reading, not checked with a Sinhala or Tamil speaker). The numeric match removes the chance of a different DS.

### Group C: DCS code differs from the spine code

For these 12 DS, DCS and COD-AB use different DS codes for the same-named unit ([crosswalk report §4](../research/geography/crosswalk-report.md)). The label and the DCS name are the same (or a 1-letter variant); the risk is in the crosswalk step, because **a code-only join would give the wrong place**: for example DCS 2309 is Walapane, but spine `LK2309` is Nildandahinna, and DCS 2310 Nildandahinna has no `LK2310` at all.

| Item | District | DCS name | DCS code | Spine ID | Persons (A6) | GN-name coverage | GNs DCS | GNs spine | Confidence | Note |
|---|---|---|---|---|---|---|---|---|---|---|
| DS-327 | Nuwara Eliya | Kothmale West | 2302 | LK2321 | 41,955 | 0.98 | 49 | 49 | high | DCS 2302 ↔ spine LK2321 (suffix 21). |
| DS-328 | Nuwara Eliya | Mathurata | 2307 | LK2318 | 33,175 | 0.98 | 52 | 52 | high | DCS 2307 ↔ spine LK2318. |
| DS-329 | Nuwara Eliya | Walapane | 2309 | LK2324 | 65,287 | 0.95 | 62 | 62 | high | DCS 2309 Walapane ↔ spine LK2324. Spine LK2309 is a different unit (Nildandahinna): a code-only join would swap the two. |
| DS-330 | Nuwara Eliya | Nildandahinna | 2310 | LK2309 | 42,422 | 1.0 | 63 | 63 | high | DCS 2310 Nildandahinna ↔ spine LK2309. A code-only join would give DCS 2310 to a non-existent LK2310. |
| DS-331 | Nuwara Eliya | Thalawakelle | 2313 | LK2327 | 129,531 | 0.94 | 34 | 34 | high | label Thalawakele vs DCS Thalawakelle: one "l" vs two. DCS code 2313 differs from spine LK2327. |
| DS-332 | Nuwara Eliya | Norwood | 2314 | LK2330 | 161,367 | 0.91 | 35 | 35 | high | DCS 2314 ↔ spine LK2330. |
| DS-333 | Galle | Wanduramba | 3128 | LK3157 | 27,702 | 1.0 | 22 | 22 | high | DCS 3128 ↔ spine LK3157. |
| DS-334 | Galle | Madampagama | 3135 | LK3160 | 33,408 | 1.0 | 38 | 38 | high | DCS 3135 ↔ spine LK3160. |
| DS-335 | Galle | Rathgama | 3137 | LK3163 | 41,456 | 1.0 | 32 | 32 | high | DCS 3137 ↔ spine LK3163. |
| DS-336 | Batticaloa | Eravur Pattu | 5112 | LK5115 | 94,237 | 0.95 | 39 | 47 | medium-high | DCS 5112 ↔ spine LK5115. Spine LK5115 is the unit DCS calls 5112; DCS 5115 is spine LK5139. Both Eravur units: GN counts differ (DCS 39 / spine 47; DCS 15 / spine 13), see GN review queue. |
| DS-337 | Batticaloa | Eravur Town | 5115 | LK5139 | 26,468 | 0.8 | 15 | 13 | medium-high | DCS 5115 Eravur Town ↔ spine LK5139. GN counts differ (DCS 15 / spine 13), known GN-level issue in the GN review queue. |
| DS-338 | Ratnapura | Kaltota | 9119 | LK9154 | 13,018 | 1.0 | 12 | 12 | high | label Kalthota vs DCS Kaltota: extra "h". DCS code 9119 differs from spine LK9154. |

"GN-name coverage" is the share of DCS GN names found under the crosswalked spine unit. All 12 are above 0.9 except Eravur Town (0.80), and each is the best match in its district ✅. Check on the two Eravur units: DCS 5112 Eravur Pattu has 39 GNs against 47 in the spine, and DCS 5115 Eravur Town has 15 against 13; this is the known COD-AB boundary difference in the GN queue ([dating analysis](../research/geography/dcs-review-items-dating.md)), and the DS pairing itself is unaffected (names, district and GN-name test agree) ✅.

**Agent recommendation: approve all 12 (high; Eravur Pattu and Eravur Town medium-high because of the GN differences).** A protective follow-up for an agent, not for the lead: a test that DS-level joins never use the `LK` + code rule in Nuwara Eliya, Galle, Batticaloa and Ratnapura.

## 5. Groups A1 and A2: bulk approve, spine spelling differs

For these the table label equals the DCS name, the code is identical in DCS and the spine, and only the spine's spelling differs (A1: 25 rows) or the spine name is a shorter form (A2: 3 rows). They are approvable in bulk; A2 is shown so you can glance at the three shortened names.

**A2: spine name is shorter (crosswalk confidence 0.8)**

| Item | District | DCS name (= label) | DCS code | Spine ID | Spine name | Crosswalk conf. | Persons (A6) |
|---|---|---|---|---|---|---|---|
| DS-309 | Kandy | Kandy Four Gravets & Gangawata Korale | 2130 | LK2130 | Gangawata Korale | 0.8 | 153,329 |
| DS-310 | Matale | Laggala-Pallegama | 2224 | LK2224 | Laggala | 0.8 | 16,300 |
| DS-311 | Trincomalee | Trincomalee Town and Gravets | 5315 | LK5315 | Town & Gravets | 0.8 | 100,270 |

**A1: spine spelling differs (crosswalk confidence 0.95 or name similarity below 0.97)**

| Item | District | DCS name (= label) | DCS code | Spine ID | Spine name | Persons (A6) |
|---|---|---|---|---|---|---|
| DS-284 | Kandy | Udadumbara | 2118 | LK2118 | Ududumbara | 23,046 |
| DS-285 | Matale | Ambanganga Korale | 2221 | LK2221 | Ambanganga | 15,876 |
| DS-286 | Galle | Galle Four Gravets | 3139 | LK3139 | Galle 4 Gravets | 108,321 |
| DS-287 | Matara | Pitabeddara | 3203 | LK3203 | Pitabaddara | 48,867 |
| DS-288 | Matara | Kamburupitiya | 3227 | LK3227 | Kaburupitiya | 42,816 |
| DS-289 | Matara | Dickwella | 3248 | LK3248 | Dikwella | 56,468 |
| DS-290 | Jaffna | Island North (Kayts) | 4103 | LK4103 | Islands North (Kayts) | 9,931 |
| DS-291 | Jaffna | Island South (Velanai) | 4139 | LK4139 | Islands South (Velanai) | 16,600 |
| DS-292 | Mannar | Nanattan | 4212 | LK4212 | Nanaddan | 19,674 |
| DS-293 | Batticaloa | Koralai Pattu North (Vaharai) | 5103 | LK5103 | Koralai Pattu North | 25,475 |
| DS-294 | Batticaloa | Koralai Pattu West (Oddamavadi) | 5106 | LK5106 | Koralai Pattu West | 24,583 |
| DS-295 | Batticaloa | Koralai Pattu (Valachchenai) | 5109 | LK5109 | Koralai Pattu | 28,762 |
| DS-296 | Batticaloa | Koralai Pattu South (Kiran) | 5110 | LK5110 | Koralai Pattu South | 28,302 |
| DS-297 | Batticaloa | Manmunai Pattu (Araipattai) | 5127 | LK5127 | Manmunai Pattu | 36,533 |
| DS-298 | Ampara | Addalachchenai | 5233 | LK5233 | Addalaichenai | 53,214 |
| DS-299 | Trincomalee | Verugal (Eachchilampattu) | 5333 | LK5333 | Verugal | 14,062 |
| DS-300 | Kurunegala | Weerambugedara | 6166 | LK6166 | Weerabugedara | 36,590 |
| DS-301 | Anuradhapura | Horowpothana | 7124 | LK7124 | Horowpathana | 41,261 |
| DS-302 | Anuradhapura | Galenbindunuwewa | 7127 | LK7127 | Galenbidunuwewa | 51,952 |
| DS-303 | Polonnaruwa | Hingurakgoda | 7203 | LK7203 | Higurakgoda | 70,651 |
| DS-304 | Badulla | Meegahakivula | 8109 | LK8109 | Meegahakiula | 22,683 |
| DS-305 | Badulla | Kandaketiya | 8112 | LK8112 | Kandeketiya | 26,913 |
| DS-306 | Monaragala | Moneragala | 8215 | LK8215 | Monaragala | 56,951 |
| DS-307 | Kegalle | Aranayaka | 9209 | LK9209 | Aranayake | 69,075 |
| DS-308 | Kegalle | Bulathkohupitiya | 9224 | LK9224 | Bulathkohipitiya | 45,237 |

Group A0 (283 rows) has identical names in table, DCS and spine (or a trivial punctuation difference); see the CSV. **Agent recommendation: bulk approve A0, A1 and A2 (high; A2 medium-high).** Spelling in the *spine* (for example "Ududumbara" vs DCS "Udadumbara") is a display-name matter for a later naming decision (D-012), not a matching risk, because code and GN names agree.

## 6. Hard case: DCS 5224 Kalmunai (item DS-340 in the CSV)

**What the tables say.** DCS 5224 Kalmunai: 29 GNs (`5224005` to `5224145`), **52,798 persons** (A6 row 245, equals the GN sum ✅) and 13,481 occupied housing units (A9 row 226 as recorded in the match file, 🟡), 0.24% of Sri Lanka and 7.1% of Ampara district ✅. DCS 5221 Kalmunai North Sub is the sister DS: 31,556 persons, 8,675 housing units, already mapped to `LK-ADM3-P0001` (D-022).

**What the spine has.** `LK5221` "Kalmunai" is COD-AB's single unit for both. It has 58 GN children: 29 named (exactly DCS 5221's GNs, per D-022 and the null-name analysis) and **29 unnamed** (`LK5221150`–`LK5221215` and `LK5221230`–`LK5221300`; codes 220 and 225 are not used) ✅. `LK5221` has **no DCS DS code and no census values** today ✅. NSDI also maps its code 5224 to `LK5221` ([crosswalk codes](../../catalog/geographies/codes/nsdi.csv)), which tells us NSDI sees the merged unit too.

**Test I ran.** The 29 DCS GN names of DS 5224 against the GN names under every spine DS in Ampara: best coverage 0.00 ✅. No named spine unit contains them, as expected, because the matching spine GNs have no names.

**Hazard.** DS name "Kalmunai" is identical in DCS and spine, so any name-only join would attach 5224's 52,798 persons to `LK5221`, a unit that also covers DCS 5221. That is why this row is excluded from the bulk approvals; the match files currently list `5224 Kalmunai` with `exact_name`, and the crosswalk leaves it unmatched on purpose ✅.

**Weak signal, not evidence ❓.** DCS 5224's GN codes run `005`–`145` in steps of 5 (29 codes). The 29 unnamed COD-AB codes could be an order-preserving renumbering of them (14 codes `150`–`215`, then a gap at `220`/`225`, then 15 codes `230`–`300`). That is consistent with the data but equally consistent with other pairings, and GN geometry (the NSDI snapshot held has DS geometry only, not GN geometry) is the test. **Do not use it for GN matching.**

**Options**

| Option | What it means | Cost and risk |
|---|---|---|
| **1. Leave unmatched (status quo)** | 5224's people count in Ampara district and Sri Lanka only; no Kalmunai DS page or row; QA keeps reporting it | Safe. A real DS of 52,798 people is absent from DS pages, rankings and the DS similar-place lists |
| **2. Add a second provisional unit** `LK-ADM3-P0002` "Kalmunai" under Ampara | Defined as `composed_of` the 29 unnamed COD-AB GNs **as a set**, justified by elimination: COD-AB `LK5221` = DCS 5221 + DCS 5224 (58 = 29 + 29, and the 29 named are exactly 5221) | DS-level values (population, housing, ethnicity and religion, etc.) can then join. GN-level values for the 29 GNs stay in district totals only, since no GN-to-GN pairing is known. The set claim rests on COD-AB's merge being exactly those two DS 🟡, not on geometry. Needs a lead decision and a note in D-022 |
| **3. Wait for evidence** | Ask the Survey Department/DCS for a GN list with numbers, or obtain GN geometry, then do option 2 with GN-level pairing | Most accurate; depends on replies not yet received |

**Agent recommendation: option 2, confidence medium; option 1 stays in force until you decide.** Reason: D-022 states that a second provisional unit "depends on matching the 29 unnamed GNs". I think that is stricter than a DS-level unit needs: a DS value needs the set of GNs, not the pairing of each GN to its name, and the set follows from elimination. If you want GN-level confirmation first, choose option 3. In either case the name must not be matched by text alone; and the unit name needs care because spine `LK5221` is also called "Kalmunai" (the DCS name for 5224). Proposed display: "Kalmunai (DCS DS 5224)", with a neutral note that it follows the DCS publication and implies no position on any administrative question (AGENTS rule 12). The 29 unnamed GNs keep p-code labels (D-028) either way.

## 7. What I did not verify

- ❓ DCS spelling is treated as correct for DCS tables; official Sinhala/Tamil names were not consulted. Variant explanations in §4 are reading of the strings only.
- 🟡 A6/A9 totals come from the `evidence` column of the match files; the A6 and A9 sheets were not reopened. They do equal the GN sums recomputed from `GN_population.xlsx` and `GN_housing.xlsx` outputs in the build ✅.
- ❌ No GN geometry was available for Kalmunai (NSDI snapshot has DS-level geometry only).
- The GN-name test uses names normalised by the same rules as the crosswalk (`norm_core`, `norm_loose`); a rename that keeps spelling similar would pass. It is a strong consistency check, not proof.
- Not re-checked: the 13 DS with differing GN counts (GN queue) and the 42 DCS GN queue items.

## 8. What happens after you decide

Not done here. After the lead's decisions an agent will (1) set `decided_by` on the approved rows in the two name-match files to the lead with the date, (2) for option 2, add `LK-ADM3-P0002`, its relations and a DCS 5224 crosswalk row, amend D-022, rebuild and re-run the audits, (3) record the approval in `docs/decisions/lead-approvals-log.md`.

**Fastest path:** approve groups A0, A1, A2, B and C in one go (338 rows; write "approve all except …" or fill the CSV `lead_decision` column), and pick one option for §6.
