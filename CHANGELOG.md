# Changelog

## 1.2.0 (2026-07-20)

### Added
- Warn-only mode: gates listed in `GANTRY_GATES_WARN` (or `*` for all) allow the
  action, say what they would have refused, and record a `would_deny` metric.
  For introducing gates in waves (docs/rollout/checklist.md).
- `/gantry:init` rewritten: three read-only scout agents, a synthesized
  `.gantry/context.md` and CLAUDE.md section, [CONFIRM] questions, a test run
  that must pass, and the doctor. Never writes architecture files.
- `templates/CLAUDE.md`: the repo contract every opted-in repo shares.
- `gantry_version` in `.gantry/context.md`, a session-start note when the
  installed Gantry is newer, and `/gantry:repair` to catch up.
- docs/rollout/: the rollout checklist with the waves as `GANTRY_GATES_WARN`
  values, security and legal answers, and a monthly metrics pack template.

## 1.1.0 (2026-07-08)

### Added
- Required mode (ADR-0010 in examples/brightwater): with `GANTRY_REQUIRED=1`
  (set through managed settings), a git repository without `.gantry/` is
  uninitialized, not dormant. Source writes and commits are refused with
  `[G-INIT]` until `/gantry:init` runs. Overridable; before init, override
  records live in `.git/gantry/`. Without the variable nothing changes.
- `gantry-check --base <ref>` reports a PR with no run report as
  `no-gantry-run` (written to `$GITHUB_OUTPUT`). It never fails a PR for it.
- `examples/brightwater/`: a managed policy, branch ruleset, CODEOWNERS, a CI
  reviewers workflow for `no-gantry-run` PRs, three ADRs, and what was tested.

### Gates
- `G-INIT`: in required mode, refuses source writes and commits in a repository
  without `.gantry/`. Override: `override G-INIT because <reason>`.

## 1.0.0 (2026-07-01)

The first release from the marketplace layout. Gantry is installed with
`/plugin marketplace add <owner>/gantry` and `/plugin install gantry@gantry-tools`.

### Added
- Marketplace layout: the plugin lives in `plugins/gantry/`; docs, tests, and CI
  stay outside it and aren't installed.
- `/gantry:doctor`: checks Python, git, opt-in, hash chains, and architecture, then
  fires a live probe through the Bash hook. Reports Gantry loaded twice.
- Hook launcher: on Python older than 3.10, every hook prints a warning that
  Gantry is not enforcing, instead of failing silently.
- Status line (`/gantry:statusline install`): branch, test evidence, open
  findings, overrides, unproven commits.
- `/gantry:stats` and `.gantry/metrics.jsonl`: denials and overrides by gate.
- Maintainer dev mode: `GANTRY_DEV=1` plus `gantry dev on because <reason>`
  allows edits to the plugin's own files for one session. Logged as an override.
- Session start reports when the doctor hasn't run in this repository, or not
  in the last week.
- Test matrix: Linux, macOS, Windows on Python 3.10 to 3.13; fail-open tests for
  every hook; the launcher checked on Python 3.8.

### Gates in this release
Every refusal starts with its ID; type `override <ID> because <reason>` to pass
one once. `G-MAIN`, `G-FORCE`, `G-SECRET`, `G-HARNESS`, `G-EVIDENCE`, `G-SPEC`,
`G-FIX`, `G-CHORE`, `G-LANE`, `G-SPIKE`, `G-REFACTOR`, `G-MIGRATION`,
`G-FINDINGS`, `G-SUBAGENT`, `G-ARCH`, `G-PR`, `G-MERGE`. See `docs/gates.md`.

### Reviewer test sets
All twelve reviewers: 0 misses, 0 false alarms on their test sets (66 cases,
one run each; see `tests/reviewers/RESULTS.md`).

## 0.x
Chapters 3 to 21 of the book; one tag per chapter (`ch03` to `ch21`).
