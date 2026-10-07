"""Independent seeded trials; shared orders; validated per-run outcomes."""

import argparse
import copy
import csv
import hashlib
import json
import platform
import random
import statistics
from pathlib import Path

from functions import (
    SearchLimitExceeded, backtracking_search, backtracking_mrv,
    backtracking_mrv_forward_checking, valid_solution, validate_csp,
)

ROOT = Path(__file__).resolve().parent
ALGORITHMS = {
    'Backtracking': backtracking_search,
    'MRV': backtracking_mrv,
    'MRV + FC': backtracking_mrv_forward_checking,
}


def make_trial(csp, seed, shuffle_count):
    if not 0 <= shuffle_count <= len(csp['variables']):
        raise ValueError('shuffle_count must be between zero and the number of variables.')
    trial = copy.deepcopy(csp)
    prefix = trial['variables'][:shuffle_count]
    random.Random(seed).shuffle(prefix)
    trial['variables'][:shuffle_count] = prefix
    return trial


def benchmark(csp, seeds=range(10), repeats=3, shuffle_count=40,
              max_assignments=20_000_000):
    validate_csp(csp)
    if repeats < 1 or (max_assignments is not None and max_assignments < 1):
        raise ValueError('Repeats and assignment budget must be positive.')
    rows, solutions = [], []
    for seed in seeds:
        trial = make_trial(csp, seed, shuffle_count)
        order = json.dumps(trial['variables'], separators=(',', ':'))
        order_hash = hashlib.sha256(order.encode()).hexdigest()
        for repeat in range(repeats):
            for name, solver in ALGORITHMS.items():
                try:
                    solution, stats = solver(copy.deepcopy(trial), max_assignments=max_assignments)
                    valid = valid_solution(trial, solution)
                    if solution is not None and not valid:
                        raise RuntimeError(f'{name} returned an invalid assignment.')
                    status = 'solved' if valid else 'unsatisfiable'
                except SearchLimitExceeded as error:
                    solution, stats, valid, status = None, error.stats, False, 'budget_exhausted'
                rows.append({
                    'seed': seed, 'repeat': repeat, 'algorithm': name,
                    'order_sha256': order_hash, 'status': status,
                    'valid_solution': valid,
                    'assignments': stats.get('assignments', ''),
                    'backtracks': stats.get('backtracks', ''),
                    'runtime_ms': stats.get('runtime_ms', ''),
                })
                solutions.append({'seed': seed, 'repeat': repeat, 'algorithm': name,
                                  'variable_order': trial['variables'], 'solution': solution,
                                  'status': status})
        print(f'Completed seed {seed}', flush=True)
    return rows, solutions


def summarize(rows):
    summaries = []
    for name in ALGORITHMS:
        group = [r for r in rows if r['algorithm'] == name]
        complete = [r for r in group if r['status'] != 'budget_exhausted']
        times = [r['runtime_ms'] for r in complete]
        summaries.append({
            'algorithm': name, 'runs': len(group),
            'valid_solutions': sum(r['valid_solution'] for r in group),
            'unsatisfiable': sum(r['status'] == 'unsatisfiable' for r in group),
            'budget_exhausted': len(group)-len(complete),
            'mean_assignments': statistics.mean(r['assignments'] for r in complete) if complete else None,
            'mean_backtracks': statistics.mean(r['backtracks'] for r in complete) if complete else None,
            'mean_runtime_ms': statistics.mean(times) if times else None,
            'median_runtime_ms': statistics.median(times) if times else None,
            'stdev_runtime_ms': statistics.stdev(times) if len(times)>1 else 0.0 if times else None,
        })
    return summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT/'map_csp.json')
    parser.add_argument('--seeds', type=int, default=10, help='Seeds 0 through N-1.')
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--shuffle-count', type=int, default=40)
    parser.add_argument('--max-assignments', type=int, default=20_000_000)
    parser.add_argument('--output', type=Path, default=ROOT/'results')
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error('--seeds must be positive')
    csp = json.loads(args.data.read_text())
    rows, solutions = benchmark(csp, range(args.seeds), args.repeats,
                                args.shuffle_count, args.max_assignments)
    summary = summarize(rows)
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output/'benchmark_runs.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    (args.output/'solutions.json').write_text(json.dumps(solutions, indent=2)+'\n')
    (args.output/'benchmark_summary.json').write_text(json.dumps({
        'python': platform.python_version(), 'platform': platform.platform(),
        'data_sha256': hashlib.sha256(args.data.read_bytes()).hexdigest(),
        'seeds': list(range(args.seeds)), 'repeats': args.repeats,
        'shuffle_count': args.shuffle_count, 'max_assignments': args.max_assignments,
        'timing': 'Solver time after input validation; includes search bookkeeping.',
        'summary': summary,
    }, indent=2)+'\n')
    for row in summary:
        print(row)
    print(f'Written benchmark and validated assignments to {args.output}')


if __name__ == '__main__':
    main()
