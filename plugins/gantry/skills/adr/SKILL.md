---
name: adr
description: Record an architecture decision as a numbered ADR in .gantry/decisions/, through a one-question-at-a-time interview.
disable-model-invocation: true
argument-hint: <short decision name>
---

## Phase 1: Interview
Ask ONE question at a time to fill in: the context that forced the decision, the
decision itself, the alternatives considered and why each was rejected, the
consequences, and the risks being accepted. Ask who decided.
**Exit when:** every section could be written without guessing.

## Phase 2: Write
Write `.gantry/decisions/NNNN-<slug>.md`, where NNNN is the next number, with:

    ---
    status: accepted
    date: <today>
    title: <one line>
    decided-by: <the name the user gave>
    supersedes: none
    ---
    ## Context
    ## Decision
    ## Alternatives considered
    ## Consequences
    ## Risks

## Hard rules
- MUST NOT write an ADR as the agent's own decision. Every ADR names the human
  who decided.
- MUST NOT edit an accepted ADR. To change a decision, write a new ADR with
  `supersedes:` pointing at the old one, and change only the old one's status
  line to `superseded`.
