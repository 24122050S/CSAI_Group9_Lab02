"""Generates publication-ready experimental charts for the PDF Report (Section 4.5 & 4.6)."""

from __future__ import annotations

import csv
from pathlib import Path


def generate_charts(results_dir: Path | None = None) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    r_dir = results_dir or (Path(__file__).resolve().parent / "results")
    csv_path = r_dir / "benchmark_results.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Run run_benchmarks.py first; missing {csv_path}")

    with csv_path.open("r", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    solvable_rows = [r for r in rows if r["terminal_state"] == "SOLVED"]
    configs = ["1_Comb_Fixed", "2_Seq_Fixed", "3_Comb_JW", "4_Comb_JW_Pruned"]
    grid_sizes = ["3x3", "4x4", "5x5"]

    saved: list[Path] = []

    # Chart 1: Mean Solve Runtime (ms) by Grid Size & Configuration
    fig, ax = plt.subplots(figsize=(8.4, 4.6), dpi=180)
    bar_width = 0.19
    x_positions = range(len(grid_sizes))

    for idx, cfg in enumerate(configs):
        avgs = []
        for gs in grid_sizes:
            matching = [
                float(r["wall_runtime_ms"])
                for r in solvable_rows
                if r["config"] == cfg and r["grid_size"] == gs
            ]
            avgs.append(sum(matching) / len(matching) if matching else 0.0)
        offsets = [x + (idx - 1.5) * bar_width for x in x_positions]
        ax.bar(offsets, avgs, width=bar_width, label=cfg)

    ax.set_xticks(list(x_positions))
    ax.set_xticklabels([f"{g} Grid" for g in grid_sizes])
    ax.set_ylabel("Mean Solve Runtime (ms)")
    ax.set_title("Mean Total Deduction Runtime Across Grid Sizes & Configurations")
    ax.grid(axis="y", linestyle="--", alpha=0.45)
    ax.legend(frameon=True)
    fig.tight_layout()
    p1 = r_dir / "chart_runtime_by_grid.png"
    fig.savefig(p1)
    plt.close(fig)
    saved.append(p1)

    # Chart 2: 3-Panel Aggregate SAT Calls, Branching Decisions, and Backtracks
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12.2, 4.2), dpi=180)
    tot_sat = [
        sum(int(r["sat_calls"]) for r in solvable_rows if r["config"] == cfg)
        for cfg in configs
    ]
    tot_dec = [
        sum(int(r["decisions"]) for r in solvable_rows if r["config"] == cfg)
        for cfg in configs
    ]
    tot_bt = [
        sum(int(r["backtracks"]) for r in solvable_rows if r["config"] == cfg)
        for cfg in configs
    ]
    colors = ["#2563eb", "#0891b2", "#7c3aed", "#16a34a"]

    for ax, vals, title, ylabel in [
        (ax1, tot_sat, "Total SAT Calls", "SAT Invocations"),
        (ax2, tot_dec, "Total Decisions", "Branching Decisions"),
        (ax3, tot_bt, "Total Backtracks", "DPLL Backtracks"),
    ]:
        bars = ax.bar(configs, vals, color=colors)
        ax.set_ylim(0, max(vals) * 1.15 if vals else 1.0)
        ax.set_title(title, fontsize=10.5, fontweight="bold")
        ax.set_ylabel(ylabel, fontsize=9)
        ax.tick_params(axis="x", rotation=22, labelsize=8)
        ax.grid(axis="y", linestyle="--", alpha=0.45)
        for b in bars:
            h = b.get_height()
            ax.annotate(
                f"{int(h)}",
                xy=(b.get_x() + b.get_width() / 2, h),
                xytext=(0, 2),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=7.5,
                fontweight="bold",
            )

    fig.tight_layout()
    p2 = r_dir / "chart_sat_calls_and_decisions.png"
    fig.savefig(p2)
    plt.close(fig)
    saved.append(p2)

    # Chart 3: Coupled Backtracking Stress Comparison (Fixed Order vs Jeroslow-Wang)
    bt_puzzles = [
        r["puzzle_id"]
        for r in solvable_rows
        if r["config"] == "1_Comb_Fixed" and int(r["backtracks"]) > 0
    ]
    if bt_puzzles:
        fig, ax = plt.subplots(figsize=(8.6, 4.5), dpi=180)
        cmp_cfgs = [
            ("1_Comb_Fixed", "Fixed Variable Order", "#dc2626"),
            ("3_Comb_JW", "Jeroslow-Wang Heuristic", "#7c3aed"),
            ("4_Comb_JW_Pruned", "Jeroslow-Wang + PLE + Witness Pruned", "#16a34a"),
        ]
        bw = 0.25
        xp = range(len(bt_puzzles))
        for idx, (cfg_key, label, col) in enumerate(cmp_cfgs):
            vals = []
            for pid in bt_puzzles:
                m = [
                    int(r["backtracks"])
                    for r in solvable_rows
                    if r["config"] == cfg_key and r["puzzle_id"] == pid
                ]
                vals.append(m[0] if m else 0)
            offs = [x + (idx - 1) * bw for x in xp]
            bars = ax.bar(offs, vals, width=bw, label=label, color=col)
            for b in bars:
                h = b.get_height()
                ax.annotate(
                    f"{int(h)}",
                    xy=(b.get_x() + b.get_width() / 2, h),
                    xytext=(0, 2),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=7.5,
                )

        max_bt_val = max(
            int(r["backtracks"])
            for r in solvable_rows
            if r["config"] in ("1_Comb_Fixed", "3_Comb_JW", "4_Comb_JW_Pruned")
        )
        ax.set_ylim(0, max_bt_val * 1.15)
        ax.set_xticks(list(xp))
        ax.set_xticklabels(bt_puzzles, rotation=22, ha="right", fontsize=8.5)
        ax.set_ylabel("Total DPLL Backtracks")
        ax.set_title("DPLL Backtracking on Coupled Overlapping Constraint Puzzles: Fixed Order vs. Jeroslow-Wang")
        ax.grid(axis="y", linestyle="--", alpha=0.45)
        ax.legend(frameon=True)
        fig.tight_layout()
        p_bt = r_dir / "chart_backtracks_coupled.png"
        fig.savefig(p_bt)
        plt.close(fig)
        saved.append(p_bt)

    # Chart 4: Combinatorial vs Sequential Counter Clause Scaling
    fig, ax = plt.subplots(figsize=(8.6, 4.4), dpi=180)
    puzzles_ordered = [
        r["puzzle_id"] for r in solvable_rows if r["config"] == "1_Comb_Fixed"
    ]
    comb_clauses = [
        int(r["cnf_clauses"]) for r in solvable_rows if r["config"] == "1_Comb_Fixed"
    ]
    seq_clauses = [
        int(r["cnf_clauses"]) for r in solvable_rows if r["config"] == "2_Seq_Fixed"
    ]
    xp = range(len(puzzles_ordered))
    ax.plot(xp, comb_clauses, marker="o", linewidth=2, label="Combinatorial CNF (0 Aux Cardinality)")
    ax.plot(xp, seq_clauses, marker="s", linewidth=2, label="Sinz Sequential Counter CNF")
    ax.set_xticks(list(xp))
    ax.set_xticklabels(puzzles_ordered, rotation=35, ha="right", fontsize=7.5)
    ax.set_ylabel("Peak CNF Clauses")
    ax.set_title("CNF Formula Size: Direct Combinatorial vs. Sinz Sequential Counter")
    ax.grid(True, linestyle="--", alpha=0.45)
    ax.legend()
    fig.tight_layout()
    p3 = r_dir / "chart_clauses_comb_vs_seq.png"
    fig.savefig(p3)
    plt.close(fig)
    saved.append(p3)

    for s in saved:
        print(f"Generated chart: {s}")
    return saved


if __name__ == "__main__":
    generate_charts()
