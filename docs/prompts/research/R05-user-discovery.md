# R05: Plan and synthesise user and customer discovery

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1+ | Research / Product | 1 | 2026-11-07 | active |

## When to use
Two modes: **plan**, before interviewing journalists, researchers, NGO analysts and potential paying clients; **synthesise**, after interviews, with the lead's notes.

## Read first
- `AGENTS.md`
- `docs/vision/vision-and-strategy.md` §5 (audiences)
- `docs/vision/organisation-and-business-model.md` §3 (revenue ladder hypotheses)
- `docs/ideas/opportunities-register.md`

## Inputs (fill in)
```
MODE:      plan | synthesise
SEGMENTS:  e.g. journalists, NGO M&E staff, market research firms, university researchers
NOTES:     (synthesise mode) path to the lead's interview notes (anonymised)
```

## Task
**Plan mode**
1. For each segment: hypotheses to test (from the revenue ladder and audiences), a screener (who qualifies) and a recruitment approach the lead can use.
2. A 30-minute interview guide focused on *current workflow and pain* (last time they needed sub-national data: what they did, how long it took, what went wrong), not on pitching. Willingness-to-pay questions about past spending, not hypotheticals.
3. A consent script and a note-taking template.
4. Save to `docs/research/user-research/plan-{{date}}.md`.

**Synthesise mode**
1. Code the notes into themes. Quote only anonymised, short excerpts.
2. Report which hypotheses were supported, contradicted or untested, and how strong the evidence is (number of interviews per segment).
3. Implications: roadmap changes, opportunities to promote or park, pricing signals.
4. Update `docs/ideas/opportunities-register.md` and propose decision-log entries where warranted.
5. Save to `docs/research/user-research/synthesis-{{date}}.md`.

## Constraints
- No real names or identifying details in the repository. Store raw notes outside Git if they are identifiable.
- Don't overstate: 3 interviews are a signal, not proof.

## Verify (show real output)
Each theme cites how many interviews it came from.

## Deliverables
Plan or synthesis document, plus register and decision-log proposals.

## Done when
The lead knows what to change, what to test next and with whom.

Report using the format in `AGENTS.md`.
