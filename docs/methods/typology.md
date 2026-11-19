# Method: `typology` v1.0, types of DS division

Status: **built locally, private preview** · 2026-11-17 · Decision: D-047 (Proposed) · Code:
`pipeline/slf/spaces.py` (`build_typology`), command `uv run slf profile spaces` · Catalogue:
`catalog/spaces/typology.yaml` · QA: [typology-v1.0.md](../qa/typology-v1.0.md)

Verification tags: ✅ checked by running it · 🟡 from a source, not independently checked · ❓ assumption.

## What a type is

A type is a group of DS divisions that sit close together in the `profile` space v0.3 (age
structure, sex ratio, housing, density, and ethnic group and religion, D-037). It is a
similarity grouping. It is not a fact about a place, not a ranking, and not an official
classification. GN divisions get no type (D-031).

## How it is built

1. The DS profile is rebuilt from the census with the profile build's own code (`prepare`,
   `fit`) and checked against the stored profile vectors: largest difference 1.2 × 10⁻⁷, which is
   the float32 precision the profile build stores ✅.
2. k-means (Lloyd's algorithm, k-means++ starts, best of 25 runs) on the 339 places × 5 retained
   axes, for every k from 3 to 10. Plain NumPy, no new dependency.
3. **Stability.** For each k, 50 bootstrap resamples: fit on the resample, assign every place to
   its nearest centre, compare with the full-data grouping by the adjusted Rand index (ARI; 1 =
   identical, 0 = chance).
4. **Choice of k.** The highest silhouette among the k whose mean ARI is at least 0.75; if no k
   qualifies, the most stable k. On the real data only k = 5 qualifies (ARI 0.82) ✅.
5. **Numbering.** Types are numbered by size, largest first.
6. **Draft names.** Each type's centre is projected back from the axes to the inputs, in standard
   deviations from the national average. The name lists up to two inputs at least 0.5 SD above
   and two at least 0.5 SD below, for example "Higher share aged 60-64 and share aged 65+; lower
   share aged 15-59". Names are tagged `machine_generated_draft` in the data and the interface.
   Since 2026-11-19 (D-054) names use age, sex, size and housing inputs only, never ethnic group
   or religion; those inputs still shape the types and are listed in each type's input profile.
7. **Per place:** its type, its distance to the type's centre, and its *agreement*: how often its
   type mates stay together across the bootstrap runs (mean Jaccard overlap).

## Where it shows

On `/explore/space` (W08), in the Profile space: the map and the similarity view are coloured by
type, and a list gives each type's size, draft name, three typical members and stability.

## Limits

- k-means assumes roughly round groups of similar spread; the silhouette of 0.27 says the types
  overlap. Places near a boundary between types carry a lower agreement.
- Ethnic group and religion separate three of the five types most strongly (D-037). Until
  2026-11-19 they also led those types' names; they are now left out of names (D-054). The names
  still await a person's review.
