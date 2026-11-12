---
name: release
description: Release a new version of Gantry from this repository (maintainers).
disable-model-invocation: true
---

Run each step; stop at the first that fails and say why.

1. CI's test matrix is green on main (`gh run list --workflow test-matrix.yml --branch main --limit 1`).
2. For every reviewer, standard, or review-matrix file changed since the last tag
   (`git diff --name-only <last-tag>..HEAD`), run its test set:
   `python tests/reviewers/run_reviewer.py <reviewer>` (three runs each). Record
   misses and false alarms per reviewer.
3. Confirm the doctor passed on a fresh install on each OS (ask the user; it's
   done on throwaway machines or CI runners).
4. Pick the version from the commits since the last tag: any `feat!` or
   "BREAKING", or any new gate that is on by default: major. Any `feat`: minor.
   Otherwise: patch.
5. Write the CHANGELOG.md section: Added, Changed, Fixed. For every new or
   changed gate, say what it refuses and how to override it. Include the
   reviewer counts from step 2.
6. Set the version in plugins/gantry/.claude-plugin/plugin.json and in
   .claude-plugin/marketplace.json's metadata.
7. Show the user the changelog section and version. After they approve: commit
   through gantry:commit-gate, then tell them to tag `v<version>` and push. Never
   push tags or to main yourself.
