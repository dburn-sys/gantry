# Changelog

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
