# Gantry migration standard

Rules the `migration-reviewer` enforces on files in `migrations/`. Projects add
their own data rules (for example tenancy) in `.gantry/standards/migration.md`.

### MIG-3: Existing migrations are never edited
Only new files. (The G-MIGRATION gate also enforces this; the reviewer catches
it in diffs the gate didn't see, such as a rebase.)

### MIG-4: Changes that lock or rewrite a large table say so
Adding a column with a volatile default, changing a column type, adding a
NOT NULL without a default, or creating an index without CONCURRENTLY on a
table that may be large: the migration has a comment saying so and how it
will be run.

### MIG-5: Destructive changes are staged
Dropping a column or table, or renaming one, happens only after a previous
release stopped using it. A drop of something the current code still reads is HIGH.

### MIG-6: Data changes are separate from schema changes
A large backfill (`UPDATE` of existing rows) is its own migration, so it can be
run and retried on its own. A one-line default for a brand-new column is fine.

### MIG-7: Constraints match the data model
Money columns are integers or numeric, never floating point. Foreign keys exist
for references. Status columns have a CHECK or an enum.

## Severity
- CRITICAL: a change that can lose data, or that breaks a project data rule
  (tenancy, money) in a way that leaks or corrupts data.
- HIGH: an unannounced long lock on a large table; a drop the code still uses.
- MEDIUM: a missing constraint; a backfill mixed into a schema change.
- LOW: naming and ordering suggestions with a concrete risk named.
