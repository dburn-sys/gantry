# Monthly metrics pack (template)

One page for leadership. Every number comes from something Gantry already records.

## Adoption
- Active repos initialized: <n> of <n> (<%>)
- Merged PRs with a Gantry run report: <%> (the rest are labeled no-gantry-run)

## Quality
- Findings caught before merge, by severity: CRITICAL <n>, HIGH <n>, MEDIUM <n>, LOW <n>
- By reviewer: <top five>
- Escapes: production defects a Gantry reviewer should have caught: <n>, with links

## Friction
- Blocking denials per developer per week: <n>
- Override rate by gate: <top five, with the most common reason for each>
- Median time from first commit attempt to green: <minutes>

## Cost
- Model usage per run, by tier and by reviewer (Claude Code telemetry): <table>

## Left out on purpose
Lines of code written by AI, number of agent invocations, and "time saved"
estimates. They're easy to produce and say very little.
