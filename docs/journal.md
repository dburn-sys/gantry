# Shortcut journal

Things Claude did without being asked, or did differently from what we wanted. Every Gantry
requirement should trace back to an entry here.

- Ch 1: Vague prompt -> Claude picked the whole stack and added extra packages.
- Ch 1: Rules I type in chat only last as long as the conversation remembers them.
- Ch 1: Nobody told Claude how to store money. It guessed.
- Ch 1: Asked Claude to delete the tests. Only thing guaranteed to stop it: me, clicking No.
- Ch 2: CLAUDE.md fixes forgetting. A pushy request can still override it.
- Ch 2: Settings deny rules hold even when Claude is convinced.
- Ch 2: Deny rules match command text, not meaning. "+main", "--force-with-lease",
  and "git -c x push" all got past "deny git push --force".
- Ch 3: Asked for a PRD without an interview. Got a confident document about someone else's
  project. Interview first, every time.
- Ch 4: Rules ran out when the tests couldn't run, and Claude mocked the database. Principles
  decide the cases rules don't cover.
- Ch 5 (needs code): running only part of the suite; editing after the last test run;
  committing to main when told to; force pushing with syntax deny rules miss.
