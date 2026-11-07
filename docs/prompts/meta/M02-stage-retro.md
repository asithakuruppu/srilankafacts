# M02: Stage retrospective and docs refresh

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| end of each stage | Strategy / Docs | 1 | 2026-11-07 | active |

## When to use
At the end of each stage, or every 6–8 weeks if a stage runs long.

## Read first
- `AGENTS.md`
- `docs/roadmap/development-strategy.md`, `docs/decisions/decision-log.md`, `docs/00-start-here.md`
- Merged PRs, QA reports and issues since the last retrospective

## Inputs (fill in)
```
STAGE:  the stage being closed
NOTES:  the lead's own observations (optional)
```

## Task
1. **Plan vs actual:** deliverables done, partly done or dropped; durations against estimates; exit criteria met?
2. **Throughput:** verified values per hour (from verification sheets), PRs per week, rework rate (PRs needing changes after Q05).
3. **What went wrong and why** (prompts that misled agents, missing decisions, data surprises).
4. **Update docs:** re-estimate the next stage in `development-strategy.md`; update statuses in the decision log (ask the lead to confirm changes); update the current status in `00-start-here.md`; fix prompts that were wrong (bump versions); refresh `draft` prompts needed in the next stage (using M03).
5. **Next stage plan:** ordered prompt sequence with parallel tracks, and the decisions needed from the lead.
6. Write `docs/roadmap/retros/{{stage}}-{{date}}.md`.

## Constraints
- Honest numbers. If a metric wasn't tracked, say so and propose how to track it.

## Verify (show real output)
Lists of merged PRs and closed issues used for the analysis.

## Deliverables
Retrospective document, doc and prompt updates, next-stage plan.

## Done when
The plan for the next stage reflects reality, and the docs are current.

Report using the format in `AGENTS.md`.
