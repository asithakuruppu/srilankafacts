# QA: `composite` v0.1

Built 2026-11-17 with `uv run slf profile spaces` · method: [composite-space.md](../methods/composite-space.md)

| Check | Result |
|---|---|
| Block contributions sum to the profile axis scores (339 × 5) | max error 8.9 × 10⁻¹⁶ ✅ |
| Equal weights reproduce the profile build's similar lists (example: Thimbirigasyaya, 10 of 10 in the same order) | ✅ (one distance differs in the third decimal: the profile build stores float32) |
| Browser vs pipeline, 10 nearest for all 339 DS divisions under 5 weight settings (equal; no identity; no housing; no demography; 2 / 1 / 0.5) | 1,695 of 1,695 lists equal, distances within 2 × 10⁻⁶ ✅ |
| Removing the identity block changes Thimbirigasyaya's neighbours | ✅ (e2e test) |
| Explanation shares sum to 100% (block and axis) | ✅ (unit and e2e tests) |
