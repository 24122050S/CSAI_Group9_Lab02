"""Generates a publication-grade System Architecture & Reveal Protocol diagram for the Report."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt


def build_architecture_diagram() -> Path:
    out_dir = Path(__file__).resolve().parent / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "architecture_diagram.png"

    fig, ax = plt.subplots(figsize=(11.5, 5.2), dpi=220)
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 5.2)
    ax.axis("off")

    def draw_zone(x, y, w, h, title, bg, border):
        rect = mpatches.FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.12,rounding_size=0.18",
            facecolor=bg,
            edgecolor=border,
            linewidth=1.8,
            linestyle="--",
        )
        ax.add_patch(rect)
        ax.text(
            x + 0.12,
            y + h - 0.22,
            title,
            fontsize=8.6,
            fontweight="bold",
            color=border,
            va="top",
        )

    def draw_box(x, y, w, h, title, subtitle, bg="#ffffff", border="#1e293b", title_col="#0f172a"):
        rect = mpatches.FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.06,rounding_size=0.12",
            facecolor=bg,
            edgecolor=border,
            linewidth=1.4,
        )
        ax.add_patch(rect)
        ax.text(
            x + w / 2,
            y + h * 0.64,
            title,
            fontsize=8.8,
            fontweight="bold",
            color=title_col,
            ha="center",
            va="center",
        )
        ax.text(
            x + w / 2,
            y + h * 0.28,
            subtitle,
            fontsize=7.3,
            color="#475569",
            ha="center",
            va="center",
        )

    def draw_arrow(x1, y1, x2, y2, label="", col="#334155", rad=0.0, ly_off=0.13):
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(
                arrowstyle="-|>,head_length=0.55,head_width=0.32",
                color=col,
                lw=1.45,
                connectionstyle=f"arc3,rad={rad}",
            ),
        )
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + ly_off
            ax.text(
                mx,
                my,
                label,
                fontsize=7.2,
                fontweight="bold",
                color=col,
                ha="center",
                va="center",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.88),
            )

    # 3 Major Security Domains
    draw_zone(0.25, 0.35, 3.1, 4.5, "1. Secret Domain (Hidden Ground Truth)", "#fff1f2", "#be123c")
    draw_zone(3.75, 0.35, 2.35, 4.5, "2. Firewall Boundary", "#fefce8", "#b45309")
    draw_zone(6.5, 0.35, 4.75, 4.5, "3. Public Logic & Solver Domain (Zero Hidden Access)", "#f0f9ff", "#0369a1")

    # Domain 1 boxes
    draw_box(0.5, 3.45, 2.6, 0.85, "Puzzle JSON Loader", "19 Verified Stages + Validator", "#ffffff", "#be123c")
    draw_box(0.5, 2.15, 2.6, 0.95, "GameEngine", "__ground_truth & __clues (Private)\nEntailment-Gated Card Flip", "#ffe4e6", "#be123c", "#881337")
    draw_box(0.5, 0.65, 2.6, 0.95, "SemanticEvaluator", "Direct Truth Evaluation\n(No CNFEncoder Dependency)", "#ffffff", "#be123c")

    # Domain 2 boxes
    draw_box(3.95, 2.85, 1.95, 1.2, "PublicGameState\n(Immutable DTO)", "Revealed Clues Only\nUnrevealed -> None", "#fef3c7", "#b45309", "#78350f")
    draw_box(3.95, 0.85, 1.95, 1.2, "Interactive Web GUI", "N×N Grid, 3D Flip,\nCNF Modal, Trace", "#ffffff", "#475569")

    # Domain 3 boxes
    draw_box(6.75, 3.5, 2.05, 0.88, "VariableManager &\nCNFEncoder", "Primary 1..N² | Aux > N²\n6 Core + 5 Extensions", "#ffffff", "#0369a1")
    draw_box(9.0, 3.5, 2.0, 0.88, "Custom DPLL Solver", "Unit Prop, Conflict, PLE,\nFixed / Jeroslow-Wang", "#e0f2fe", "#0369a1", "#0c4a6e")
    draw_box(6.75, 2.05, 4.25, 1.0, "DeductiveLogicAgent (No-Guess Loop)", "Refutation KB_t ∧ ¬L_i => UNSAT | Witness Pruning\nOutputs Step-by-Step DeductionTrace", "#dcfce7", "#15803d", "#14532d")
    draw_box(6.75, 0.65, 2.05, 0.95, "HintEngine (MUS)", "Deletion-Based Minimal\nClue Subset Extraction", "#f3e8ff", "#7e22ce", "#581c87")
    draw_box(9.0, 0.65, 2.0, 0.95, "UniquenessChecker", "Primary-Only Blocking\nClause Verification", "#ffffff", "#0369a1")

    # Arrows
    draw_arrow(1.8, 3.45, 1.8, 3.10, "", "#be123c")
    draw_arrow(1.8, 1.60, 1.8, 2.15, "Verify Truth", "#be123c", ly_off=0.0)
    draw_arrow(3.1, 2.75, 3.95, 3.35, "get_public_state()", "#b45309", ly_off=0.18)
    draw_arrow(5.20, 2.85, 5.20, 2.05, "Render KB_t", "#475569", ly_off=0.08)
    draw_arrow(5.90, 3.45, 6.75, 3.85, "Read-Only", "#0369a1", ly_off=0.16)
    draw_arrow(5.90, 3.25, 6.75, 2.65, "KB_t", "#15803d", ly_off=0.14)
    draw_arrow(8.80, 3.94, 9.00, 3.94, "CNF", "#0369a1", ly_off=0.14)
    draw_arrow(7.78, 3.05, 7.78, 3.50, "", "#0369a1")
    draw_arrow(10.0, 3.50, 10.0, 3.05, "SAT/UNSAT", "#0369a1", ly_off=0.0)
    draw_arrow(7.78, 2.05, 7.78, 1.60, "", "#7e22ce")
    draw_arrow(6.75, 2.25, 3.10, 2.25, "submit_verdict() -> ACCEPTED / NOT_PROVABLE / CONTRADICTED", "#15803d", rad=0.14, ly_off=-0.30)
    draw_arrow(3.95, 1.45, 3.10, 2.15, "Manual Verdict", "#475569", rad=-0.12, ly_off=-0.16)

    fig.tight_layout(pad=0.2)
    fig.savefig(out_path)
    plt.close(fig)
    print(f"Saved architecture diagram: {out_path}")
    return out_path


if __name__ == "__main__":
    build_architecture_diagram()
