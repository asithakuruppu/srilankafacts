# M03: Write a new prompt for this collection

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| any | Docs | 1 | 2026-11-07 | active |

## When to use
When a task will recur and has no prompt, or a `draft` prompt needs refreshing because its stage has arrived.

## Read first
- `AGENTS.md`
- `docs/prompts/README.md` (conventions) and `docs/prompts/_template.md`
- Two existing prompts in the same workstream, as style references
- **The current repository state** in the area the prompt covers (code, catalogue, docs). Prompts must match reality, not the plan.

## Inputs (fill in)
```
TASK:        what the new prompt should accomplish
WORKSTREAM:  research | foundation | geography | data | web | content | quality | ops | ai | services | meta
EXISTING_ID: (if refreshing) the prompt to update
```

## Task
1. Inspect the repository to learn actual paths, commands, modules and conventions. Note anything in docs that no longer matches the code.
2. Write the prompt from the template: specific "Read first" paths; an Inputs block with placeholders; numbered, project-specific steps; constraints beyond AGENTS.md; verification requiring real output; deliverables; observable "Done when".
3. Avoid generic advice that would fit any project. Tie each step to Sri Lanka Facts' data, geography, rights or users.
4. Pick the next free ID in the workstream (never reuse retired IDs), or bump the version of EXISTING_ID and set status `active`.
5. Add or update the row in the `docs/prompts/README.md` index.
6. If docs and code disagree, list the discrepancies in the report for the lead.

## Constraints
- One prompt = one verifiable PR. Split larger tasks.

## Verify (show real output)
Every path referenced in the prompt exists (show a check), or is explicitly marked "to be created".

## Deliverables
New or updated prompt file and the index update.

## Done when
An agent with no prior context could run the prompt and produce a reviewable PR.

Report using the format in `AGENTS.md`.
