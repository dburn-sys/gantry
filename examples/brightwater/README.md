# Brightwater: making Gantry the only way in (Chapter 23)

A worked example of a company rollout. Brightwater forks Gantry into its own
marketplace repo, `brightwater/claude-plugins`, and enforces it in three layers.

| Layer | What | Files here |
| --- | --- | --- |
| 1. Managed settings | Gantry installed and enabled for everyone; no sideloading; only managed hooks; GANTRY_REQUIRED | `policy/managed-settings.json` |
| 2. Every repo in scope | Gantry's required mode: no `.gantry/` means [G-INIT], not dormant | (in the plugin since 1.1.0) and `docs/decisions/0010-gantry-required-mode.md` |
| 3. Server-side backstops | Branch protection, required checks, code owners, CI reviewers for PRs that skipped Gantry | `github/`, `workflows/` |

Decisions, with reasons: `docs/decisions/0010` to `0012`.

## Rolling out the policy
1. Validate it in CI: `python -m json.tool policy/managed-settings.json`. A file
   that isn't valid JSON stops Claude Code from starting for everyone who gets it.
2. Stage it: deliver the candidate to the platform team's machines first, through
   a source that takes priority there, and check `/status` shows it in effect.
3. Write the rollback runbook before you need it: which setting, who can change
   it, and how long it takes to reach machines.

## What was checked against a real Claude Code
When the companion repo was built, this policy's core was installed as a system
`managed-settings.json` on a test machine, with Gantry from a local marketplace:
see `TESTED.md`.
