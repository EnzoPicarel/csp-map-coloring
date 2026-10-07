# Verification record

Verified on 7 October 2026 with Python 3.12.3 using the standard library only.

## Correctness checks

Seven unit tests pass. They check partial/invalid assignments, satisfiable and
unsatisfiable instances, self-loops, empty graphs, asymmetric input rejection,
independent seeds, shared trial orders, explicit budget outcomes, and agreement
with exhaustive enumeration on 80 randomly generated six-variable graphs.
Every successful benchmark result is separately checked against the map.

## Recorded benchmark

```bash
python -m unittest discover -s tests -v
python tab_results.py --seeds 10 --repeats 3 --shuffle-count 40 --max-assignments 20000000
```

The recorded benchmark comprises ten independently generated variable orders
and three repetitions per algorithm/order: 90 runs, not 90 independent maps.
Each order shuffles a fresh copy of the first 40 reference variables and keeps
the final eight in their original order.

- Backtracking: 24 validated solutions, 6 budget-exhausted runs.
- MRV: 30 validated solutions, no exhausted budgets, no backtracks.
- MRV + FC: 30 validated solutions, no exhausted budgets, no backtracks.
- No run in this four-color map benchmark is reported as unsatisfiable.

`benchmark_runs.csv` retains every run, including counters and durations for
capped searches. `benchmark_summary.json` includes the dataset hash, platform,
Python version, configuration and descriptive timing statistics. The sample
assignment and tile-grid SVG come from a validated MRV solution for seed 0.

## Timing and outcome semantics

Assignments count attempted variable/color choices, including choices rejected
for inconsistency. Backtracks count recursive nodes whose color choices fail.
Solver timers exclude input validation but include bookkeeping and domain copies.

An exhausted assignment budget means satisfiability remains unknown for that
run. It never becomes a claim that no solution exists. Means, medians and sample
standard deviations summarize completed runs only, so the baseline's timing
distribution is censored and must not be ranked directly against uncensored
heuristic summaries. The three repetitions of each seed share the same search
order and deterministic count; they sample runtime variation only.

Timings depend on interpreter, hardware and other machine activity. This is a
local algorithm demonstration, not an isolated hardware-performance study.
Old report times used a different trial-order protocol and are not reused here.
