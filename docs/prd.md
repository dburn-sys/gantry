# Gantry PRD

## 1. Problem
Claude Code writes good code but follows no process unless told to, and forgets what it is
told. The journal (docs/journal.md) records the failures: unrequested dependencies, guessed
requirements, rules that fade, tests skipped under pressure, and actions on shared state
(commits, pushes) that nothing checks.

## 2. Users
Developers using Claude Code on a shared codebase. First a single developer; later a team with
mixed Claude Code experience who must be able to install and use Gantry without hand-holding.

## 3. Goals
- G1. No untested code reaches a commit.
- G2. No secret reaches a tracked file or a command line.
- G3. Feature work starts from a written, human-approved spec.
- G4. Every skipped rule is deliberate, attributed, and recorded.
- G5. Gantry never stops a developer because Gantry itself is broken.

## 4. Non-goals
- Gantry does not replace CI. Anything checked locally should also be checked on the server.
- Gantry does not replace human code review on pull requests.
- Gantry does not support coding agents other than Claude Code.
- Gantry does not try to make Claude write better code. It makes Claude follow a better process.

## 5. Requirements
- G-1  MUST refuse a commit when code has changed since the last passing test run. (Journal ch1)
- G-2  MUST refuse commits and pushes directly to main. (Journal ch2)
- G-3  MUST block secrets from being written to tracked files.
- G-4  MUST require an approved spec before feature code is written. (Journal ch1)
- G-5  MUST let a developer bypass any rule deliberately, and MUST record every bypass.
- G-6  MUST do nothing in a repo that hasn't opted in.
- G-7  MUST NOT block the developer when Gantry itself fails; a broken check warns and allows.
- G-8  SHOULD send changes to specialist reviewers based on which files changed.
- G-9  SHOULD keep a readable record of decisions and why they were made.
- G-10 MUST work on Windows, macOS, and Linux.

## 6. Success measures
- Commits with no passing test run on record: zero, outside recorded overrides.
- Overrides per week, with reasons, visible to the team.
- Time from opening a repo to first gated commit for a new user: under 15 minutes.

## 7. Risks
- A broken hook could block every commit for every developer (mitigated by G-7).
- Gates that are too strict get disabled or worked around.

## 8. Open questions
- [CONFIRM-01] Where should override records live long term: repo, or a central service?
