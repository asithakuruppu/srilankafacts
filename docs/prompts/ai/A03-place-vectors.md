# A03: Profile vector space and "places like this"

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1 (typology: 2) | AI / analytics | 2 | 2026-11-07 | active |

## When to use
After census observations are validated (D01) for the blocks in use. Builds profile vectors, similar places with reasons, and later the typology.

## Read first
- `AGENTS.md`
- `docs/architecture/vector-space-model.md` (all; §5 defines the method)
- `docs/architecture/spatial-first-analytics.md` §6.4 (guardrails)
- `docs/decisions/decision-log.md` D-015, D-016

## Inputs (fill in)
```
LEVELS: gn, ds
VINTAGE: 2024
BLOCKS: demography, housing_amenities, education_work   # Stage 1 blocks
RECIPE_VERSION: v1
TOP_K: 20
MODE: similarity        # similarity | typology (Stage 2)
```

## Task
1. Propose the space first, as `catalog/spaces/profile.yaml` (`space_id: profile`, version, entity types `geography` and `indicator`, metric `euclidean`): indicators per block, transformation (share, per-capita, log-ratio), standardisation, block weights (equal by default), factorisation method (PCA; correspondence analysis only if you justify it for count tables) and number of axes with the criterion. **Exclude ethnicity and religion.** Stop and ask the lead to approve before computing.
2. Build the joint space: place coordinates and indicator coordinates from the same factorisation. Write `vectors/profile_{RECIPE_VERSION}.parquet` (`entity_type`, `entity_id`, `period`, `space_id`, `space_version`, `vector` float32, `norm`) and `vectors/profile_{RECIPE_VERSION}_axes.parquet` (loadings, variance explained, draft axis labels marked AI-generated). Missing values: state the rule; places with too many gaps are listed, not dropped silently.
3. Similar places: top-K nearest neighbours per place, each with an **exact decomposition** of the squared distance into axis and indicator contributions (top 3 alike, top 3 different). Write `vectors/similar_{level}_{vintage}.json` recording `space_id` and `space_version`.
4. "How unusual": each place's distance from the national centre, with its percentile.
5. Two-space contrasts: for each place, bordering units (from the contiguity graph) that are far apart in `profile`; feed these to the QA report as well.
6. Sensitivity check: rerun with one block removed at a time; report neighbour-list overlap at K.
7. *(Typology mode, Stage 2)* Cluster in the profile space with k-means or Ward over a stated k range; choose k with stated criteria; draft **descriptive** type names for the lead to rewrite and approve.

## Constraints
- No vector database or embedding service (D-015). Plain Python/NumPy is enough.
- Never rank places as better or worse from vectors.
- Type names are drafts until the lead approves them (AI-generated text is labelled, AGENTS.md rule 7).

## Verify (show real output)
- Vector table shape and missing-value report.
- 5 hand-picked places (the lead names them) with their top-10 similar places and reasons.
- A test showing the per-indicator contributions sum to the squared distance for 100 random pairs.
- Variance explained per axis and the top loadings, for the lead to label.
- Stability numbers from the sensitivity check.

## Deliverables
Space definition, embedding and axis files, similar-places file, unusualness scores, contrasts, sensitivity report, methods note in `docs/methods/profile-space.md`.

## Done when
For any GN or DS, the release lists similar places with understandable reasons, and the lead has approved the recipe.

Report using the format in `AGENTS.md`.
