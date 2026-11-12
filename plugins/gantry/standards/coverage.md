# Gantry coverage standard

Rules the `coverage-auditor` enforces: whether the tests in a change prove what
they claim.

### COV-1: Every obligation has a test that would fail without the behavior
Each OB-n or AC-n in the run's obligations table maps to a test whose assertion
checks that behavior. A test named for an obligation that asserts something
weaker (status 2xx, "is defined") is a finding.

### COV-2: No skipped or focused tests without a [NEEDS-TRIAGE] reference
`.skip`, `.only`, `xit`, `xdescribe`, `it.todo` added in the change are findings
unless the same line, the line above, or the run report cites `[NEEDS-TRIAGE]`
and a ticket. A skip with that reference is not a finding under any rule,
COV-1 included: the reference is how the team accepts the gap on purpose.

### COV-3: Test infrastructure changes are explained
Changes to the test command, test config, or where tests live are findings unless
the run report explains them.

### COV-4: A test must not mock the thing it claims to test
Violation:
    vi.mock("../src/webhooks/signature.js", () => ({ verifySignature: () => true }));
    it("rejects a bad signature", ...)

### COV-5: Expected values don't change alongside the code they test
A changed expected value in a test, in the same change as the code it tests, is
a finding unless the spec changed too.

## Severity
- CRITICAL: a test that can't fail, covering money, auth, or tenancy.
- HIGH: COV-4; an obligation with no real test; a removed or weakened assertion.
- MEDIUM: COV-2, COV-3, COV-5 elsewhere.
- LOW: a test that would be clearer or faster, with a concrete risk named.
