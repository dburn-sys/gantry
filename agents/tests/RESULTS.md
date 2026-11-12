# Reviewer test results

Run with `RUNS=1 python agents/tests/run_reviewer.py <reviewer>`. Each line is a
single pass; the release checklist (Chapter 22) runs three.

| Reviewer | Planted | Clean | Misses | False alarms (final pass) |
| --- | --- | --- | --- | --- |
| typescript-reviewer | 9 | 6 | 0 | 0 |
| security-reviewer | 4 | 2 | 0 | 0 |
| auth-crypto-reviewer | 4 | 2 | 0 | 0 |
| dependency-reviewer | 4 | 2 | 0 | 0 |
| migration-reviewer | 4 | 2 | 0 | 0 |
| ai-reviewer | 4 | 2 | 0 | 0 |
| coverage-auditor | 4 | 2 | 0 | 0 |

## What tuning found

- **The runner itself.** Headless runs could not read `standards/` until the runner
  passed `--add-dir` for the plugin folder. Every case "missed" until then.
- **Weak clean examples.** Four of the first clean examples had real problems the
  reviewers were right about: a role check written as a denylist, a webhook that
  didn't check the payout's state, a new model feature with no eval set, and a
  duplicate-event test a plain state guard would also pass. Those were fixed in
  the examples, not by loosening the reviewers.
- **Standard wording.** SEC-6 needed a "not a violation" for ids we issued that come
  back signed. COV-2 needed to say the `[NEEDS-TRIAGE]` reference may sit on the
  line above, and that an accepted skip isn't a COV-1 finding either. AI-5 needed
  to say running evals is the commit gate's job.
- **Run-to-run variation.** Two clean cases passed one run and were flagged the next.
  Both traced to ambiguous wording, which is why each case should run three times.
- **Failed runs look like misses.** A pass made while the model was unavailable
  reported three misses per reviewer. If misses look evenly spread and implausible,
  check the raw output before tuning anything.
