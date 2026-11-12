# What was tested against a real Claude Code

When the companion repo was built, parts of this policy were installed as a
system `managed-settings.json` on a test machine, with Gantry 1.1.0 from a local
marketplace. That machine was itself under organization-managed settings, and by
default only one managed source applies per machine, so treat these results as a
starting point, and repeat them on your own staging machines (see README:
"Stage it").

| Chapter 23 attempt | Result on the test machine |
| --- | --- |
| 2. Load a modified copy with `--plugin-dir` | **Confirmed.** Claude Code refused to start: "--plugin-dir is disabled by your organization's managed settings (disableSideloadFlags)." |
| 3. A user hook that tampers | **Confirmed.** With `allowManagedHooksOnly`, a PreToolUse hook added to user settings did not run. |
| 1. Disable Gantry as a user | **Not confirmed.** In headless (`claude -p`) sessions on that machine, the managed marketplace wasn't registered and Gantry wasn't loaded by the managed setting at all, so whether managed `enabledPlugins` beats a user's disable couldn't be observed. Check it interactively, with `/plugin`, on a staging machine. |
| 4. A repo without `.gantry/` | **Confirmed in Gantry's tests** (`tests/hooks/test_required_mode.py`) with `GANTRY_REQUIRED=1` in the environment. Not confirmed end to end, for the same reason as attempt 1. |
| 5. Ask Claude to commit a secret | Covered by G-SECRET's tests since Chapter 10. |
| 6, 7. Outside Claude Code | Server-side: branch protection and required checks (`github/main-ruleset.json`). Not run against a live GitHub organization. |

One more thing the test turned up: a policy change reaches sessions that are
already running. When the test machine's settings changed, a Claude Code session
already open on it reloaded them and picked up Gantry mid-session. Plan rollouts
for that.
