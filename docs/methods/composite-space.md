# Method: `composite` v0.1, the profile space with block weights

Status: **built locally, private preview** · 2026-11-17 · Decision: D-047 (Proposed) · Code:
`pipeline/slf/spaces.py` (`build_composite`), `web/src/lib/atlas/spaces.ts` · Catalogue:
`catalog/spaces/composite.yaml` · QA: [composite-v0.1.md](../qa/composite-v0.1.md)

## Idea

The profile space weights its three blocks of inputs equally (demography, housing, and at DS
level ethnic group and religion). A reader may want to ask "alike in housing, whatever the
population mix?". The composite space answers that without a new fit and without losing the exact
decomposition of distances.

## Construction

Each DS place's score on a retained axis is a sum over its weighted, standardised inputs. Grouping
those inputs by block splits the score exactly:

  score[axis] = Σ over blocks of contribution[block][axis],
  contribution[block][axis] = z[block's inputs] · basis[block's inputs, axis].

The pipeline writes the contributions (339 places × 3 blocks × 5 axes, rounded to 6 decimals).
The browser multiplies each block's contributions by the reader's weight (0 to 2, in steps of
0.25) and adds them up. With all weights 1 this is profile v0.3 exactly; weight 0 removes a block.

## Exactness

- The squared distance between two places is a sum over axes, so each axis's share is exact.
- Within an axis, the squared difference d² equals Σ over blocks of (weighted block difference ×
  d), so each block's share is exact too. A block's share can be negative when it pulls two places
  together on an axis; the shares always sum to 100%.

## Where it shows

On `/explore/space`: three sliders, the neighbour table and the "Explain" panel recompute in the
browser; the URL keeps the weights (`w=1,1,0`).
