"""Main entry point for Project 2: Griductive Solver (CSC14003)."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Ensure Source/ is on sys.path regardless of working directory
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def run_cli_solve(puzzle_path: str, encoding: str, heuristic: str, prune: bool) -> None:
    from agent.deductive_agent import DeductiveLogicAgent
    from engine.game_engine import GameEngine
    from engine.puzzle_loader import PuzzleLoader
    from models.enums import EncodingMode
    from solver.dpll import BranchingHeuristic

    enc_mode = EncodingMode(encoding.upper())
    heur_mode = BranchingHeuristic(heuristic.upper())
    puzzle = PuzzleLoader.load_file(puzzle_path)
    engine = GameEngine(puzzle, encoding_mode=enc_mode)
    agent = DeductiveLogicAgent(
        encoding_mode=enc_mode,
        heuristic=heur_mode,
        use_witness_pruning=prune,
    )

    print(f"=== Solving Puzzle: {puzzle.title} ({puzzle.board.grid_size}x{puzzle.board.grid_size}) ===")
    uniq = engine.check_complete_uniqueness(encoding_mode=enc_mode)
    print(
        f"Complete Clue Set Uniqueness: consistent={uniq.is_consistent}, unique={uniq.is_unique} "
        f"({uniq.num_primary_vars} primary + {uniq.num_aux_vars} aux vars, {uniq.num_clauses} clauses)"
    )

    report = agent.solve(engine)
    for tr in report.steps:
        if tr.chosen_cell:
            print(
                f"  Step #{tr.step_number:2d}: {tr.chosen_character:8s} ({tr.chosen_cell}) -> "
                f"{tr.verdict.value:8s} | SAT calls={len(tr.sat_queries):2d} | "
                f"New clue: {tr.newly_revealed_clue_text or 'None'}"
            )
        else:
            print(f"  Step #{tr.step_number:2d}: Terminal State = {tr.terminal_state.value}")

    print("\n--- Summary ---")
    print(f"Terminal State : {report.terminal_state.value}")
    print(f"Steps / Waves  : {report.deduction_steps} steps ({report.reveal_waves} waves)")
    print(f"Peak Variables : {report.peak_primary_vars} primary + {report.peak_aux_vars} auxiliary")
    print(f"Peak Clauses   : {report.peak_clauses}")
    print(f"Total SAT Calls: {report.total_sat_calls}")
    print(
        f"DPLL Counters  : {report.total_stats.decisions} decisions, "
        f"{report.total_stats.propagations} propagations, "
        f"{report.total_stats.backtracks} backtracks"
    )
    print(f"Total Runtime  : {report.wall_runtime_sec * 1000.0:.2f} ms")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Griductive Solver — Propositional Logic, CNF & Custom DPLL SAT Solver"
    )
    parser.add_argument(
        "--cli",
        type=str,
        default=None,
        help="Solve a specific JSON puzzle file in CLI trace mode instead of launching GUI.",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run the full experimental benchmark suite and generate charts.",
    )
    parser.add_argument(
        "--encoding",
        choices=["COMBINATORIAL", "SEQUENTIAL"],
        default="COMBINATORIAL",
        help="Cardinality CNF encoding mode (for --cli mode).",
    )
    parser.add_argument(
        "--heuristic",
        choices=["FIXED_ORDER", "JEROSLOW_WANG"],
        default="FIXED_ORDER",
        help="DPLL variable branching strategy (for --cli mode).",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Enable witness-guided SAT query pruning (for --cli mode).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Optional localhost port for the Web GUI.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Start the Web GUI server without automatically opening a browser tab.",
    )

    args = parser.parse_args()

    if args.benchmark:
        from experiments.plot_results import generate_charts
        from experiments.run_benchmarks import run_all_benchmarks

        run_all_benchmarks()
        generate_charts()
        return

    if args.cli:
        run_cli_solve(args.cli, args.encoding, args.heuristic, args.prune)
        return

    from gui.app import launch_gui

    launch_gui(port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
