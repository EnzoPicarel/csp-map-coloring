import copy
import time


class SearchLimitExceeded(RuntimeError):
    """The search budget ended before satisfiability could be decided."""

    def __init__(self, stats):
        self.stats = {key: value for key, value in stats.items() if not key.startswith('_')}
        self.stats['runtime_ms'] = (time.perf_counter() - stats['_start_time']) * 1000
        super().__init__(f"Assignment budget of {stats['max_assignments']} exhausted.")


def validate_csp(csp):
    """Validate a finite undirected graph-coloring problem."""
    variables, colors, neighbors = csp['variables'], csp['colors'], csp['neighbors']
    if len(set(variables)) != len(variables) or len(set(colors)) != len(colors):
        raise ValueError('Variables and colors must be unique.')
    if set(neighbors) != set(variables):
        raise ValueError('Every variable needs exactly one neighbor list.')
    for var, adjacent in neighbors.items():
        if len(set(adjacent)) != len(adjacent):
            raise ValueError('Neighbor lists must not contain duplicates.')
        for other in adjacent:
            if other not in neighbors or var not in neighbors[other]:
                raise ValueError('Edges must connect known variables symmetrically.')


def valid_solution(csp, solution):
    """Require all variables, allowed colors, and every adjacency constraint."""
    return (isinstance(solution, dict)
            and set(solution) == set(csp['variables'])
            and all(value in csp['colors'] for value in solution.values())
            and all(solution[var] != solution[other]
                    for var in csp['variables'] for other in csp['neighbors'][var]))


def _record_attempt(stats):
    limit = stats.get('max_assignments')
    if limit is not None and stats['assignments'] >= limit:
        raise SearchLimitExceeded(stats)
    stats['assignments'] += 1

def backtracking_search(csp, max_assignments=None):
    validate_csp(csp)
    stats = {"assignments": 0, "backtracks": 0, "max_assignments": max_assignments}
    start_time = time.perf_counter()
    stats['_start_time'] = start_time
    solution = recursive_backtracking({}, csp, stats)
    end_time = time.perf_counter()
    stats["runtime_ms"] = (end_time - start_time) * 1000
    return solution, stats

def recursive_backtracking(assignment, csp, stats):
    if len(assignment) == len(csp["variables"]):
        return assignment

    # select an unassigned variable
    var = select_unassigned_variable(assignment, csp)
    # try each value in that variable’s domain
    for value in order_domain_values(var, assignment, csp):
        _record_attempt(stats)
        if is_consistent(var, value, assignment, csp):
            assignment[var] = value
            result = recursive_backtracking(assignment, csp, stats)
            if result is not None:
                return result
            del assignment[var]
    # return failure so that the caller backtracks
    stats["backtracks"] += 1
    return None

def select_unassigned_variable(assignment, csp):
    for var in csp["variables"]:
        if var not in assignment:
            return var
    return None

def order_domain_values(var, assignment, csp):
    return csp["colors"]

# Check if the value assignment is consistent with the constraints
def is_consistent(var, value, assignment, csp):
    if var in csp['neighbors'][var]:
        return False
    for neighbor in csp["neighbors"][var]:
        if neighbor in assignment and assignment[neighbor] == value:
            return False
    return True

def backtracking_mrv(csp, max_assignments=None):
    validate_csp(csp)
    stats = {"assignments": 0, "backtracks": 0, "max_assignments": max_assignments}
    start_time = time.perf_counter()
    stats['_start_time'] = start_time
    solution = recursive_backtracking_mrv({}, csp, stats)
    end_time = time.perf_counter()
    stats["runtime_ms"] = (end_time - start_time) * 1000
    return solution, stats

