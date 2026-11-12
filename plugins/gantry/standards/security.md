# Gantry security standard

Rules the `security-reviewer` enforces: authorization, injection, trust
boundaries, webhooks and callbacks, unsafe execution, request forgery.
Authentication, tokens, crypto, and secrets belong to `auth-crypto.md`.

### SEC-1: Every route checks permission for the specific resource
Being signed in is not permission. A route that loads a record by id must check
that the caller may see or change *that* record (owner, role, or company).
Violation:
    app.get("/expenses/:id", async (req) => getExpense(req.params.id));   // any user, any expense
Not a violation: a query that can only return the caller's rows (a WHERE on the
caller's id, or a row-level security policy the request is scoped to).

### SEC-2: Roles are checked on the server, from the authenticated user
Never from a header, body field, or query parameter the client controls.
Violation:
    if (req.headers["x-role"] === "finance") await pay(id);

### SEC-3: Outside data is validated before it reaches a query, path, command, URL, or template
Violation:
    db.query(`SELECT * FROM expenses ORDER BY ${req.query.sort}`);
    readFile(join(UPLOADS, req.params.name));          // "../../etc/passwd"
Not a violation: parameterized values (`$1`); identifiers chosen from a fixed allowlist.

### SEC-4: No shell commands built from outside data
Violation:
    exec(`convert ${req.body.file} out.png`);
Not a violation: `execFile("convert", [checkedPath, "out.png"])` after SEC-3 validation.

### SEC-5: Webhooks verify, reject replays, and are idempotent
A webhook handler (a) verifies the sender's signature over the raw request body,
(b) rejects timestamps older than five minutes, and (c) records each event id so
the same event twice has no extra effect. Missing any of the three is a finding.
The signature *comparison method* is auth-crypto's AC-2.

### SEC-6: Webhooks and callbacks never trust amounts or ids they could look up
Act on our own record of what was requested, found by an id we issued.
Violation:
    await markPaid(event.data.expenseId, event.data.amount);   // amount from the sender
Not a violation: ids we issued (sent in our request's metadata) that come back
inside a signed payload, used only to find our own record, with the action
taken from a fixed set of statuses and checked against that record's state.

### SEC-7: Any URL the server fetches is checked against an allowlist
Violation:
    const res = await fetch(req.body.receiptUrl);      // server-side request forgery

## Severity
- CRITICAL: one user or company can read or change another's data; an outsider
  can trigger an action (unsigned webhook, injection).
- HIGH: replay or double-processing of a money event; SSRF; a missing permission
  check that needs a valid account to exploit.
- MEDIUM: defense-in-depth gaps where another layer currently holds.
- LOW: hardening suggestions with a concrete risk named.
