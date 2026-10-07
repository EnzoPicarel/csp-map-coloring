# Benchmark corrections

The original coursework files remain in their original folder. This portfolio
edition makes the following changes:

1. Each seed starts from a deep copy of the unmodified reference map. The old
   script created a copy but shuffled the previous trial's mutable map instead.
2. A local `random.Random(seed)` shuffles only the requested prefix; it does not
   affect global RNG state. All algorithms/repetitions share that order while
   receiving separate input copies.
3. Every non-null solution must cover exactly the variables, use allowed colors,
   and satisfy every edge. The old summary discarded returned solutions and
   passed an empty dictionary to a formatter that reported it as success.
4. Single-case and benchmark CLIs both default to shuffling 40 states. The old
   single-case script used 30 while the report/benchmark used 40.
5. Forward Checking passes a private domain copy into each branch, making failed
   recursion unable to change domains inherited by a sibling.
6. The runner retains per-run results and records mean, median and sample standard
   deviation of completed runtimes. An assignment budget is reported as
   `budget_exhausted`, not as a proof of unsatisfiability.
7. Input paths are independent of the working directory. Invalid/asymmetric
   adjacency, invalid solutions and unsupported counts raise explicit errors.

These changes alter trial orders, search bookkeeping and timing. The historical
coursework averages are not copied into the portfolio results. They must not be
compared as a before/after speed optimization on an identical experiment.
