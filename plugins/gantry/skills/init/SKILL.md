---
name: init
description: Opt this repository into Gantry. Scouts the codebase, drafts the configuration, confirms what it couldn't tell, proves the test suite runs, and checks the install.
disable-model-invocation: true
---

## Phase 1: Scout
If `.gantry/context.md` already exists, say so, suggest /gantry:repair, and stop.
Dispatch three `gantry:scout` agents IN ONE MESSAGE, one question each:
1. How do tests and lint run? (package scripts, Makefiles, CI files, tox/pytest config)
2. What is the layout? (source, tests, docs, migrations, infrastructure, generated code)
3. What conventions and decisions exist? (ADRs, contributing guides, an existing CLAUDE.md)
**Exit when:** all three have reported.

## Phase 2: Synthesize
Draft `.gantry/context.md`:

    ---
    gantry: enabled
    project: <folder name>
    gantry_version: <the installed plugin's version, from ${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json>
    test_command: <the full suite>
    not_source: <comma list: tests, docs, config, generated folders, .gantry/, .github/, *.md ...>
    ---
    # Project state

    No open questions. No tasks in flight.

Draft the Gantry section of CLAUDE.md from ${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md
(and the other sections too, if the repo has no CLAUDE.md). Anything the
scouts disagreed about or didn't find becomes a [CONFIRM-NN].

## Phase 3: Confirm
Ask the [CONFIRM] questions ONE at a time, with the options the scouts found.
**Exit when:** none are left.

## Phase 4: Verify
Run the test command once, exactly as written in the draft.
**Exit when:** it passes. The evidence ledger now has its first entry.
**If it fails:** say so and stop. Gantry can't gate commits on a suite that's
already red; fixing it comes first, through the fix lane.

## Phase 5: Write and check
Write `.gantry/context.md`, `.gantry/.gitignore` (evidence.jsonl, unproven.log,
override-token.json, intent-samples.jsonl, conformance.jsonl, metrics.jsonl,
probe.jsonl, dev-mode.json), and the CLAUDE.md section. Run gantry:doctor and
show its result. Then say, in two sentences, that architecture conformance is
available when the team is ready (`.gantry/architecture/`, Chapter 19 of the
guide) and isn't turned on by init. Tell the user to commit `.gantry/` and
CLAUDE.md through gantry:commit-gate.

## Hard rules
- MUST NOT write architecture files. That's the team's decision, later.
- MUST NOT pick a test command the scouts disagreed about. Ask.
