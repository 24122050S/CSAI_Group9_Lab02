"""Separate uniqueness checker for the complete clue set (Section 4.4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from logic.cnf_encoder import CNFEncoder
from models.board import BoardMetadata
from models.clue import Clue
from models.enums import EncodingMode, Status
from solver.dpll import DPLLSolver
from solver.stats import SolverStats


@dataclass(frozen=True)
class UniquenessReport:
    """Result of checking solution uniqueness over a complete clue set."""

    is_consistent: bool
    is_unique: bool
    primary_solution: dict[str, Status] | None
    alternate_solution: dict[str, Status] | None
    differing_cells: tuple[str, ...]
    num_primary_vars: int
    num_aux_vars: int
    num_clauses: int
    sat_calls: int
    stats: SolverStats

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_consistent": self.is_consistent,
            "is_unique": self.is_unique,
            "primary_solution": (
                {k: v.value for k, v in self.primary_solution.items()}
                if self.primary_solution
                else None
            ),
            "alternate_solution": (
                {k: v.value for k, v in self.alternate_solution.items()}
                if self.alternate_solution
                else None
            ),
            "differing_cells": list(self.differing_cells),
            "num_primary_vars": self.num_primary_vars,
            "num_aux_vars": self.num_aux_vars,
            "num_clauses": self.num_clauses,
            "sat_calls": self.sat_calls,
            "stats": self.stats.to_dict(),
        }


class UniquenessChecker:
    """Checks whether a complete clue set admits a unique Criminal/Innocent assignment.

    Method:
    1. Encode all clues (plus optional opening status facts) into CNF.
    2. Solve for a first satisfying assignment M_1. If UNSAT -> inconsistent.
    3. Add a blocking clause over ONLY the primary variables C_1..C_{N^2}:
           bigvee_{i=1}^{N^2} (~C_i if M_1(C_i) else C_i)
       so auxiliary variables cannot mask or manufacture spurious solutions.
    4. Re-solve: if UNSAT -> unique solution; if SAT -> multiple valid solutions exist.
    """

    @staticmethod
    def check(
        board: BoardMetadata,
        all_clues: Iterable[Clue],
        initial_verdicts: dict[str, Status] | None = None,
        encoding_mode: EncodingMode = EncodingMode.COMBINATORIAL,
        solver: DPLLSolver | None = None,
    ) -> UniquenessReport:
        sat_solver = solver or DPLLSolver()
        encoder = CNFEncoder(board, encoding_mode=encoding_mode)
        kb = encoder.build_knowledge_base(
            revealed_clues=all_clues,
            proved_verdicts=initial_verdicts,
        )

        agg_stats = SolverStats()
        res1 = sat_solver.solve(kb.clauses, num_vars=kb.variables.total_vars)
        agg_stats.merge(res1.stats)

        if not res1.is_sat or res1.assignment is None:
            return UniquenessReport(
                is_consistent=False,
                is_unique=False,
                primary_solution=None,
                alternate_solution=None,
                differing_cells=(),
                num_primary_vars=kb.num_primary_vars,
                num_aux_vars=kb.num_aux_vars,
                num_clauses=kb.num_clauses,
                sat_calls=1,
                stats=agg_stats,
            )

        sol1 = kb.variables.extract_primary_statuses(res1.assignment)

        # Blocking clause strictly over primary variables 1..N^2
        blocking_clause = tuple(
            (-vid if res1.assignment[vid] else vid)
            for vid in kb.variables.primary_var_ids
        )

        res2 = sat_solver.solve(
            list(kb.clauses) + [blocking_clause],
            num_vars=kb.variables.total_vars,
        )
        agg_stats.merge(res2.stats)

        if not res2.is_sat or res2.assignment is None:
            return UniquenessReport(
                is_consistent=True,
                is_unique=True,
                primary_solution=sol1,
                alternate_solution=None,
                differing_cells=(),
                num_primary_vars=kb.num_primary_vars,
                num_aux_vars=kb.num_aux_vars,
                num_clauses=kb.num_clauses,
                sat_calls=2,
                stats=agg_stats,
            )

        sol2 = kb.variables.extract_primary_statuses(res2.assignment)
        diff = tuple(cid for cid in board.cell_ids if sol1[cid] != sol2[cid])

        return UniquenessReport(
            is_consistent=True,
            is_unique=False,
            primary_solution=sol1,
            alternate_solution=sol2,
            differing_cells=diff,
            num_primary_vars=kb.num_primary_vars,
            num_aux_vars=kb.num_aux_vars,
            num_clauses=kb.num_clauses,
            sat_calls=2,
            stats=agg_stats,
        )
