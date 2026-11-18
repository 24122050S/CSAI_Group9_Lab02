"""Exhaustive truth-table equivalence tests: SemanticEvaluator vs CNFEncoder + DPLL."""

from __future__ import annotations

from itertools import product
import unittest

from logic.cnf_encoder import CNFEncoder
from logic.evaluator import SemanticEvaluator
from models.clue import Clue, RegionSpec
from models.enums import ClueType, CompoundOperator, Direction, EncodingMode, ParityKind, Status
from solver.dpll import DPLLSolver
from tests.test_regions_clues import make_sample_3x3_board


class TestCNFEquivalenceWithSemanticEvaluator(unittest.TestCase):
    """Enumerates all 2^9 = 512 complete truth assignments on a 3x3 board.

    Asserts that for every clue template (6 core + 3 extensions) and both encoding
    modes (COMBINATORIAL and SEQUENTIAL), SemanticEvaluator(clue, alpha) matches
    SAT(CNF(clue) ^ unit_assumptions(alpha)) identically on all 512 assignments.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.board = make_sample_3x3_board()
        cls.all_assignments: list[tuple[dict[str, bool], tuple[int, ...]]] = []
        cell_ids = cls.board.cell_ids
        for bits in product([False, True], repeat=len(cell_ids)):
            str_map = {cid: bit for cid, bit in zip(cell_ids, bits)}
            assumptions = tuple(
                (idx if bit else -idx) for idx, bit in enumerate(bits, start=1)
            )
            cls.all_assignments.append((str_map, assumptions))

    def _assert_clue_equivalence(self, clue: Clue) -> None:
        solver = DPLLSolver()
        for mode in (EncodingMode.COMBINATORIAL, EncodingMode.SEQUENTIAL):
            encoder = CNFEncoder(self.board, encoding_mode=mode)
            clauses = encoder.encode_clue(clue)
            total_vars = encoder.variables.total_vars
            # Verify primary vs auxiliary variable separation
            self.assertEqual(encoder.variables.num_primary_vars, 9)
            self.assertEqual(total_vars, 9 + encoder.variables.num_aux_vars)

            for str_map, assumptions in self.all_assignments:
                sem_val = SemanticEvaluator.evaluate(clue, str_map, self.board)
                sat_res = solver.solve(
                    clauses, num_vars=total_vars, assumptions=assumptions
                )
                self.assertEqual(
                    sem_val,
                    sat_res.is_sat,
                    msg=(
                        f"Mismatch on clue={clue.clue_id} ({clue.clue_type.value}) "
                        f"in mode={mode.value}: semantic={sem_val}, cnf_sat={sat_res.is_sat}"
                    ),
                )

    def test_core_binary_and_unit_clues(self) -> None:
        clues = [
            Clue("f_crim", "A1", ClueType.FACT, target="B2", status=Status.CRIMINAL),
            Clue("f_inno", "A1", ClueType.FACT, target="Clara", status=Status.INNOCENT),
            Clue("same_1", "A1", ClueType.SAME, target1="Abel", target2="Ivy"),
            Clue("diff_1", "A1", ClueType.DIFFERENT, target1="B1", target2="C2"),
        ]
        for clue in clues:
            self._assert_clue_equivalence(clue)

    def test_core_counting_clues_all_k(self) -> None:
        # Test k = 0..5 on a 5-cell region (neighbors of edge B1)
        reg5 = RegionSpec.neighbors("B1")
        for k in range(0, 6):
            self._assert_clue_equivalence(
                Clue(f"ex_{k}", "B1", ClueType.EXACTLY, count=k, region=reg5)
            )
            self._assert_clue_equivalence(
                Clue(f"ge_{k}", "B1", ClueType.AT_LEAST, count=k, region=reg5)
            )
            self._assert_clue_equivalence(
                Clue(f"le_{k}", "B1", ClueType.AT_MOST, count=k, region=reg5)
            )

        # NO alias & INNOCENT target_status
        self._assert_clue_equivalence(
            Clue("no_row1", "A1", ClueType.NO, region=RegionSpec.row_region(1))
        )
        self._assert_clue_equivalence(
            Clue(
                "ex2_inno",
                "C1",
                ClueType.EXACTLY,
                count=2,
                region=RegionSpec.corners(),
                target_status=Status.INNOCENT,
            )
        )

    def test_extensions_comparison_and_parity(self) -> None:
        # Overlapping regions Row 1 (A1,B1,C1) vs Col A (A1,A2,A3)
        self._assert_clue_equivalence(
            Clue(
                "more_r1_ca",
                "A1",
                ClueType.MORE_CRIMINALS,
                region=RegionSpec.row_region(1),
                region2=RegionSpec.col_region("A"),
            )
        )
        self._assert_clue_equivalence(
            Clue(
                "eq_r2_cc",
                "B2",
                ClueType.EQUAL_CRIMINALS,
                region=RegionSpec.row_region(2),
                region2=RegionSpec.col_region("C"),
            )
        )
        # Parity ODD and EVEN over 8 neighbors of B2
        self._assert_clue_equivalence(
            Clue(
                "odd_nb_b2",
                "B2",
                ClueType.PARITY,
                region=RegionSpec.neighbors("B2"),
                parity=ParityKind.ODD,
            )
        )
        self._assert_clue_equivalence(
            Clue(
                "even_cooks",
                "A1",
                ClueType.PARITY,
                region=RegionSpec.by_profession("Cook"),
                parity=ParityKind.EVEN,
            )
        )

    def test_extensions_4_and_5_compound_and_connected(self) -> None:
        # Extension 5: 1D path connectivity (Row 1 & Directional ray like Figure 1 D5)
        self._assert_clue_equivalence(
            Clue.connected("conn_row1", "A1", RegionSpec.row_region(1), Status.CRIMINAL)
        )
        self._assert_clue_equivalence(
            Clue.connected(
                "conn_right_a1",
                "C3",
                RegionSpec.directional("A1", Direction.RIGHT),
                Status.INNOCENT,
            )
        )
        # Extension 5: General 2D graph connectivity (5-cell neighbors, 8-ring boundary, disconnected corners)
        self._assert_clue_equivalence(
            Clue.connected("conn_nb_b1", "B1", RegionSpec.neighbors("B1"), Status.CRIMINAL)
        )
        self._assert_clue_equivalence(
            Clue.connected("conn_boundary_inno", "B2", RegionSpec.boundary(), Status.INNOCENT)
        )
        self._assert_clue_equivalence(
            Clue.connected("conn_corners", "A1", RegionSpec.corners(), Status.CRIMINAL)
        )

        # Extension 4: COMPOUND (AND, OR, IMPLIES, including Figure 1 A5 & D5 patterns)
        # Figure 1 A5 pattern: "Grant is one of Eliza's 2 criminal neighbors"
        fig1_a5_style = Clue.compound(
            "cmp_and_fig1",
            "A3",
            CompoundOperator.AND,
            [
                Clue("sub1", "A3", ClueType.FACT, target="Grant", status=Status.CRIMINAL),
                Clue("sub2", "A3", ClueType.EXACTLY, count=2, region=RegionSpec.neighbors("Eliza")),
            ],
        )
        self._assert_clue_equivalence(fig1_a5_style)

        # Figure 1 D5 pattern: "Both innocents to the right of Abel are connected"
        ray = RegionSpec.directional("Abel", Direction.RIGHT)
        fig1_d5_style = Clue.compound(
            "cmp_conn_fig1",
            "C3",
            CompoundOperator.AND,
            [
                Clue("sub_cnt", "C3", ClueType.EXACTLY, count=2, region=ray, target_status=Status.INNOCENT),
                Clue.connected("sub_con", "C3", ray, target_status=Status.INNOCENT),
            ],
        )
        self._assert_clue_equivalence(fig1_d5_style)

        # Compound OR over counting & parity clues
        cmp_or = Clue.compound(
            "cmp_or",
            "B2",
            CompoundOperator.OR,
            [
                Clue("or1", "B2", ClueType.EXACTLY, count=2, region=RegionSpec.row_region(1)),
                Clue("or2", "B2", ClueType.PARITY, parity=ParityKind.ODD, region=RegionSpec.col_region("C")),
            ],
        )
        self._assert_clue_equivalence(cmp_or)

        # Compound IMPLIES over EXACTLY -> MORE_CRIMINALS (tests structural negation + auxiliary vars!)
        cmp_imp = Clue.compound(
            "cmp_imp",
            "C1",
            CompoundOperator.IMPLIES,
            [
                Clue("imp_a", "C1", ClueType.EXACTLY, count=2, region=RegionSpec.row_region(2)),
                Clue(
                    "imp_b",
                    "C1",
                    ClueType.MORE_CRIMINALS,
                    region=RegionSpec.row_region(1),
                    region2=RegionSpec.row_region(3),
                ),
            ],
        )
        self._assert_clue_equivalence(cmp_imp)


if __name__ == "__main__":
    unittest.main()
