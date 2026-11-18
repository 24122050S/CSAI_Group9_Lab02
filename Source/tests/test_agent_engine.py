"""Unit tests for GameEngine, DeductiveLogicAgent, UniquenessChecker, and HintEngine."""

from __future__ import annotations

import unittest

from agent.deductive_agent import DeductiveLogicAgent
from agent.hint import HintEngine
from agent.uniqueness import UniquenessChecker
from engine.game_engine import GameEngine
from engine.puzzle_generator import PuzzleGenerator
from engine.puzzle_loader import SecretPuzzleData
from models.clue import Clue, RegionSpec
from models.enums import AgentTerminalState, ClueType, EncodingMode, Status, VerdictStatus
from tests.test_regions_clues import make_sample_3x3_board


class TestAgentAndEngine(unittest.TestCase):
    def _make_handcrafted_puzzle(self) -> SecretPuzzleData:
        board = make_sample_3x3_board()
        truth = {
            "A1": Status.INNOCENT,
            "B1": Status.CRIMINAL,
            "C1": Status.CRIMINAL,
            "A2": Status.INNOCENT,
            "B2": Status.CRIMINAL,
            "C2": Status.INNOCENT,
            "A3": Status.CRIMINAL,
            "B3": Status.INNOCENT,
            "C3": Status.INNOCENT,
        }
        clues = {
            # Opening A1 is INNOCENT; Row 1 has 2 criminals -> forces B1 & C1 CRIMINAL!
            "A1": Clue("c_A1", "A1", ClueType.EXACTLY, count=2, region=RegionSpec.row_region(1)),
            # B1 forces A2 INNOCENT (since B1=CRIMINAL and DIFFERENT(B1, A2))
            "B1": Clue("c_B1", "B1", ClueType.DIFFERENT, target1="B1", target2="A2"),
            # C1: Col C has 1 criminal -> since C1=CRIMINAL, forces C2 & C3 INNOCENT!
            "C1": Clue("c_C1", "C1", ClueType.EXACTLY, count=1, region=RegionSpec.col_region("C")),
            # A2: Row 2 has 1 criminal -> since A2=INNOCENT & C2=INNOCENT, forces B2 CRIMINAL!
            "A2": Clue("c_A2", "A2", ClueType.EXACTLY, count=1, region=RegionSpec.row_region(2)),
            # C2: SAME(B2, A3) -> since B2=CRIMINAL, forces A3 CRIMINAL!
            "C2": Clue("c_C2", "C2", ClueType.SAME, target1="B2", target2="A3"),
            # A3: Row 3 has at most 1 criminal -> since A3=CRIMINAL, forces B3 INNOCENT!
            "A3": Clue("c_A3", "A3", ClueType.AT_MOST, count=1, region=RegionSpec.row_region(3)),
            "B2": Clue("c_B2", "B2", ClueType.AT_LEAST, count=3, region=RegionSpec.neighbors("B2")),
            "B3": Clue("c_B3", "B3", ClueType.EXACTLY, count=5, region=RegionSpec.boundary(), target_status=Status.INNOCENT),
            "C3": Clue("c_C3", "C3", ClueType.DIFFERENT, target1="A3", target2="C3"),
        }
        return SecretPuzzleData(
            puzzle_id="test_3x3_chain",
            title="Handcrafted 3x3 Chain",
            difficulty="Easy",
            description="Stepwise chain test.",
            board=board,
            ground_truth=truth,
            clues=clues,
            initial_revealed=("A1",),
        )

    def test_strict_public_state_isolation_and_verdict_rejection(self) -> None:
        puzzle = self._make_handcrafted_puzzle()
        engine = GameEngine(puzzle)
        pub = engine.get_public_state()

        # Unrevealed cells must NOT expose hidden status or clue
        b2_view = pub.get_cell("B2")
        self.assertFalse(b2_view.is_revealed)
        self.assertEqual(b2_view.status, Status.UNKNOWN)
        self.assertIsNone(b2_view.clue)

        # At t=0, B2 is actually CRIMINAL in hidden truth, so guessing CRIMINAL is a "lucky guess"
        # Engine MUST reject it as NOT_PROVABLE and keep B2 face-down!
        lucky_guess = engine.submit_verdict("B2", Status.CRIMINAL)
        self.assertEqual(lucky_guess.status_code, VerdictStatus.NOT_PROVABLE)
        self.assertIsNone(lucky_guess.revealed_clue)
        self.assertFalse(engine.get_public_state().get_cell("B2").is_revealed)

        # At t=0, B1 IS logically forced CRIMINAL. Submitting INNOCENT must return CONTRADICTED!
        wrong_forced = engine.submit_verdict("B1", Status.INNOCENT)
        self.assertEqual(wrong_forced.status_code, VerdictStatus.CONTRADICTED)
        self.assertIsNone(wrong_forced.revealed_clue)

        # Submitting CRIMINAL for B1 must be ACCEPTED and reveal B1's clue!
        ok = engine.submit_verdict("B1", Status.CRIMINAL)
        self.assertEqual(ok.status_code, VerdictStatus.ACCEPTED)
        self.assertIsNotNone(ok.revealed_clue)
        self.assertEqual(ok.revealed_clue.clue_id, "c_B1")

    def test_full_solve_both_modes_and_hint_mus(self) -> None:
        puzzle = self._make_handcrafted_puzzle()

        # Check Hint at initial state
        engine0 = GameEngine(puzzle)
        hint = HintEngine.get_hint(engine0.get_public_state())
        self.assertTrue(hint.available)
        self.assertEqual(hint.target_cell, "B1")
        self.assertEqual(hint.forced_status, Status.CRIMINAL)
        self.assertIn("c_A1", hint.relevant_clue_ids)

        # Compare explicit refutation vs witness-pruned refutation across both encodings
        for enc_mode in (EncodingMode.COMBINATORIAL, EncodingMode.SEQUENTIAL):
            for prune in (False, True):
                eng = GameEngine(puzzle, encoding_mode=enc_mode)
                agent = DeductiveLogicAgent(
                    encoding_mode=enc_mode, use_witness_pruning=prune
                )
                rep = agent.solve(eng)
                self.assertEqual(rep.terminal_state, AgentTerminalState.SOLVED)
                self.assertEqual(rep.deduction_steps, 8)
                self.assertTrue(eng.get_public_state().is_solved)

        # Verify uniqueness check
        uniq = engine0.check_complete_uniqueness()
        self.assertTrue(uniq.is_consistent)
        self.assertTrue(uniq.is_unique)

    def test_ambiguous_stuck_and_inconsistent_detection(self) -> None:
        board = make_sample_3x3_board()
        truth = {cid: Status.INNOCENT for cid in board.cell_ids}
        truth["B2"] = Status.CRIMINAL

        # Ambiguous puzzle: A1 clue says at most 2 criminals in Row 2 -> nothing forced!
        amb_puzzle = SecretPuzzleData(
            puzzle_id="amb",
            title="Ambiguous",
            difficulty="Test",
            description="",
            board=board,
            ground_truth=truth,
            clues={
                "A1": Clue("c_A1", "A1", ClueType.AT_MOST, count=2, region=RegionSpec.row_region(2))
            },
            initial_revealed=("A1",),
        )
        eng_amb = GameEngine(amb_puzzle)
        rep_amb = DeductiveLogicAgent().solve(eng_amb)
        self.assertEqual(rep_amb.terminal_state, AgentTerminalState.STUCK)
        self.assertEqual(rep_amb.deduction_steps, 0)

        uniq_amb = UniquenessChecker.check(
            board, amb_puzzle.clues.values(), initial_verdicts={"A1": Status.INNOCENT}
        )
        self.assertTrue(uniq_amb.is_consistent)
        self.assertFalse(uniq_amb.is_unique)
        self.assertGreater(len(uniq_amb.differing_cells), 0)

        # Inconsistent puzzle: A1 says B1=CRIMINAL, C1 says B1=INNOCENT, both open!
        inc_puzzle = SecretPuzzleData(
            puzzle_id="inc",
            title="Inconsistent",
            difficulty="Test",
            description="",
            board=board,
            ground_truth=truth,
            clues={
                "A1": Clue("c1", "A1", ClueType.FACT, target="B1", status=Status.CRIMINAL),
                "C1": Clue("c2", "C1", ClueType.FACT, target="B1", status=Status.INNOCENT),
            },
            initial_revealed=("A1", "C1"),
            allow_inconsistent=True,
        )
        eng_inc = GameEngine(inc_puzzle)
        rep_inc = DeductiveLogicAgent().solve(eng_inc)
        self.assertEqual(rep_inc.terminal_state, AgentTerminalState.INCONSISTENT)

    def test_generator_synthesizes_valid_4x4(self) -> None:
        p4 = PuzzleGenerator.generate(
            puzzle_id="gen_4x4_test",
            title="Generated 4x4",
            grid_size=4,
            seed=42,
            include_extensions=True,
            num_initial_revealed=2,
        )
        eng = GameEngine(p4)
        rep = DeductiveLogicAgent(use_witness_pruning=True).solve(eng)
        self.assertEqual(rep.terminal_state, AgentTerminalState.SOLVED)
        self.assertEqual(rep.deduction_steps, 14)


if __name__ == "__main__":
    unittest.main()
