import copy
import itertools
import random
import unittest
from functions import SearchLimitExceeded, valid_solution, validate_csp
from tab_results import ALGORITHMS, benchmark, make_trial, summarize


def graph(variables, edges, colors):
    neighbors = {v: [] for v in variables}
    for a, b in edges:
        neighbors[a].append(b)
        if a != b:
            neighbors[b].append(a)
    return {'variables': variables, 'neighbors': neighbors, 'colors': colors}


class SearchTests(unittest.TestCase):
    def test_invalid_and_partial_assignments(self):
        csp = graph(['a', 'b'], [('a', 'b')], ['red','blue'])
        for solution in [None, {}, {'a':'red'}, {'a':'red','b':'red'}, {'a':'green','b':'blue'}]:
            self.assertFalse(valid_solution(csp, solution))
        self.assertTrue(valid_solution(csp, {'a':'red','b':'blue'}))

    def test_satisfiable_unsatisfiable_and_self_loop(self):
        for csp, expected in [
            (graph(['a','b','c'], [('a','b'),('b','c')], [0,1]), True),
            (graph(['a','b','c'], [('a','b'),('b','c'),('c','a')], [0,1]), False),
            (graph(['a'], [('a','a')], [0,1]), False),
            (graph([], [], []), True),
        ]:
            for solver in ALGORITHMS.values():
                original = copy.deepcopy(csp)
                solution, _ = solver(csp)
                self.assertEqual(solution is not None, expected)
                if expected:self.assertTrue(valid_solution(csp, solution))
                self.assertEqual(csp, original)

    def test_independent_seeded_orders_and_shared_trials(self):
        csp = graph(list('abcdef'), [], [0,1])
        original = copy.deepcopy(csp)
        first = make_trial(csp, 3, 4)
        make_trial(csp, 7, 4)
        self.assertEqual(first, make_trial(csp, 3, 4))
        self.assertEqual(csp, original)
        self.assertEqual(first['variables'][4:], csp['variables'][4:])
        rows, _ = benchmark(csp, [0,1], 2, 4)
        for seed in [0,1]:
            self.assertEqual(len({r['order_sha256'] for r in rows if r['seed']==seed}),1)

    def test_failure_is_not_reported_as_success(self):
        csp = graph(['a','b','c'], [('a','b'),('b','c'),('c','a')], [0,1])
        rows, _ = benchmark(csp, [0], 1, 3)
        self.assertTrue(all(r['status']=='unsatisfiable' and not r['valid_solution'] for r in rows))
        self.assertTrue(all(r['valid_solutions']==0 for r in summarize(rows)))

    def test_budget_is_unknown_not_unsatisfiable(self):
        csp = graph(['a','b'], [('a','b')], [0,1])
        for solver in ALGORITHMS.values():
            with self.assertRaises(SearchLimitExceeded):solver(csp, max_assignments=1)
        rows, _ = benchmark(csp, [0], 1, 2, max_assignments=1)
        self.assertTrue(all(r['status']=='budget_exhausted' for r in rows))
        self.assertTrue(all(r['unsatisfiable']==0 for r in summarize(rows)))

    def test_against_exhaustive_search(self):
        rng = random.Random(8)
        for _ in range(80):
            edges=[e for e in itertools.combinations(range(6),2) if rng.random()<.45]
            csp=graph(list(range(6)),edges,[0,1,2])
            expected=any(valid_solution(csp,dict(zip(csp['variables'],values)))
                         for values in itertools.product(csp['colors'],repeat=6))
            for solver in ALGORITHMS.values():
                solution,_=solver(csp)
                self.assertEqual(solution is not None,expected)
                if solution is not None:self.assertTrue(valid_solution(csp,solution))

    def test_reject_asymmetric_map(self):
        with self.assertRaises(ValueError):
            validate_csp({'variables':['a','b'],'colors':[0], 'neighbors':{'a':['b'],'b':[]}})


if __name__ == '__main__':unittest.main()
