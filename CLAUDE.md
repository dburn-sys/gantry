# Gantry

This repository is a Claude Code plugin marketplace. The plugin itself is in
`plugins/gantry/`; everything outside that folder (docs, tests, CI) is for
maintainers and is never installed on users' machines.

## Commands
- Hook tests: `python -m pytest tests/hooks -q`
- Reviewer test sets (cost model time): `python tests/reviewers/run_reviewer.py <reviewer>`
- Validate: `claude plugin validate plugins/gantry`

## Hard rules
- MUST NOT add a Python dependency other than pytest (dev only).
  Hooks run on machines we don't control; stdlib only.
- MUST keep every hook's main() wrapped in run_hook so it fails open.
- Hook scripts run through hooks/_launcher.py, which MUST stay valid in
  Python 3.6 syntax so old interpreters can report that they're too old.
