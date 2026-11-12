# Security and legal review: Gantry

Answers to write down before review. Replace the bracketed parts with your own.

| Question | Answer |
| --- | --- |
| What code and data are sent to the AI provider? | Whatever Claude Code sends during a session, under [company]'s agreement with the provider. Gantry adds its persona and the repo's `.gantry/context.md` to that context; its hooks send nothing anywhere. |
| Which outside services does Gantry talk to? | None from hooks (Python standard library only, no network calls). MCP servers such as GitHub are configured and allowlisted by [company]. |
| Where are secrets? | Never in Gantry's files. G-SECRET refuses them in file writes and commands; logs store only redacted previews. |
| What's in the logs, and for how long? | Committed with the repo, kept with its history: overrides, approvals, accepted findings, run reports, sprint logs, ADRs. Local and gitignored: evidence ledger, conformance records, metrics, probes. Telemetry, if enabled: counts and IDs, never code or prompts. |
| Who can change the rules? | The platform team, through reviewed PRs and ADRs in the marketplace repo. Architecture rules: code owners per repo. |
| Can a developer get past a gate? | Yes, with an override that names the gate, gives a reason, and is logged in a hash-chained file. Admins can bypass branch protection; the code host logs it and the platform team reviews monthly. |
| What does the plugin run on a developer's machine? | Python scripts from the installed plugin, as the developer's user, on Claude Code events. Source is in [company]'s marketplace repo. |
