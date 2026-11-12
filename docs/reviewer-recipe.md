# The reviewer recipe

Every Gantry reviewer is built in seven steps. Each produces a file or a line.

1. **Write the standard first.** `standards/<name>.md`: rules with an ID, a
   one-line statement, a reason, a violation, and "not a violation" examples.
   Projects add their own rules in `.gantry/standards/<name>.md`.
2. **Draw the scope boundary.** What this reviewer owns, and which reviewer owns
   everything else. Out-of-scope observations go under "Noticed, out of scope".
3. **Decide when it's dispatched.** Paths or file types. These become the
   reviewer's row in the review matrix (Chapter 17).
4. **Minimal tools.** Read, Grep, Glob. A reviewer never changes anything.
5. **A severity map for this standpoint.** Examples of CRITICAL, HIGH, MEDIUM,
   and LOW in this reviewer's domain, plus "never a finding".
6. **The output contract.** Findings table with a Rule column, "Noticed, out of
   scope", and a PASS or BLOCK verdict. No rule, no finding.
7. **Test it with planted bugs.** `agents/tests/<name>/planted/` (one diff per
   rule, named `<rule>-<slug>.diff`) and `clean/` (tempting but correct changes).
   Run `python agents/tests/run_reviewer.py <name>`; every case runs three times.
   Ship at zero misses and zero false alarms.

Run the test set whenever the reviewer's prompt or standard changes, and before
every release. It costs model time, so it isn't part of `pytest`.
