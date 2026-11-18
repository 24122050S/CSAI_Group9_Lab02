"""Unit tests for the custom DPLL SAT Solver (Section 4.3)."""

from __future__ import annotations

import unittest

from solver.dpll import BranchingHeuristic, DPLLSolver


class TestDPLLSolver(unittest.TestCase):
    def test_pdf_page4_entailment_example(self) -> None:
        """Verify the exact example on Page 4 of the project specification:
        KB = (C_A v C_B) ^ (~C_A v C_B), where A=1, B=2.
        - KB ^ ~C_B must be UNSAT (so B is forced Criminal).
        - KB ^ C_A and KB ^ ~C_A must both be SAT (so A remains UNKNOWN).
        """
        kb = [(1, 2), (-1, 2)]
        solver = DPLLSolver()

        res_not_b = solver.solve(kb, num_vars=2, assumptions=[-2])
        self.assertFalse(res_not_b.is_sat)
        self.assertGreaterEqual(res_not_b.stats.propagations, 2)

        res_b = solver.solve(kb, num_vars=2, assumptions=[2])
        self.assertTrue(res_b.is_sat)
        self.assertIsNotNone(res_b.assignment)
        self.assertEqual(set(res_b.assignment.keys()), {1, 2})

        res_a = solver.solve(kb, num_vars=2, assumptions=[1])
        res_not_a = solver.solve(kb, num_vars=2, assumptions=[-1])
        self.assertTrue(res_a.is_sat)
        self.assertTrue(res_not_a.is_sat)

    def test_pigeonhole_php_4_3_unsat_and_backtracking(self) -> None:
        """4 pigeons into 3 holes -> guaranteed UNSAT requiring branching & backtracks."""
        # var(p, h) = (p - 1) * 3 + h for p in 1..4, h in 1..3 (vars 1..12)
        def v(p: int, h: int) -> int:
            return (p - 1) * 3 + h

        clauses: list[tuple[int, ...]] = []
        # Each pigeon in at least 1 hole
        for p in range(1, 5):
            clauses.append((v(p, 1), v(p, 2), v(p, 3)))
        # No two pigeons in same hole
        for h in range(1, 4):
            for p1 in range(1, 5):
                for p2 in range(p1 + 1, 5):
                    clauses.append((-v(p1, h), -v(p2, h)))

        for heuristic in (BranchingHeuristic.FIXED_ORDER, BranchingHeuristic.JEROSLOW_WANG):
            for ple in (False, True):
                solver = DPLLSolver(heuristic=heuristic, use_pure_literal=ple)
                res = solver.solve(clauses, num_vars=12)
                self.assertFalse(res.is_sat)
                self.assertGreater(res.stats.decisions, 0)
                self.assertGreater(res.stats.backtracks, 0)
                self.assertGreaterEqual(res.stats.runtime_sec, 0.0)

    def test_complete_assignment_fills_unconstrained_variables(self) -> None:
        """Solver must return a complete assignment over 1..num_vars even for unconstrained vars."""
        solver = DPLLSolver()
        res = solver.solve([(2,)], num_vars=5)
        self.assertTrue(res.is_sat)
        assert res.assignment is not None
        self.assertEqual(set(res.assignment.keys()), {1, 2, 3, 4, 5})
        self.assertTrue(res.assignment[2])
        self.assertTrue(DPLLSolver.is_formula_satisfied([(2,)], res.assignment))


if __name__ == "__main__":
    unittest.main()
