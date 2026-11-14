# Lead approvals log

Every approval the lead gives on a corrections entry, a QA sheet or a data judgement is recorded here, so it can be found and reversed later. Formal decisions stay in [decision-log.md](decision-log.md); this log is for sign-offs that act on specific data or outputs.

**Entry format:** ID (LA-NNN) · date · what was approved · scope · evidence the approval rests on · what the lead said (paraphrase or quote) · how to reverse.

---

## LA-001: Approve corrections entry C-001 wording

- **Date:** 2026-11-12
- **Approved by:** Shamil Asitha Kuruppu (lead)
- **What:** The wording of `C-001` in [corrections/log.yaml](../corrections/log.yaml). The entry records that DCS GN 2206125 Kandalama and DCS GN 2206265 Kiralessa were swapped between COD-AB units LK2206125 and LK2206300 in v2026.11.1 to v2026.11.5, and that the fix is in v2026.11.6-preview.1. It affects 28 values across all 14 census indicators.
- **Scope:** `scope: private_preview`. The entry is not yet public (no public release exists).
- **Evidence:** [docs/research/geography/null-name-gns.md](../research/geography/null-name-gns.md), [catalog/geographies/manual-matches.csv](../../catalog/geographies/manual-matches.csv)
- **Lead's words:** "Approve the C-001 wording."
- **Change made:** `approved_by` set from `null` to `"Shamil Asitha Kuruppu (lead), 2026-11-12"`. A public release now accepts this entry.
- **How to reverse:** set `approved_by` back to `null` in `docs/corrections/log.yaml`. A public release would then refuse to build until it is approved again.

---

## LA-002: Q01 accuracy check of 20 values, provisional

- **Date:** 2026-11-12
- **Approved by:** Shamil Asitha Kuruppu (lead)
- **What:** The 20 values in the Q01 lead sheet for release `v2026.11.7-preview.1` are approved, "for now".
- **Scope:** Private preview only. Q01 is not passed for a public release on this basis alone.
- **Evidence:** [docs/qa/accuracy-audit-v2026.11.7-preview.1.md](../qa/accuracy-audit-v2026.11.7-preview.1.md), [docs/qa/q01-lead-sheet-v2026.11.7-preview.1.csv](../qa/q01-lead-sheet-v2026.11.7-preview.1.csv). The machine re-trace found 0 errors in 207 values; the 20 were checked by the lead against source documents.
- **Lead's words:** "20 Q01 approved for now."
- **Caveat:** "For now" means the approval may be revisited. The lead has not recorded which source pages or cells were checked.
- **How to reverse:** mark the 20 rows as not approved in the Q01 sheet, and note the reversal here as a new entry (LA-NNN) that references LA-002. Do not edit this entry in place.

---

## LA-003: Profile space similar-place lists look correct

- **Date:** 2026-11-12
- **Approved by:** Shamil Asitha Kuruppu (lead)
- **What:** The lead's judgement that the profile space's similar-place lists look correct, under D-031 (similar places for DS divisions, and GN divisions as position and unusualness only).
- **Scope:** Judgement on the output of `profile` in preview `v2026.11.8-preview.1`. Not a formal approval of the profile space as a whole.
- **Evidence:** [docs/methods/profile-space.md](../methods/profile-space.md), [docs/qa/profile-space-v0.2.md](../qa/profile-space-v0.2.md)
- **Lead's words:** "profile spaces looks correct."
- **Not covered by this entry:** the other two items in the next-actions list. The 5 named places used to judge the lists, and the written axis labels, are still open. Record them as separate LA entries when the lead provides them.
- **How to reverse:** add an LA entry that withdraws this judgement. The profile preview can be rebuilt without the change.

---

## LA-004: Household indicators on place pages: total plus 37 shares; counts in downloads only

- **Date:** 2026-11-13
- **Approved by:** Shamil Asitha Kuruppu (lead)
- **What:** Of the 75 household and amenity indicators (D-032 step a), place files, per-level API files and the website carry `households_total` and the 37 shares. The 37 category counts are marked `distribution: downloads_only` in `catalog/indicators/`: they stay in `observations.parquet` and `.csv` and are listed in `api/v1/indicators.json`, but are not in place files or per-level files.
- **Scope:** How releases distribute these indicators. No values change.
- **Evidence:** [docs/methods/census-2024-households.md](../methods/census-2024-households.md) §5 (trial release sizes); the agent's recommendation in PR 28.
- **Lead's words:** "Total plus 37 shares."
- **How to reverse:** remove `distribution: downloads_only` from the 37 count files (the default is `api`) and rebuild the release.

## LA-005: LA-004 also applies to age, sector and local authority type

- **Date:** 2026-11-14
- **Approved by:** Shamil Asitha Kuruppu (lead)
- **What:** The 51 indicators of D-032 step b follow LA-004. The 26 shares go to place files, per-level API files and the website. The 25 counts (`population_age_*`, `population_sector_*`, `population_local_authority_*`, without `_share`) are `distribution: downloads_only`.
- **Scope:** How releases distribute these indicators. No values change.
- **Evidence:** [docs/qa/census-2024-age-sector-local-authority.md](../qa/census-2024-age-sector-local-authority.md) (trial release sizes); the agent's recommendation in PR 29.
- **Lead's words:** "Yes, keep LA-004."
- **How to reverse:** remove `distribution: downloads_only` from the 25 count files and rebuild the release.
