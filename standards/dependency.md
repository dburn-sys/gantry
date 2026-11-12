# Gantry dependency standard

Rules the `dependency-reviewer` enforces on new and changed dependencies.

### DEP-1: Every new dependency has a stated reason
The run report or PR says why the standard library and existing dependencies
aren't enough. A new entry in `dependencies` or `devDependencies` with no reason
is a finding.

### DEP-2: No install scripts without explicit approval
`preinstall`, `install`, and `postinstall` run code on every developer's machine
and in CI. A new dependency that declares one (visible in the lockfile as
`"hasInstallScript": true`, or on its registry page) is a finding unless the run
report approves it by name.

### DEP-3: Licenses are on the allowlist
Allowed: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, 0BSD. Anything else,
including no license, is a finding. A project can extend the list in
`.gantry/standards/dependency.md`.

### DEP-4: Versions are pinned by the lockfile
A dependency change without a matching lockfile change is a finding. So is a
version range of `*` or `latest`.

### DEP-5: Names are checked for near-misses
A name one or two characters from a popular package (`expresss`, `lodahs`,
`fastfy`) is CRITICAL until shown to be the intended package.

### DEP-6: Container base images are pinned
`FROM node:latest` or an untagged image is a finding. Use a version tag, ideally a digest.

## Checking
You may use WebFetch on https://registry.npmjs.org/<name> to check maintainers,
license, release history, and install scripts. If a fetch fails, say "couldn't
verify" for that check. Never guess.

## Severity
- CRITICAL: a likely typosquat; an install script from an unknown publisher.
- HIGH: a disallowed or missing license; an unapproved install script.
- MEDIUM: no stated reason; an unpinned version or base image.
- LOW: a dependency that duplicates one already present.
