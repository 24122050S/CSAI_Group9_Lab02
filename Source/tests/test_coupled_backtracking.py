"""Regression tests verifying genuine DPLL backtracking and Jeroslow-Wang gains on coupled puzzles."""

from __future__ import annotations

from pathlib import Path
import unittest

from agent.deductive_agent import DeductiveLogicAgent
from engine.game_engine import GameEngine
from engine.puzzle_loader import PuzzleLoader
from models.enums import AgentTerminalState, EncodingMode
from solver.dpll import BranchingHeuristic


class TestCoupledBacktrackingStress(unittest.TestCase):
    def setUp(self) -> None:
        self.puzzles_dir = Path(__file__).resolve().parent.parent / "puzzles"

    def test_4x4_coupled_forces_backtracking_and_jw_improvement(self) -> None:
        p = PuzzleLoader.load_file(
            self.puzzles_dir / "4x4" / "4x4_07_coupled_parity_matrix.json"
        )
        eng_fixed = GameEngine(p)
        rep_fixed = DeductiveLogicAgent(
            encoding_mode=EncodingMode.COMBINATORIAL,
            heuristic=BranchingHeuristic.FIXED_ORDER,
        ).solve(eng_fixed)

        eng_jw = GameEngine(p)
        rep_jw = DeductiveLogicAgent(
            encoding_mode=EncodingMode.COMBINATORIAL,
            heuristic=BranchingHeuristic.JEROSLOW_WANG,
        ).solve(eng_jw)

        self.assertEqual(rep_fixed.terminal_state, AgentTerminalState.SOLVED)
        self.assertEqual(rep_jw.terminal_state, AgentTerminalState.SOLVED)
        self.assertGreaterEqual(rep_fixed.total_stats.backtracks, 100)
        self.assertGreater(rep_jw.total_stats.backtracks, 0)
        self.assertLess(rep_jw.total_stats.backtracks, rep_fixed.total_stats.backtracks // 3)

    def test_5x5_coupled_fortress_stress(self) -> None:
        p = PuzzleLoader.load_file(
            self.puzzles_dir / "5x5" / "5x5_05_coupled_fortress.json"
        )
        eng_fixed = GameEngine(p)
        rep_fixed = DeductiveLogicAgent(
            encoding_mode=EncodingMode.COMBINATORIAL,
            heuristic=BranchingHeuristic.FIXED_ORDER,
        ).solve(eng_fixed)

        eng_jw = GameEngine(p)
        rep_jw = DeductiveLogicAgent(
            encoding_mode=EncodingMode.COMBINATORIAL,
            heuristic=BranchingHeuristic.JEROSLOW_WANG,
            use_witness_pruning=True,
        ).solve(eng_jw)

        self.assertEqual(rep_fixed.terminal_state, AgentTerminalState.SOLVED)
        self.assertEqual(rep_jw.terminal_state, AgentTerminalState.SOLVED)
        self.assertGreaterEqual(rep_fixed.total_stats.backtracks, 500)
        self.assertLess(rep_jw.total_stats.backtracks, rep_fixed.total_stats.backtracks // 3)


if __name__ == "__main__":
    unittest.main()
