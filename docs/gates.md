# Gates

Every refusal starts with its gate ID. To get past one deliberately, type:
`override <ID> because <a reason of at least five words>`. The override is
logged and lets exactly one blocked action through within ten minutes.

A blocking review finding can be accepted, rather than fixed, only by a person:
`accept finding <n> because <a reason of at least five words>`.

| ID | Refuses | Chapter |
| --- | --- | --- |
| `G-MAIN` | Commits or pushes to main or master | 9 |
| `G-FORCE` | Force pushes, in any spelling | 9 |
| `G-SECRET` | Secrets in file writes or commands | 10 |
| `G-HARNESS` | Agent changes to Gantry's own files and records | 10 |
| `G-EVIDENCE` | Commits without a full passing test run of the current code | 11 |
| `G-SPEC` | Feature source without an approved spec | 12 |
| `G-FIX` | Fix source before a failing regression run | 13 |
| `G-CHORE` | Chores that touch source | 13 |
| `G-LANE` | Source on a branch with no lane, or moving a branch between lanes | 13 |
| `G-SPIKE` | Merging spike branches | 13 |
| `G-REFACTOR` | Refactors without a green baseline, or that change existing tests | 13 |
| `G-MIGRATION` | Edits to committed migrations | 14 |
| `G-FINDINGS` | Commits while a review finding has no disposition, or a CRITICAL or HIGH finding is neither fixed nor accepted by a person | 14, 18 |
| `G-SUBAGENT` | Subagents committing, pushing, merging, or rebasing | 18 |
| `G-ARCH` | Commits touching an architecture section without a CONFORMANT review of the current code | 19 |
