# Gantry TypeScript standard

Rules the `typescript-reviewer` enforces. Every finding cites one rule ID.
A project can add rules in its own `.gantry/standards/typescript.md`.

Never a finding under this standard: anything `tsc --strict` or the linter
already enforces, naming, formatting, or function length.

### TS-1: No `any` or type assertions on data from outside the process
Requests, files, environment variables, and API responses are untrusted until
parsed. `any` or `as X` turns off the checks exactly where they matter.
Violation:
    const body = req.body as Expense;
    await saveExpense(body.amount);
Not a violation:
    const LANES = ["feat", "fix"] as const;   // a literal, not external data
    const el = document.getElementById("x") as HTMLInputElement;  // DOM, not external data

### TS-2: `catch` binds `unknown` and narrows before use
Anything can be thrown. Reading `.message` from an unnarrowed error is a guess.
Violation:
    } catch (err: any) { log(err.message); }
Not a violation:
    } catch (err) { if (err instanceof TransitionError) ... ; throw err; }

### TS-3: Every promise is awaited, returned, or explicitly handled
A floating promise's errors vanish, and the code after it runs before it finishes.
Violation:
    saveAudit(expense);          // returns a Promise, ignored
    return reply.send(expense);
Not a violation:
    void warmCache().catch(logError);   // explicitly handled

### TS-4: No non-null assertions (`!`) on values that can really be null
`!` silences the compiler; it doesn't make the value exist.
Violation:
    const row = rows[0]!;        // the query can return no rows
    return toApi(row);
Not a violation:
    req.user!.id inside a route registered behind requireUser   // set by the preHandler

### TS-5: A catch on a write path rethrows or records the failure
Swallowing a failed write makes the caller believe it worked.
A catch that rethrows is never a TS-5 violation, whatever else it does
(logging, wrapping, cleanup).
Violation:
    try { await db.query("UPDATE ...") } catch { /* ignore */ }
    return { ok: true };
Not a violation:
    } catch (err) { logger.error(err); throw err; }

### TS-6: Unions that represent states are handled exhaustively
When a new state is added, every switch over the union should fail to compile
until it handles it.
Violation:
    switch (status) {
      case "submitted": ...; case "approved": ...;
      default: return "unknown";   // hides "rejected" and "paid"
    }
Not a violation:
    default: { const never: never = status; throw new Error(never); }

### TS-7: (project rules go in the project's standard)
Reserved for project rules. See the project's `.gantry/standards/typescript.md`.

### TS-8 (React): Hooks only at the top level
Hooks called conditionally or in loops run in a different order between
renders, and React mixes up their state.
Violation:
    if (!expense) return null;
    const [open, setOpen] = useState(false);

### TS-9 (React): Dependency arrays list every value the callback reads
A missing dependency means the effect or memo uses a stale value.
Missing state, props, and values derived from either all count.
Violation (missing state):
    const [filter, setFilter] = useState("all");
    useEffect(() => { load(filter); }, []);
Violation (missing prop):
    function List({ companyId }: Props) {
      useEffect(() => { fetchExpenses(companyId); }, []);
    }
