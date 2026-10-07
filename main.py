"""Solve the same seeded map with all three search strategies."""
import argparse
import json
from pathlib import Path
from functions import SearchLimitExceeded, print_results, valid_solution
from tab_results import ALGORITHMS, make_trial


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path(__file__).with_name('map_csp.json'))
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--shuffle-count', type=int, default=40)
    parser.add_argument('--max-assignments', type=int, default=20_000_000)
    args = parser.parse_args()
    if args.max_assignments < 1:
        parser.error('--max-assignments must be positive')
    csp = make_trial(json.loads(args.data.read_text()), args.seed, args.shuffle_count)
    for name, solver in ALGORITHMS.items():
        try:
            solution, stats = solver(csp, args.max_assignments)
        except SearchLimitExceeded:
            print(f'{name}: assignment budget exhausted; satisfiability unknown.')
            continue
        if solution is not None and not valid_solution(csp, solution):
            raise RuntimeError(f'{name} returned an invalid assignment.')
        print_results(name, solution, stats)


if __name__ == '__main__':
    main()
