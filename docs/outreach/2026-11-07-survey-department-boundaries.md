# Draft: boundary currency and reuse terms (Survey Department of Sri Lanka, copy to NSDI)

Status: **draft** · Channel: letter or email to the Survey Department; copy to the NSDI geoportal team (addresses to be chosen by the lead) · Prompt: R04 · Language: English

---

**Subject:** Questions on the currency and reuse of administrative boundary data

Dear Sir/Madam,

I am writing on behalf of Sri Lanka Facts, an early-stage, independent and self-funded project that is building an open, map-based reference of Sri Lankan places and statistics, with every figure linked to its official source (code: https://github.com/asithakuruppu/srilankafacts).

For administrative boundaries we currently use the Common Operational Dataset of administrative boundaries for Sri Lanka published by UN OCHA on the Humanitarian Data Exchange. That dataset (version 03) names the Survey Department of Sri Lanka as its source and states that its boundaries were created in August 2022. We also consulted the administrative boundary service on the NSDI geoportal. We would be grateful for guidance on three points:

1. **Currency.** Are the August 2022 boundaries still the current official administrative boundaries? The OCHA dataset has 339 Divisional Secretariat units and 14,043 Grama Niladhari divisions, while the NSDI service lists 14,051 GN divisions and other sources cite 331 DS divisions. Is there an official list, with codes, of current DS and GN divisions and the dates of recent changes?
2. **Reuse terms.** On what terms may the administrative boundaries published on the NSDI geoportal be reused and redistributed, for example in public maps and downloadable files, with attribution to the Survey Department?
3. **Attribution.** Is there a preferred attribution wording?

In return, we will attribute the Department wherever its boundaries are used and share with you, privately and before publication, any inconsistencies our quality checks find. For example, the OCHA release notes that 65 GN divisions lack an English name, and that 530 GN divisions belong to groups with identical English names but different Sinhala spellings.

Thank you for your time.

Yours faithfully,

[Name]
[Role], Sri Lanka Facts
[Email] · [Phone]

---

## Facts stated and their sources

| Claim in the draft | Source |
|---|---|
| COD-AB version 03, source Survey Department, boundaries created 2 August 2022 | ✅ HDX metadata snapshot `raw/ocha-hdx/cod-ab-lka/20261107T163632Z/hdx_package_show.json` (sha256 `bcab1d4a…`) |
| 339 DS units and 14,043 GN divisions in COD-AB | ✅ counted in our build (`docs/qa/geography-spine-v0.md` §4); matches HDX notes |
| NSDI lists 14,051 GN divisions | `docs/lanka-data-layer-audit.md` §11 (queried 2026-11-07) 🟡 |
| 331 DS divisions commonly cited | `docs/research/ecosystem-landscape.md` §1 🟡 |
| 65 GN without English name; 530 in conflicting-Sinhala-name sets | ✅ HDX caveats (quoted in the QA report §1); 65 also confirmed in our build (§6) |
| NSDI shows no licence text | `docs/lanka-data-layer-audit.md` §11 |

## Notes for the lead
- The Survey Department website refused an automated check on 2026-11-07, so I could not confirm a current contact address. Please choose it yourself.
- Survey Department geodetic data is sold (`docs/architecture/multi-scale-features.md`); this letter asks only about the published administrative boundaries.
