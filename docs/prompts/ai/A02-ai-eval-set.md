# A02: Public AI evaluation set for Sri Lankan facts

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 2 | AI / Quality | 1 | 2026-11-07 | draft (refresh with M03 at Stage 2) |

## When to use
To measure how accurately our MCP server, and optionally popular assistants, answer questions about Sri Lankan places (OPP-10).

## Read first
- `AGENTS.md`
- Release data and indicator catalogue
- `docs/lankadata-audit.md` §5 (no public evaluation exists for competitors' AI)

## Inputs (fill in)
```
RELEASE:   version the answers are based on
SIZE:      e.g. 150 questions
```

## Task
1. Write questions in categories: direct lookup (district, DS and GN), comparison, aggregation (sum of children), definition and method, change over time (only where valid), and **unanswerable** (data doesn't exist) to test refusals.
2. Each item has: question, expected answer (value and unit, or "not available"), tolerance, `geography_id`, indicator, release and source citation.
3. Avoid sensitive framing (no "which ethnic group is…" rankings). Questions should be useful, neutral and factual.
4. A scoring harness: automatic for our MCP server (exact or within tolerance, plus citation present); a manual protocol for external assistants (record date, model and interface; don't automate against services whose terms forbid it).
5. Publish the set under CC BY 4.0 in the repository with a README; report results in `qa/ai-eval-{{date}}.md`.

## Constraints
- Expected answers come from the release, verified against the source for a sample.

## Verify (show real output)
Set statistics by category; harness run output on our MCP server.

## Deliverables
Evaluation set, harness, results report.

## Done when
We can state our AI accuracy with evidence and track it across releases.

Report using the format in `AGENTS.md`.
