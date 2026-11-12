# Gantry auth and crypto standard

Rules the `auth-crypto-reviewer` enforces: authentication, sessions and tokens,
cryptographic primitives, key handling, TLS, and secrets in code. Who is allowed
to do what belongs to `security.md`.

## Banned primitives
Any use of these is CRITICAL. There is no debate about these rows.

| Rule | Banned | Use instead |
| --- | --- | --- |
| AC-2 | `===`, `==`, `Buffer.equals`, or `.compare` on secrets, signatures, tokens, or hashes | `crypto.timingSafeEqual` on equal-length buffers |
| AC-4 | MD5, SHA-1, SHA-256 (or any plain hash) for passwords | scrypt, argon2, or bcrypt, with a salt |
| AC-5 | `Math.random()` for tokens, ids, keys, nonces, or codes | `crypto.randomBytes`, `crypto.randomUUID` |
| AC-8 | `rejectUnauthorized: false`, `NODE_TLS_REJECT_UNAUTHORIZED=0` | Fix the certificate |

### AC-1: Tokens are signed and checked for expiry
A session or API token that isn't signed, or whose expiry isn't checked, is a finding.

### AC-3: Keys and secrets come from the environment or a secret store
Never a literal in source, a default value, or a test fixture that ships.
Violation:
    const key = process.env.SIGNING_KEY ?? "dev-secret";
Not a violation: a test file that generates a random key per run.

### AC-6: Secrets never reach logs, error responses, or URLs
Violation:
    logger.info({ headers: req.headers }, "webhook");   // logs the signature and API key

### AC-7: Only hashes of API keys are stored
Store a hash; show the key once.

## Severity
- CRITICAL: any banned primitive (AC-2, AC-4, AC-5, AC-8); a hard-coded secret.
- HIGH: a token without expiry or signature check; secrets in logs.
- MEDIUM: a weak but not banned choice (for example a short key length).
- LOW: hardening with a concrete risk named.
