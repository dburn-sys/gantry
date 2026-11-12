# Gantry (companion repo)

The harness from *Gantry: Building an Agent Harness for Claude Code*, built chapter
by chapter. Each chapter's checkpoint is a git tag (`ch03` to `ch24`); releases are
`v<version>` tags.

From Chapter 22 this repository is a Claude Code plugin marketplace:

```text
.claude-plugin/marketplace.json   the catalog (marketplace name: gantry-tools)
plugins/gantry/                   the plugin: what users install
docs/                             PRD, principles, ADRs, gates
tests/hooks/                      pytest suite for the hooks
tests/reviewers/                  reviewer test sets (run with claude -p)
ci/gantry_check.py                paper-trail check for project CI
```

Install it:

```text
/plugin marketplace add <owner>/gantry
/plugin install gantry@gantry-tools
```

Develop it: `python -m pytest tests/hooks -q`, and load your working copy with
`claude --plugin-dir plugins/gantry`.

Before Chapter 22, the plugin was the repository root: check out an earlier tag
and use `claude --plugin-dir <path-to-gantry>`.
