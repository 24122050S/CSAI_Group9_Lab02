"""Automated experimental benchmark runner across all 3x3, 4x4, and 5x5 puzzles (Section 4.5)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from agent.deductive_agent import DeductiveLogicAgent
from engine.game_engine import GameEngine
from engine.puzzle_loader import PuzzleLoader
from models.enums import EncodingMode
from solver.dpll import BranchingHeuristic


@dataclass(frozen=True)
class SolverConfigSpec:
    name: str
    encoding_mode: EncodingMode
    heuristic: BranchingHeuristic
    use_pure_literal: bool
    use_witness_pruning: bool


BENCHMARK_CONFIGS: tuple[SolverConfigSpec, ...] = (
    SolverConfigSpec(
        name="1_Comb_Fixed",
        encoding_mode=EncodingMode.COMBINATORIAL,
        heuristic=BranchingHeuristic.FIXED_ORDER,
        use_pure_literal=False,
        use_witness_pruning=False,
    ),
    SolverConfigSpec(
        name="2_Seq_Fixed",
        encoding_mode=EncodingMode.SEQUENTIAL,
        heuristic=BranchingHeuristic.FIXED_ORDER,
        use_pure_literal=False,
        use_witness_pruning=False,
    ),
    SolverConfigSpec(
        name="3_Comb_JW",
        encoding_mode=EncodingMode.COMBINATORIAL,
        heuristic=BranchingHeuristic.JEROSLOW_WANG,
        use_pure_literal=False,
        use_witness_pruning=False,
    ),
    SolverConfigSpec(
        name="4_Comb_JW_Pruned",
        encoding_mode=EncodingMode.COMBINATORIAL,
        heuristic=BranchingHeuristic.JEROSLOW_WANG,
        use_pure_literal=True,
        use_witness_pruning=True,
    ),
)


def run_all_benchmarks(
    puzzles_dir: Path | None = None,
    results_dir: Path | None = None,
    timeout_sec: float = 25.0,
) -> list[dict]:
    src_root = Path(__file__).resolve().parent.parent
    p_dir = puzzles_dir or (src_root / "puzzles")
    out_dir = results_dir or (Path(__file__).resolve().parent / "results")
    out_dir.mkdir(parents=True, exist_ok=True)

    puzzle_files = sorted(p_dir.rglob("*.json"))
    if not puzzle_files:
        raise FileNotFoundError(f"No puzzle JSON files found in {p_dir}")

    rows: list[dict] = []
    for cfg in BENCHMARK_CONFIGS:
        print(f"\n=== Running Configuration: {cfg.name} ===")
        for pf in puzzle_files:
            puzzle = PuzzleLoader.load_file(pf)
            engine = GameEngine(puzzle, encoding_mode=cfg.encoding_mode)
            agent = DeductiveLogicAgent(
                encoding_mode=cfg.encoding_mode,
                heuristic=cfg.heuristic,
                use_pure_literal=cfg.use_pure_literal,
                use_witness_pruning=cfg.use_witness_pruning,
                timeout_sec=timeout_sec,
            )
            rep = agent.solve(engine)

            row = {
                "config": cfg.name,
                "puzzle_id": puzzle.puzzle_id,
                "grid_size": f"{puzzle.board.grid_size}x{puzzle.board.grid_size}",
                "difficulty": puzzle.difficulty,
                "terminal_state": rep.terminal_state.value,
                "timed_out": rep.timed_out,
                "primary_vars": rep.peak_primary_vars,
                "aux_vars": rep.peak_aux_vars,
                "cnf_clauses": rep.peak_clauses,
                "sat_calls": rep.total_sat_calls,
                "decisions": rep.total_stats.decisions,
                "propagations": rep.total_stats.propagations,
                "backtracks": rep.total_stats.backtracks,
                "deduction_steps": rep.deduction_steps,
                "reveal_waves": rep.reveal_waves,
                "dpll_runtime_ms": round(rep.total_stats.runtime_ms, 3),
                "wall_runtime_ms": round(rep.wall_runtime_sec * 1000.0, 3),
            }
            rows.append(row)
            print(
                f"  {row['puzzle_id']:28s} | {row['terminal_state']:12s} | "
                f"vars={row['primary_vars']}+{row['aux_vars']:2d} | "
                f"cls={row['cnf_clauses']:4d} | sat={row['sat_calls']:3d} | "
                f"dec={row['decisions']:4d} | prop={row['propagations']:5d} | "
                f"bt={row['backtracks']:4d} | steps={row['deduction_steps']:2d} "
                f"(waves={row['reveal_waves']:2d}) | {row['wall_runtime_ms']:7.2f} ms"
            )

    csv_path = out_dir / "benchmark_results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    _write_markdown_summary(rows, out_dir / "benchmark_summary.md")
    print(f"\nSaved CSV results to: {csv_path}")
    return rows


def _write_markdown_summary(rows: list[dict], md_path: Path) -> None:
    lines: list[str] = [
        "# Experimental Benchmark Results (Section 4.5)",
        "",
        "All configurations were evaluated on the exact same 19-puzzle benchmark suite (including Extension 4-5 showcases, coupled backtrack stress cases, `STUCK`, and `INCONSISTENT` diagnostic cases).",
        "",
        "## 1. Detailed Per-Puzzle Results (`1_Comb_Fixed` Baseline)",
        "",
        "| Puzzle ID | Grid | State | Primary + Aux Vars | Peak Clauses | SAT Calls | Decisions | Propagations | Backtracks | Steps (Waves) | Runtime (ms) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for r in rows:
        if r["config"] != "1_Comb_Fixed":
            continue
        lines.append(
            f"| `{r['puzzle_id']}` | {r['grid_size']} | `{r['terminal_state']}` | "
            f"{r['primary_vars']} + {r['aux_vars']} | {r['cnf_clauses']} | "
            f"{r['sat_calls']} | {r['decisions']} | {r['propagations']} | "
            f"{r['backtracks']} | {r['deduction_steps']} ({r['reveal_waves']}) | "
            f"{r['wall_runtime_ms']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## 2. Aggregate Comparison Across Solver & Encoding Configurations (17 Solvable Puzzles)",
            "",
            "| Configuration | Avg Aux Vars | Avg Peak Clauses | Total SAT Calls | Total Decisions | Total Propagations | Total Backtracks | Total Runtime (ms) |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
    )

    for cfg in BENCHMARK_CONFIGS:
        sub = [
            r
            for r in rows
            if r["config"] == cfg.name and r["terminal_state"] == "SOLVED"
        ]
        if not sub:
            continue
        n = len(sub)
        avg_aux = sum(r["aux_vars"] for r in sub) / n
        avg_cls = sum(r["cnf_clauses"] for r in sub) / n
        tot_sat = sum(r["sat_calls"] for r in sub)
        tot_dec = sum(r["decisions"] for r in sub)
        tot_prop = sum(r["propagations"] for r in sub)
        tot_bt = sum(r["backtracks"] for r in sub)
        tot_ms = sum(r["wall_runtime_ms"] for r in sub)
        lines.append(
            f"| `{cfg.name}` | {avg_aux:.1f} | {avg_cls:.1f} | {tot_sat} | "
            f"{tot_dec} | {tot_prop} | {tot_bt} | {tot_ms:.2f} |"
        )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run_all_benchmarks()
