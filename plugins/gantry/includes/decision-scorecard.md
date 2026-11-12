# Decision scorecard

Use for every decision a sprint makes that the spec, its Sprint defaults, the
plan, the ADRs, and the architecture don't already answer. If one of those
answers it, cite it and don't score.

1. List the realistic options (usually two or three).
2. Score each option 1 to 5 on six lenses:
   - Fit: matches the spec, the ticket facts, and the sprint defaults.
   - Safety: protects data, money, and access.
   - Reversibility: easy to undo if wrong.
   - Consistency: matches ADRs, architecture rules, and code patterns.
   - Evidence: backed by something written down, not inferred.
   - Cost: little work now and later (5 = least).
3. Choose the highest total. Break ties in this order: security, correctness,
   maintainability, performance, speed.
4. Rate confidence 1 to 5:
   - 5: the spec or an ADR effectively answers it; the scores confirm it.
   - 3: reasonable options were close; a clear but modest margin.
   - 1: a guess between options that each have real downsides.
   **Confidence 1 is a hard stop, not a decision.**
5. Append it to the sprint log in exactly this form:

       ### D-<n>: <short title> (task T-<n>)
       Question: <one sentence>
       Options:
         A. <option>   Fit n  Safety n  Rev n  Cons n  Evid n  Cost n  = total
         B. ...
       Chosen: <letter>
       Why: <two sentences at most, citing what's written down>
       Confidence: <1-5>
