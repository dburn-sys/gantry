# Gantry

Gantry is a Claude Code plugin. Hooks are Python 3.10+ in `hooks/`.

## Commands
- Tests: `python -m pytest hooks/tests -q`

## Hard rules
- MUST NOT add a Python dependency other than pytest (dev only).
  Hooks run on machines we don't control; stdlib only.
- MUST keep every hook's main() wrapped in run_hook so it fails open.
