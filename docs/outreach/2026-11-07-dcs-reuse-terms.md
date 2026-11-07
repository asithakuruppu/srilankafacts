# Draft: reuse terms for Census 2024 tables (Department of Census and Statistics)

Status: **draft** · Channel: email or letter to DCS (Census division or Director General's office; address to be chosen by the lead) · Prompt: R04 · Language: English

---

**Subject:** Request for clarification: reuse of published Census of Population and Housing 2024 tables

Dear Sir/Madam,

I am writing on behalf of Sri Lanka Facts, an early-stage, independent and self-funded project that is building an open, map-based reference of Sri Lankan places and statistics, with every figure linked to its official source. The project's code is public at https://github.com/asithakuruppu/srilankafacts.

We would like to use the Census of Population and Housing 2024 tables that the Department publishes on its website, especially the tables by Grama Niladhari division. Before we use them, we would be grateful for clarification on three points:

1. **Reuse terms.** May these published tables be reproduced and redistributed, in full or in part (for example as maps, downloadable tables and through a data interface), with attribution to the Department? Does this include use by organisations that may charge for services, such as analysis built on the published figures?
2. **Attribution.** Is there a preferred wording for attribution? We currently plan to use: "Source: Department of Census and Statistics, Sri Lanka, Census of Population and Housing 2024."
3. **Machine-readable versions and codes.** Are the GN-level tables available in a spreadsheet or CSV format, and is there an official list of the GN and DS division codes and names used for the 2024 Census?

In return, we will attribute the Department on every page and download that uses its figures, link back to the original publications, never alter official figures (any correction we suggest is shown separately with evidence), and share privately with the Department any inconsistencies we find, so they can be checked before anything is published.

Thank you for your time. I would be glad to provide any further information.

Yours faithfully,

[Name]
[Role], Sri Lanka Facts
[Email] · [Phone]

---

## Facts stated and their sources

| Claim in the draft | Source |
|---|---|
| Project is early-stage, independent, self-funded | Lead (vision docs; `docs/vision/organisation-and-business-model.md`) |
| Code is public at github.com/asithakuruppu/srilankafacts | ✅ repository is public (checked with `gh repo view`, 2026-11-07) |
| DCS publishes CPH 2024 tables, including by GN division | `docs/research/ecosystem-landscape.md` §6 (DCS Census 2024: GN-level topic tables; final report) 🟡 |
| No public reuse licence found | `catalog/sources/dcs.yaml` notes; landscape §6 ("Rights known? ❌ ask") |

## Notes for the lead
- Choose the recipient and postal or email address yourself; none is recorded in the catalogue, and I did not invent one.
- The commercial-use question matters because the business model includes paid services (`data-model.md` §2.4: commercial products may only use datasets with `commercial_reuse: yes`).
- Record the reply as evidence in `catalog/sources/dcs.yaml` (`rights.evidence`).
