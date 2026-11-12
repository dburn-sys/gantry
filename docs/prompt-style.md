# Gantry prompt style guide

Applies to commands, skills, agents, and hook messages.

1. **Say how binding each instruction is.** MUST, MUST NOT, SHOULD, MAY, only inside a "Hard
   rules" section. Never use: consider, try to, ideally, where possible, as appropriate.
2. **Lock terminology.** command = a `/gantry:` entry point; skill = a routine with phases;
   agent = a specialist in its own context; phase = one step of a skill; gate = a phase exit
   condition or a refusing hook; finding = one reported problem; severity = CRITICAL, HIGH,
   MEDIUM, LOW (not the same as blocking). Verbs: the user *invokes*, the orchestrator
   *routes*, a skill *dispatches*.
3. **Phases have "Exit when" and "If not".**
4. **Every external dependency has a failure branch.** Default: stop and report in one line;
   never change code, tests, or config to get around it.
5. **Examples over adjectives.**
6. **Fix the output format** when another agent or a script will read it.
7. **Only two placeholders:** `[CONFIRM-NN]` and `[NEEDS-TRIAGE]`.
8. **Give the reason, in one line.**
9. **Keep emphasis rare.** No all-caps sentences.
10. **Short, and load the rest on demand.**

## Pre-commit checklist for a prompt
1. Does every hard rule use MUST, MUST NOT, SHOULD, or MAY, only inside Hard rules?
2. Have I removed every soft word (consider, try to, ideally, as appropriate)?
3. Does every term match the terminology lock?
4. Does every phase have "Exit when" and "If not"?
5. Does every external dependency have a failure branch?
6. Is there an example wherever there's a format?
7. Is any output another agent reads in a fixed format?
8. Are the only placeholders [CONFIRM-NN] and [NEEDS-TRIAGE]?
9. Does each hard rule carry a one-line reason?
10. Have I run the four pressure tests (urgency, authority, ambiguity, broken environment)?