def recursive_backtracking_mrv(assignment, csp, stats):
    if len(assignment) == len(csp["variables"]):
        return assignment

    # select an unassigned variable using MRV heuristic
    var = select_unassigned_variable_mrv(assignment, csp)
    # try each value in that variable’s domain
    for value in order_domain_values(var, assignment, csp):
        _record_attempt(stats)
        if is_consistent(var, value, assignment, csp):
            assignment[var] = value
            result = recursive_backtracking_mrv(assignment, csp, stats)
            if result is not None:
                return result
            del assignment[var]
    # return failure so that the caller backtracks
    stats["backtracks"] += 1
    return None

def select_unassigned_variable_mrv(assignment, csp):
    best_var = None
    min_remaining_values = float('inf')
    for var in csp["variables"]:
        if var not in assignment:
            neighbor_colors = []

            # Check the colors assigned to the neighbors of the variable
            for neighbor in csp["neighbors"][var]:
                if neighbor in assignment:
                    neighbor_colors.append(assignment[neighbor])

            # Count the remaining values in the domain
            remaining_values = 0
            for color in csp["colors"]:
                if color not in neighbor_colors:
                    remaining_values += 1

            # Update the best variable
            if remaining_values < min_remaining_values:
                min_remaining_values = remaining_values
                best_var = var
    return best_var

def backtracking_mrv_forward_checking(csp, max_assignments=None):
    validate_csp(csp)
    stats = {"assignments": 0, "backtracks": 0, "max_assignments": max_assignments}
    start_time = time.perf_counter()
    stats['_start_time'] = start_time
    current_domains = {var: list(csp["colors"]) for var in csp["variables"]}
    solution = recursive_backtracking_mrv_forward_checking({}, csp, stats, current_domains)
    end_time = time.perf_counter()
    stats["runtime_ms"] = (end_time - start_time) * 1000
    return solution, stats

def recursive_backtracking_mrv_forward_checking(assignment, csp, stats, current_domains):
    if len(assignment) == len(csp["variables"]):
        return assignment

    # select an unassigned variable using MRV heuristic
    var = select_unassigned_variable_mrv_fc(assignment, csp, current_domains)
    # try each value in that variable’s domain
    for value in current_domains[var]:
        _record_attempt(stats)
        if is_consistent(var, value, assignment, csp):
            assignment[var] = value
            # Each branch gets its own domains; failed recursion cannot prune siblings.
            next_domains = copy.deepcopy(current_domains)

            # Forward checking: remove the value from the domains of the neighbors
            fc_failed = False
            for neighbor in csp["neighbors"][var]:
                if neighbor not in assignment and value in next_domains[neighbor]:
                    next_domains[neighbor].remove(value)
                    if len(next_domains[neighbor]) == 0:
                        fc_failed = True
                        break

            if not fc_failed:
                result = recursive_backtracking_mrv_forward_checking(assignment, csp, stats, next_domains)
                if result is not None:
                    return result
            
            # Bookkeeping: restore the domains and remove the assignment
            del assignment[var]
    stats["backtracks"] += 1
    return None

# Simplified version of the MRV selection function for forward checking
def select_unassigned_variable_mrv_fc(assignment, csp, current_domains):
    best_var = None
    min_remaining_values = float('inf')
    for var in csp["variables"]:
        if var not in assignment:
            remaining_values = len(current_domains[var])
            if remaining_values < min_remaining_values:
                min_remaining_values = remaining_values
                best_var = var
    return best_var

def print_results(algorithm_name, solution, stats, print_solution=True):
    print("=" * 50)
    print(f"Algorithm: {algorithm_name}")
    print("=" * 50)
    
    if solution is not None:
        print("\nSolution found: YES")
    else:
        print("\nSolution found: NO")
        
    print(f"Assignments attempted: {stats['assignments']}")
    print(f"Backtracks: {stats['backtracks']}")
    print(f"Runtime (ms): {stats['runtime_ms']:.2f}")
    
    if solution is not None and print_solution:
        print("\nSolution:")
        for var, color in solution.items():
            print(f"{var} = {color}")
    print()
