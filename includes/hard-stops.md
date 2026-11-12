# Hard stops (sprint MUST stop and wait for the user)

- Any decision about authentication, authorization, cryptography, secrets, or
  tenancy.
- Anything irreversible: deleting data, a migration that drops or rewrites
  columns, sending external messages or payments outside the sandbox.
- Any gate refusal that would need an override. The sprint never types override
  phrases; only the user does.
- An unresolved [CONFIRM-NN] that the spec, ADRs, and sprint defaults don't answer.
- Any change that a conformance review says needs an architecture rule to change
  (that needs an ADR, which needs a human).
- Any decision with confidence 1.
- Merging, or anything that writes to the default branch.
- An area the spec's Sprint defaults reserve for the user.

## Stop limits
- The same task fails review three times.
- More than 25 tasks, or more than the time limit the user gave.
- A senior-engineer author escalates further.

## How to stop
Append to the sprint log:

    ### S-<n>: <Hard stop | Stop limit> (<reason in two words>)
    <what is needed, the options if there are any, and where the sprint is>
    Waiting.

Set the log's Status line to `stopped`. Tell the user the same thing in the chat,
then wait. When they answer, record the answer under the stop, set Status back to
`running`, and continue.
