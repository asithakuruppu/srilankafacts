# S02: Commissioned analysis for a client

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1+ | Services | 1 | 2026-11-07 | active |

## When to use
For paid or pilot work such as a district profile pack, a sampling frame or a catchment analysis (business model §3).

## Read first
- `AGENTS.md`
- `docs/vision/organisation-and-business-model.md` §3–§4 (offers, firewall rules)
- The catalogue rights of every dataset you plan to use

## Inputs (fill in)
```
BRIEF:        sanitised description of the client's question (no confidential details in the public repo)
DELIVERABLES: e.g. GN-level sampling frame CSV + maps + 5-page note
DEADLINE:     date
WORKSPACE:    private location for client files (never this public repository)
```

## Task
1. **Scope note:** questions, data needed, a rights check (only datasets with `commercial_reuse: yes`, or an explicit permission on file), method, assumptions, deliverables and a time estimate.
2. **Reproducible analysis** in the private WORKSPACE, reading only public release data plus any client-supplied data.
3. **Common recipes:**
   - *Sampling frame:* GN-level units with population and households, strata (district, urban/rural/estate where available), PPS selection with a recorded seed, replacement units, and field maps.
   - *Catchment:* population and households within a radius of sites (area-weighted GN shares, method stated); travel time only if a routing setup exists.
   - *Profile pack:* standard place-page content plus the client's indicators, with consistent charts and maps.
4. QA: totals reconcile with the release; method appendix; limitations.
5. **Firewall:** if you find an error in public data, open a public issue to fix it for everyone (without client details). Never change public outputs for a client.
6. Keep a time log (for pricing) in the private workspace.

## Constraints
- No client data or confidential details in this repository. No personal data processing without a written basis and PDPA review.

## Verify (show real output)
Reconciliation of totals; the seed used for any random selection; a deliverables checklist.

## Deliverables
Client deliverables (private), a public-safe summary of reusable improvements (if any) for the main repository.

## Done when
The client gets a reproducible, documented result, and public data stays independent.

Report using the format in `AGENTS.md`.
