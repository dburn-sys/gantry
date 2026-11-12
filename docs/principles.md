# Gantry principles

Every rule in Gantry traces back to one of these. When rules conflict, use the priority order
at the end.

1. **Route, don't implement.** The orchestrator sends each kind of work to the routine or
   specialist that owns it. Why: one long generalist session produced the journal (PRD G-8).
2. **Force the agent, never trap the user.** Gates make Claude follow the process; a human can
   always get past one deliberately, with a record (G-5).
3. **A check that can't run warns and lets the work through.** A gate that fails refuses; a
   gate that can't run warns in one line, allows, and marks its record unproven (G-7).
4. **Ask, don't guess.** Unknowns become numbered `[CONFIRM-NN]` questions (journal ch1).
5. **Evidence over claims.** Nothing is done because someone says so; it is done when a record
   shows it (G-1).
6. **Surface conflicts, never reconcile them silently.** Show both sides; if a choice must be
   made, use the priority order below.
7. **Dormant until invited.** Gantry does nothing in a repository without a `.gantry/` folder
   (G-6).

## When principles conflict
1. Security and audit-trail integrity
2. Correctness and data integrity
3. Maintainability and reviewability
4. Performance
5. Developer speed
