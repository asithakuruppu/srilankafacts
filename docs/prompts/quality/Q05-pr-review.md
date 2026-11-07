# Q05: Review another agent's pull request (for the lead)

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| any | Quality | 1 | 2026-11-07 | active |

## When to use
For every non-trivial PR written by an AI agent, run in a **separate session** from the one that wrote it. This gives the non-coding lead an independent, plain-language assessment.

## Read first
- `AGENTS.md`
- `docs/decisions/decision-log.md`
- The prompt the authoring agent was given (from the PR description)
- The PR description and the full diff

## Inputs (fill in)
```
PR:     number or branch
PROMPT: the prompt ID used (e.g. G02)
```

## Task
1. **Scope:** does the PR do what the prompt asked, no more, no less? Flag unrelated changes and new dependencies or services not in the architecture.
2. **Rules:** check against AGENTS.md golden rules (fabrication, provenance, raw immutability, rights, crosswalk joins, silent drops, labelling, secrets, outward-facing actions).
3. **Decisions:** any contradiction of Accepted decisions? Any implicit new decision that should be in the log?
4. **Evidence:** re-run the commands and tests the PR claims and compare outputs. Spot-check **5 data values** against their source locators. Report mismatches.
5. **Quality:** tests meaningful (not just present)? Edge cases (unmatched units, nulls, duplicates)? Docs updated?
6. **Risk:** what could go wrong after merge? Is it reversible?
7. Produce a verdict for the lead in plain language: **Approve / Approve with notes / Request changes**, the top 3 risks, questions for the author, and a list of what you could not verify.

## Constraints
- Do not merge, push to the PR branch or approve on GitHub. Report only.
- Be specific: file and line references, commands and outputs.

## Verify (show real output)
Re-run outputs; the 5 spot-check results.

## Deliverables
A review report (as a PR comment draft or a markdown file for the lead).

## Done when
The lead can decide to merge without reading code.

Report using the format in `AGENTS.md`.
