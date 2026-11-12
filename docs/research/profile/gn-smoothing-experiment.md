# GN similar places from smoothed values: experiment for D-031 option (c)

Prepared 2026-11-12 by an agent for the lead. Verification tags: ✅ verified by running ·
🟡 claimed, not checked · ❌ not found or failed · ❓ assumption.

Reproduce: `uv run slf profile smoothing-experiment` (about 3 minutes). Results:
[`gn-smoothing-experiment.json`](gn-smoothing-experiment.json). Code:
`pipeline/slf/profile_smoothing.py`.

## Answer

**No.** Smoothing does not make GN similar-place lists stable ✅. Under the same count-noise test
that led to D-031:

- raw values keep **12.9%** of a GN's top-20 list;
- smoothing towards the national rate keeps **12.4%**;
- smoothing towards the GN's own DS keeps **13.1%**;
- also restricting neighbours to the same district keeps **37.6%**.

The bar, set before the run, was **70%**. No variant passes, including two exploratory ones.

**Recommendation:** keep D-031 as it is. Close option (c), and treat option (d), broad GN types,
as the route to GN comparisons. Test it with the same noise test, applied to group membership
instead of a ranked list.

## Method ✅

- **Data:** census build observations, GN level. 13,934 GNs with vectors, same exclusions as the
  profile build.
- **Space:** profile space v0.2 recipe (D-025, D-029), refitted on each variant's inputs; 3 axes
  retained in every main variant.
- **Smoothing:** the census spatial context's own empirical Bayes estimators
  (`slf.enrich`):
  - beta-binomial for each age share and for the male share, which gives the sex ratio;
  - gamma-Poisson for persons per occupied housing unit.

  Population, housing units and density are not smoothed: they are counts, and their noise on the
  log scale is small. The table below confirms this.
- **Priors:** national (`eb_national`), or the GN's own DS division (`eb_ds`). A DS with fewer
  than 5 GNs falls back to the national prior.
- **Noise test:** identical to PR 14's (the evidence for D-031). Each count is redrawn from a
  Poisson distribution with the published count as its mean. The values are then re-derived,
  **re-smoothed**, and projected through the original standardisation. Top-20 overlap is
  averaged over 5 runs (seed 20241108).
- **Parity check:** the raw variant gives 0.129, against PR 14's 0.13 ✅. The test is the same.

## Results ✅

| Variant | Mean overlap under count noise | Passes 0.70 | Chance | Median shift ÷ median distance to 20th neighbour | Same list as raw |
|---|---|---|---|---|---|
| `raw` (D-031 baseline) | **0.129** | no | 0.001 | 2.02 | 1.000 |
| `eb_national` | **0.124** | no | 0.001 | 2.14 | 0.799 |
| `eb_ds` | **0.131** | no | 0.001 | 2.07 | 0.351 |
| `eb_ds_within_district` | **0.376** | no | 0.036 | 2.07 | 0.119 |
| `raw`, without persons per unit (exploratory) | 0.156 | no | 0.001 | 2.23 | 0.132 |
| `eb_ds_within_district`, without persons per unit (exploratory) | 0.507 | no | 0.036 | 2.34 | 0.078 |

By GN population (mean overlap, with the number of GNs in brackets):

| Variant | 100–999 | 1,000–1,999 | 2,000–4,999 | 5,000+ |
|---|---|---|---|---|
| `raw` | 0.075 (5,169) | 0.089 (5,781) | 0.263 (2,638) | 0.609 (346) |
| `eb_national` | 0.078 | 0.083 | 0.243 | 0.580 |
| `eb_ds` | 0.085 | 0.090 | 0.254 | 0.587 |
| `eb_ds_within_district` | 0.319 | 0.333 | 0.536 | **0.718** |
| `raw`, without persons per unit | 0.102 | 0.103 | 0.308 | **0.705** |
| `eb_ds_within_district`, without persons per unit | 0.460 | 0.460 | 0.666 | **0.799** |

Only GNs with 5,000+ people (346 of 13,934) clear 0.70, and only in some variants.

## Why smoothing does not help ✅

The noise is not where smoothing acts. Under one noise draw (raw variant), each input's share of
the squared movement in the space is:

| Input | Noise SD ÷ place-to-place SD | Share of the movement |
|---|---|---|
| Persons per occupied housing unit | 0.44 / 0.53 | **75%** |
| Share aged 60–64 | 0.26 / 0.41 | 9% |
| Sex ratio | 0.30 / 0.38 | 5% |
| Other age shares | 0.13–0.20 / 0.40 | 3–4% each |
| Population, housing units, density | ≤ 0.05 / 0.41–0.58 | ≤ 1% |

- **Persons per unit** is a ratio of two noisy counts, and its true variation between GNs is
  small. So its noise is almost as large as its signal. The gamma-Poisson estimator shrinks it
  only a little, because the observed spread between GNs looks like real variation to the
  estimator ❓. (Its noise model treats housing units as fixed, while the test redraws them too.)
- **Removing persons per unit** cuts the median movement from 0.32 to 0.13. But GNs also get much
  closer together: the median distance to the 20th neighbour falls from 0.159 to 0.059. Noise
  still moves a typical GN about twice the radius of its own top-20 list.
- **The root cause:** with 13,934 GNs in a 3-axis space, a GN's 20 nearest neighbours sit so close
  that ordinary count noise reshuffles them. A ranked top-20 list at this scale asks for more
  precision than the counts carry.

## What this means for D-031

1. **Option (c), smoothing, does not reach the bar.** Recommendation: record it as tested and
   rejected in D-031's "Revisit when" line. This is a lead decision; the text is in
   "Decisions needed" below.
2. **Comparing within the district helps most** (0.376), partly because there are fewer
   candidates (chance rises from 0.001 to 0.036). It still falls well short.
3. **Option (d), broad GN types (A03 step 7), is the remaining route.** A type label only needs a
   GN to stay in the same broad group, not to keep its exact rank among 13,934 GNs. Its test
   should be "share of GNs whose type survives the noise test". Suggested bar: 90% ❓.
4. **A space change** (dropping persons per unit, or merging ages 60–64 into 60+) would also need
   a new space version and the lead's agreement. On these numbers it is not enough alone.

## Not verified / limits

- 5 noise runs per variant, as in PR 14. More runs would narrow the estimates; it would not change
  the conclusion (the best main variant is 0.376 against 0.70).
- Within-district neighbours: districts with 20 or fewer GNs get no list. The smallest district has 95
  GNs, so no GN was dropped ✅ (places = 13,934 in every variant).
- The noise model is PR 14's (independent Poisson redraws, area held fixed). It is a sensitivity
  test, not an estimate of census error.

## Decisions needed from the lead

1. Should D-031's "Revisit when" say that option (c) was tested on 2026-11-12 and did not reach
   70%? Recommendation: yes.
2. Should option (d), broad GN types, be the next GN-comparison task, tested by type stability?
   Recommendation: yes, but after 1B, since it is not needed for the public beta.
