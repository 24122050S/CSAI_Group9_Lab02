"""Custom Davis-Putnam-Logemann-Loveland (DPLL) SAT Solver (Section 4.3)."""

from __future__ import annotations

import time
from enum import Enum
from typing import Iterable, Sequence

from solver.stats import DPLLResult, SolverStats

Clause = tuple[int, ...]


class BranchingHeuristic(str, Enum):
    """Deterministic variable selection strategies (Section 4.3 & 4.5)."""

    FIXED_ORDER = "FIXED_ORDER"  # Smallest unassigned variable ID first, True before False
    JEROSLOW_WANG = "JEROSLOW_WANG"  # 2-sided Jeroslow-Wang score, tie-broken by smallest var ID


class SolverTimeoutError(TimeoutError):
    """Raised when a DPLL run exceeds the configured wall-clock timeout."""


class DPLLSolver:
    """Pure-Python DPLL SAT Solver implemented from scratch.

    Satisfies all Section 4.3 requirements:
    1. Unit propagation
    2. Conflict detection
    3. Deterministic variable selection
    4. Recursive branching and backtracking
    5. Returning SAT with a complete assignment or UNSAT
    6. Recording decisions, propagations, backtracks, and runtime
    Optional flags: `heuristic` (FIXED_ORDER | JEROSLOW_WANG) and `use_pure_literal`.
    """

    def __init__(
        self,
        heuristic: BranchingHeuristic = BranchingHeuristic.FIXED_ORDER,
        use_pure_literal: bool = False,
        timeout_sec: float | None = None,
    ) -> None:
        self.heuristic = heuristic
        self.use_pure_literal = use_pure_literal
        self.timeout_sec = timeout_sec

    @staticmethod
    def _lit_value(lit: int, assignment: dict[int, bool]) -> bool | None:
        val = assignment.get(abs(lit))
        if val is None:
            return None
        return val if lit > 0 else (not val)

    @staticmethod
    def _normalize_initial_clauses(clauses: Iterable[Sequence[int]]) -> list[Clause]:
        """Deduplicate literals within each clause and drop tautological clauses (v v ~v)."""
        normalized: list[Clause] = []
        for raw in clauses:
            if len(raw) == 0:
                return [()]  # Immediate empty clause (UNSAT)
            seen: set[int] = set()
            deduped: list[int] = []
            is_tautology = False
            for lit in raw:
                if lit == 0:
                    raise ValueError("Literal 0 is invalid in CNF clause.")
                if -lit in seen:
                    is_tautology = True
                    break
                if lit not in seen:
                    seen.add(lit)
                    deduped.append(lit)
            if not is_tautology:
                normalized.append(tuple(deduped))
        return normalized

    @classmethod
    def _simplify_clauses(
        cls,
        clauses: list[Clause],
        assignment: dict[int, bool],
    ) -> tuple[bool, list[Clause]]:
        """Simplify `clauses` under `assignment`.

        Returns:
            (has_conflict, simplified_clauses)
        """
        simplified: list[Clause] = []
        for clause in clauses:
            clause_satisfied = False
            remaining: list[int] = []
            for lit in clause:
                val = cls._lit_value(lit, assignment)
                if val is True:
                    clause_satisfied = True
                    break
                if val is None:
                    remaining.append(lit)
            if clause_satisfied:
                continue
            if not remaining:
                return True, []  # Empty clause -> conflict!
            simplified.append(tuple(remaining))
        return False, simplified

    @classmethod
    def _unit_propagate(
        cls,
        clauses: list[Clause],
        assignment: dict[int, bool],
        stats: SolverStats,
    ) -> tuple[bool, list[Clause], dict[int, bool]]:
        """Iteratively propagate unit clauses until fixed point or conflict."""
        # First check for pre-existing empty clauses or already-assigned literals
        conflict, working = cls._simplify_clauses(clauses, assignment)
        if conflict:
            return True, [], assignment

        while True:
            unit_lit: int | None = None
            for clause in working:
                if len(clause) == 1:
                    unit_lit = clause[0]
                    break
            if unit_lit is None:
                return False, working, assignment

            var = abs(unit_lit)
            val = unit_lit > 0
            existing = assignment.get(var)
            if existing is not None:
                if existing != val:
                    return True, [], assignment
            else:
                assignment[var] = val
                stats.propagations += 1

            conflict, working = cls._simplify_clauses(working, assignment)
            if conflict:
                return True, [], assignment

    @classmethod
    def _pure_literal_eliminate(
        cls,
        clauses: list[Clause],
        assignment: dict[int, bool],
        stats: SolverStats,
    ) -> list[Clause]:
        """Assign literals that appear with only a single polarity in remaining clauses."""
        working = clauses
        while working:
            polarities: dict[int, int] = {}  # var -> +1 (pos only), -1 (neg only), 0 (both)
            for clause in working:
                for lit in clause:
                    v = abs(lit)
                    sign = 1 if lit > 0 else -1
                    prev = polarities.get(v)
                    if prev is None:
                        polarities[v] = sign
                    elif prev != sign:
                        polarities[v] = 0

            pure_vars = sorted(v for v, p in polarities.items() if p != 0)
            if not pure_vars:
                break

            for v in pure_vars:
                assignment[v] = polarities[v] > 0
                stats.pure_eliminations += 1

            _, working = cls._simplify_clauses(working, assignment)
        return working

    def _select_branch_variable(
        self,
        clauses: list[Clause],
        assignment: dict[int, bool],
        all_vars: range,
    ) -> tuple[int, bool]:
        """Deterministically choose an unassigned variable and initial truth value."""
        if self.heuristic == BranchingHeuristic.JEROSLOW_WANG:
            pos_score: dict[int, float] = {}
            neg_score: dict[int, float] = {}
            for clause in clauses:
                clen = len(clause)
                weight = 1.0 / (1 << clen) if clen < 30 else (2.0 ** (-clen))
                for lit in clause:
                    v = abs(lit)
                    if lit > 0:
                        pos_score[v] = pos_score.get(v, 0.0) + weight
                    else:
                        neg_score[v] = neg_score.get(v, 0.0) + weight

            candidates = sorted(set(pos_score.keys()) | set(neg_score.keys()))
            if candidates:
                # Deterministic tie-break: highest total JW score, then smallest variable ID
                best_var = max(
                    candidates,
                    key=lambda v: (pos_score.get(v, 0.0) + neg_score.get(v, 0.0), -v),
                )
                first_val = pos_score.get(best_var, 0.0) >= neg_score.get(best_var, 0.0)
                return best_var, first_val

        # FIXED_ORDER (or fallback): smallest unassigned variable appearing in clauses or range
        active_vars = sorted({abs(lit) for c in clauses for lit in c if abs(lit) not in assignment})
        if active_vars:
            return active_vars[0], True
        for v in all_vars:
            if v not in assignment:
                return v, True
        raise RuntimeError("No unassigned variable available for branching.")

    def solve(
        self,
        clauses: Sequence[Sequence[int]],
        num_vars: int | None = None,
        assumptions: Sequence[int] = (),
    ) -> DPLLResult:
        """Solve CNF `clauses` joined with unit `assumptions`.

        Returns:
            DPLLResult(is_sat, complete_assignment_or_None, stats)
        """
        stats = SolverStats()
        start_time = time.perf_counter()

        # Append assumptions as temporary unit clauses without mutating caller's formula
        combined_raw: list[Sequence[int]] = list(clauses)
        for lit in assumptions:
            combined_raw.append((lit,))

        max_var_in_formula = 0
        for raw in combined_raw:
            for lit in raw:
                if abs(lit) > max_var_in_formula:
                    max_var_in_formula = abs(lit)

        total_vars = max(num_vars or 0, max_var_in_formula)
        all_vars = range(1, total_vars + 1)

        initial_clauses = self._normalize_initial_clauses(combined_raw)

        def _dpll_recursive(
            curr_clauses: list[Clause],
            curr_assign: dict[int, bool],
        ) -> dict[int, bool] | None:
            if self.timeout_sec is not None:
                if (time.perf_counter() - start_time) > self.timeout_sec:
                    raise SolverTimeoutError(
                        f"DPLL exceeded timeout of {self.timeout_sec:.2f}s."
                    )

            conflict, simplified, prop_assign = self._unit_propagate(
                curr_clauses, dict(curr_assign), stats
            )
            if conflict:
                return None

            if self.use_pure_literal and simplified:
                simplified = self._pure_literal_eliminate(simplified, prop_assign, stats)

            # All clauses satisfied -> fill any unconstrained variables deterministically
            if not simplified:
                for v in all_vars:
                    if v not in prop_assign:
                        prop_assign[v] = False
                return prop_assign

            var, first_polarity = self._select_branch_variable(
                simplified, prop_assign, all_vars
            )

            # Branch 1
            stats.decisions += 1
            branch1 = dict(prop_assign)
            branch1[var] = first_polarity
            res1 = _dpll_recursive(simplified, branch1)
            if res1 is not None:
                return res1

            # Backtrack -> Branch 2
            stats.backtracks += 1
            branch2 = dict(prop_assign)
            branch2[var] = not first_polarity
            return _dpll_recursive(simplified, branch2)

        model = _dpll_recursive(initial_clauses, {})
        stats.runtime_sec = time.perf_counter() - start_time

        if model is None:
            return DPLLResult(is_sat=False, assignment=None, stats=stats)

        # Return sorted complete assignment {1: bool, ..., total_vars: bool}
        complete = {v: model[v] for v in sorted(model.keys())}
        return DPLLResult(is_sat=True, assignment=complete, stats=stats)

    @classmethod
    def is_formula_satisfied(
        cls,
        clauses: Iterable[Sequence[int]],
        assignment: dict[int, bool],
    ) -> bool:
        """Check directly whether a complete variable `assignment` satisfies all `clauses`."""
        for clause in clauses:
            if not any(cls._lit_value(lit, assignment) is True for lit in clause):
                return False
        return True
