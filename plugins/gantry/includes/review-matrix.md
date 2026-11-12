# Review matrix

The single source of truth for which reviewers see a change. The commit gate,
`/gantry:review`, the PR command, and the sprint runner all read this file.
Never copy the table into a skill.

A project can add rows in `.gantry/review-matrix.md`. Its rows are added to
these; they never remove one.

| Reviewer | Dispatched when the change touches |
| --- | --- |
| code-reviewer | any source change (always) |
| typescript-reviewer | *.ts, *.tsx, tsconfig*.json |
| security-reviewer | src/routes/**, src/app.ts, src/webhooks/**, src/integrations/**, middleware, .github/**, Dockerfile |
| auth-crypto-reviewer | src/auth/**; any file importing crypto; env vars named *KEY*, *SECRET*, *TOKEN* |
| dependency-reviewer | package.json, package-lock.json, Dockerfile FROM lines |
| migration-reviewer | migrations/** |
| ai-reviewer | src/ai/**; any file importing a model provider SDK or calling a model API |
| coverage-auditor | any source or test change |
