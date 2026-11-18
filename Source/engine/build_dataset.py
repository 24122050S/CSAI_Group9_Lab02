"""Builds and verifies the standard 17-puzzle Griductive suite (3x3, 4x4, 5x5 + coupled backtrack & diagnostic cases)."""

from __future__ import annotations

from pathlib import Path
import random

from agent.deductive_agent import DeductiveLogicAgent
from engine.game_engine import GameEngine
from engine.puzzle_generator import PuzzleGenerator
from engine.puzzle_loader import PuzzleLoader, SecretPuzzleData
from models.board import BoardMetadata, CellCoord, CharacterInfo
from models.clue import Clue, RegionSpec
from models.enums import (
    AgentTerminalState,
    ClueType,
    CompoundOperator,
    Direction,
    ParityKind,
    Status,
)


def _make_tutorial_3x3() -> SecretPuzzleData:
    names_jobs = [
        ("A1", "Abel", "Cook"),
        ("B1", "Bea", "Guard"),
        ("C1", "Clara", "Cook"),
        ("A2", "Derek", "Clerk"),
        ("B2", "Eliza", "Detective"),
        ("C2", "Franz", "Guard"),
        ("A3", "Grant", "Farmer"),
        ("B3", "Hannah", "Cook"),
        ("C3", "Ivy", "Detective"),
    ]
    board = BoardMetadata.from_characters(
        3,
        [
            CharacterInfo(CellCoord.parse(cid, 3), name, job)
            for cid, name, job in names_jobs
        ],
    )
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
        "A1": Clue("clue_A1", "A1", ClueType.EXACTLY, count=2, region=RegionSpec.row_region(1)),
        "B1": Clue("clue_B1", "B1", ClueType.DIFFERENT, target1="B1", target2="A2"),
        "C1": Clue("clue_C1", "C1", ClueType.EXACTLY, count=1, region=RegionSpec.col_region("C")),
        "A2": Clue("clue_A2", "A2", ClueType.EXACTLY, count=1, region=RegionSpec.row_region(2)),
        "B2": Clue("clue_B2", "B2", ClueType.AT_LEAST, count=3, region=RegionSpec.neighbors("B2")),
        "C2": Clue("clue_C2", "C2", ClueType.SAME, target1="B2", target2="A3"),
        "A3": Clue("clue_A3", "A3", ClueType.AT_MOST, count=1, region=RegionSpec.row_region(3)),
        "B3": Clue("clue_B3", "B3", ClueType.NO, region=RegionSpec.cell_list(["B3", "C3"])),
        "C3": Clue("clue_C3", "C3", ClueType.DIFFERENT, target1="A3", target2="C3"),
    }
    return SecretPuzzleData(
        puzzle_id="3x3_01_core_intro",
        title="3x3 Stage 1 — Tutorial Watch",
        difficulty="Easy",
        description="Handcrafted 3x3 tutorial puzzle using only the 6 core clue templates.",
        board=board,
        ground_truth=truth,
        clues=clues,
        initial_revealed=("A1",),
    )


def _make_ambiguous_3x3(board: BoardMetadata) -> SecretPuzzleData:
    truth = {
        "A1": Status.INNOCENT,
        "B1": Status.CRIMINAL,
        "C1": Status.CRIMINAL,
        "A2": Status.INNOCENT,
        "B2": Status.CRIMINAL,
        "C2": Status.INNOCENT,
        "A3": Status.INNOCENT,
        "B3": Status.CRIMINAL,
        "C3": Status.INNOCENT,
    }
    clues = {
        "A1": Clue("clue_A1", "A1", ClueType.EXACTLY, count=2, region=RegionSpec.row_region(1)),
        "B1": Clue("clue_B1", "B1", ClueType.EXACTLY, count=1, region=RegionSpec.row_region(2)),
        "C1": Clue("clue_C1", "C1", ClueType.EXACTLY, count=1, region=RegionSpec.row_region(3)),
        "A2": Clue("clue_A2", "A2", ClueType.AT_MOST, count=3, region=RegionSpec.col_region("B")),
        "B2": Clue("clue_B2", "B2", ClueType.AT_LEAST, count=1, region=RegionSpec.col_region("B")),
        "C2": Clue("clue_C2", "C2", ClueType.AT_MOST, count=1, region=RegionSpec.col_region("C")),
        "A3": Clue("clue_A3", "A3", ClueType.SAME, target1="A2", target2="A3"),
        "B3": Clue("clue_B3", "B3", ClueType.SAME, target1="B2", target2="B3"),
        "C3": Clue("clue_C3", "C3", ClueType.SAME, target1="C2", target2="C3"),
    }
    return SecretPuzzleData(
        puzzle_id="3x3_04_ambiguous_case",
        title="3x3 Diagnostic — Ambiguous State (No-Guess Stop)",
        difficulty="Diagnostic",
        description="Demonstrates no-guess behavior: solves B1 & C1, then halts cleanly as STUCK when multiple models remain.",
        board=board,
        ground_truth=truth,
        clues=clues,
        initial_revealed=("A1",),
    )


def _make_inconsistent_3x3(board: BoardMetadata) -> SecretPuzzleData:
    truth = {cid: Status.INNOCENT for cid in board.cell_ids}
    truth["B1"] = Status.CRIMINAL
    clues = {
        "A1": Clue("clue_A1", "A1", ClueType.EXACTLY, count=2, region=RegionSpec.row_region(1)),
        "A2": Clue("clue_A2", "A2", ClueType.NO, region=RegionSpec.row_region(1)),
    }
    return SecretPuzzleData(
        puzzle_id="3x3_05_inconsistent_case",
        title="3x3 Diagnostic — Contradictory Clues (UNSAT)",
        difficulty="Diagnostic",
        description="Demonstrates INCONSISTENT detection when active clues form an unsatisfiable CNF knowledge base.",
        board=board,
        ground_truth=truth,
        clues=clues,
        initial_revealed=("A1", "A2"),
        allow_inconsistent=True,
    )


def _make_3x3_compound_connected(board: BoardMetadata) -> SecretPuzzleData:
    """3x3 puzzle showcasing Extension 4 (COMPOUND AND/OR/IMPLIES) & Extension 5 (CONNECTED)."""
    truth = {
        "A1": Status.INNOCENT,
        "B1": Status.CRIMINAL,
        "C1": Status.CRIMINAL,
        "A2": Status.INNOCENT,
        "B2": Status.CRIMINAL,
        "C2": Status.INNOCENT,
        "A3": Status.INNOCENT,
        "B3": Status.CRIMINAL,
        "C3": Status.INNOCENT,
    }
    # Notice criminals are {B1, C1, B2, B3} -> T-shape, 100% orthogonally connected!
    # Row 1 to the right of Abel (A1) = {B1=1, C1=1}.
    clues = {
        # Opening A1 (Innocent): "Both people to the right of Abel are connected criminals" -> forces B1=1, C1=1!
        "A1": Clue.compound(
            "clue_A1",
            "A1",
            CompoundOperator.AND,
            [
                Clue("a1_1", "A1", ClueType.EXACTLY, count=2, region=RegionSpec.directional("Abel", Direction.RIGHT)),
                Clue.connected("a1_2", "A1", RegionSpec.directional("Abel", Direction.RIGHT)),
            ],
            text="Both people to the right of Abel are connected criminals.",
        ),
        # B1: "If Clara is a Criminal, then Derek (A2) and Franz (C2) are both Innocent."
        "B1": Clue.compound(
            "clue_B1",
            "B1",
            CompoundOperator.IMPLIES,
            [
                Clue("b1_1", "B1", ClueType.FACT, target="Clara", status=Status.CRIMINAL),
                Clue("b1_2", "B1", ClueType.NO, region=RegionSpec.cell_list(["A2", "C2"])),
            ],
            text="If Clara is a Criminal, then neither Derek nor Franz is a Criminal.",
        ),
        # C1: 2D connectivity + count on Col B / Neighbors of A2 {A1=0, B1=1, B2=1, A3=0, B3=1}!
        # Look! In Row 3 {A3, B3, C3}, say C1 says: "All criminals in Row 2 are connected, and Row 2 has at least 1 criminal."
        # Since A2=0 and C2=0 are forced by B1, "Row 2 has at least 1 criminal" forces B2 = CRIMINAL!
        "C1": Clue.compound(
            "clue_C1",
            "C1",
            CompoundOperator.AND,
            [
                Clue("c1_1", "C1", ClueType.AT_LEAST, count=1, region=RegionSpec.row_region(2)),
                Clue.connected("c1_2", "C1", RegionSpec.neighbors("Derek")),
            ],
            text="At least 1 person in row 2 is a Criminal, and all criminals neighboring Derek are connected.",
        ),
        # A2: "Either Derek is a Criminal or Hannah (B3) is a Criminal." -> since Derek(A2)=0, forces B3 = CRIMINAL!
        "A2": Clue.compound(
            "clue_A2",
            "A2",
            CompoundOperator.OR,
            [
                Clue("a2_1", "A2", ClueType.FACT, target="Derek", status=Status.CRIMINAL),
                Clue("a2_2", "A2", ClueType.FACT, target="Hannah", status=Status.CRIMINAL),
            ],
            text="Either Derek is a Criminal or Hannah is a Criminal.",
        ),
        # B2: "Hannah (B3) is one of Eliza's (B2) 3 criminal neighbors."
        # Eliza's neighbors are {A1=0, B1=1, C1=1, A2=0, C2=0, A3, B3=1, C3} -> already 3 criminals {B1,C1,B3}, forcing A3=0 & C3=0!
        "B2": Clue.compound(
            "clue_B2",
            "B2",
            CompoundOperator.AND,
            [
                Clue("b2_1", "B2", ClueType.FACT, target="Hannah", status=Status.CRIMINAL),
                Clue("b2_2", "B2", ClueType.EXACTLY, count=3, region=RegionSpec.neighbors("Eliza")),
            ],
            text="Hannah is one of Eliza's 3 criminal neighbors.",
        ),
        "C2": Clue.connected("clue_C2", "C2", RegionSpec.neighbors("Franz"), Status.CRIMINAL),
        "A3": Clue("clue_A3", "A3", ClueType.SAME, target1="A3", target2="C3"),
        "B3": Clue("clue_B3", "B3", ClueType.EXACTLY, count=1, region=RegionSpec.row_region(3)),
        "C3": Clue("clue_C3", "C3", ClueType.DIFFERENT, target1="B3", target2="C3"),
    }
    return SecretPuzzleData(
        puzzle_id="3x3_06_compound_connected",
        title="3x3 Stage 4 — Compound & Connected Clues",
        difficulty="Hard",
        description="Demonstrates Extension 4 (AND, OR, IMPLIES compound clues) and Extension 5 (1D & 2D orthogonal connectivity).",
        board=board,
        ground_truth=truth,
        clues=clues,
        initial_revealed=("A1",),
    )


def _make_5x5_figure1_showcase() -> SecretPuzzleData:
    """5x5 showcase modeling the exact clue patterns of Figure 1 in the project specification."""
    from engine.puzzle_generator import ALPHABETICAL_NAMES

    jobs = [
        "Astronaut", "Cook", "Guard", "Cook", "Detective",
        "Detective", "Clerk", "Guard", "Clerk", "Farmer",
        "Painter", "Farmer", "Astronaut", "Clerk", "Clerk",
        "Farmer", "Detective", "Guard", "Painter", "Farmer",
        "Cook", "Guard", "Clerk", "Detective", "Painter",
    ]
    chars = []
    idx = 0
    for r in range(1, 6):
        for c in range(5):
            chars.append(
                CharacterInfo(
                    coord=CellCoord(row=r, col_idx=c),
                    name=ALPHABETICAL_NAMES[idx],
                    profession=jobs[idx],
                )
            )
            idx += 1
    board = BoardMetadata.from_characters(5, chars)

    truth = {
        "A1": Status.INNOCENT,
        "B1": Status.CRIMINAL,
        "C1": Status.INNOCENT,
        "D1": Status.INNOCENT,
        "E1": Status.CRIMINAL,
        "A2": Status.CRIMINAL,
        "B2": Status.INNOCENT,
        "C2": Status.INNOCENT,
        "D2": Status.CRIMINAL,
        "E2": Status.INNOCENT,
        "A3": Status.INNOCENT,
        "B3": Status.INNOCENT,
        "C3": Status.CRIMINAL,
        "D3": Status.CRIMINAL,
        "E3": Status.INNOCENT,
        "A4": Status.INNOCENT,
        "B4": Status.CRIMINAL,
        "C4": Status.CRIMINAL,
        "D4": Status.INNOCENT,
        "E4": Status.INNOCENT,
        "A5": Status.CRIMINAL,
        "B5": Status.INNOCENT,
        "C5": Status.CRIMINAL,
        "D5": Status.INNOCENT,
        "E5": Status.INNOCENT,
    }

    right_of_abel = RegionSpec.directional("Abel", Direction.RIGHT)
    mara_nb = RegionSpec.neighbors("Mara")
    mara_nb_col_b = RegionSpec.intersection(mara_nb, RegionSpec.col_region("B"))

    clues = {
        # Figure 1 C1 style: "Exactly 2 of the 4 innocents neighboring Mara are in column B."
        "C1": Clue.compound(
            "clue_C1",
            "C1",
            CompoundOperator.AND,
            [
                Clue("c1_a", "C1", ClueType.EXACTLY, count=4, region=mara_nb, target_status=Status.INNOCENT),
                Clue("c1_b", "C1", ClueType.EXACTLY, count=2, region=mara_nb_col_b, target_status=Status.INNOCENT),
            ],
            text="Exactly 2 of the 4 innocents neighboring Mara are in column B.",
        ),
        # Figure 1 A5 style: "Uma is one of Priya's 2 criminal neighbors."
        "B4": Clue.compound(
            "clue_B4",
            "B4",
            CompoundOperator.AND,
            [
                Clue("b4_a", "B4", ClueType.FACT, target="Uma", status=Status.CRIMINAL),
                Clue("b4_b", "B4", ClueType.EXACTLY, count=2, region=RegionSpec.neighbors("Priya"), target_status=Status.CRIMINAL),
            ],
            text="Uma is one of Priya's 2 criminal neighbors.",
        ),
        # Figure 1 D5 style: "Both innocents to the right of Abel are connected."
        "E4": Clue.compound(
            "clue_E4",
            "E4",
            CompoundOperator.AND,
            [
                Clue("e4_a", "E4", ClueType.EXACTLY, count=2, region=right_of_abel, target_status=Status.INNOCENT),
                Clue.connected("e4_b", "E4", right_of_abel, target_status=Status.INNOCENT),
            ],
            text="Both innocents to the right of Abel are connected.",
        ),
        "C3": Clue.compound(
            "clue_C3",
            "C3",
            CompoundOperator.IMPLIES,
            [
                Clue("c3_a", "C3", ClueType.FACT, target="Clara", status=Status.INNOCENT),
                Clue("c3_b", "C3", ClueType.FACT, target="Derek", status=Status.INNOCENT),
            ],
            text="If Clara is Innocent, then Derek is Innocent.",
        ),
        # 2D 5-cell neighborhood connectivity around Wendy (C5): {B4=1, C4=1, D4=0, B5=0, D5=0}
        "B2": Clue.connected(
            "clue_B2",
            "B2",
            RegionSpec.neighbors("Wendy"),
            target_status=Status.CRIMINAL,
            text="All criminals neighboring Wendy are orthogonally connected.",
        ),
        "B3": Clue("clue_B3", "B3", ClueType.NO, region=RegionSpec.cell_list(["A1", "C2", "D4"])),
        "A3": Clue("clue_A3", "A3", ClueType.EXACTLY, count=2, region=RegionSpec.row_region(2)),
        "B1": Clue("clue_B1", "B1", ClueType.DIFFERENT, target1="E1", target2="E2"),
        "D1": Clue("clue_D1", "D1", ClueType.NO, region=RegionSpec.cell_list(["E3", "A4"])),
        "E1": Clue.compound(
            "clue_E1",
            "E1",
            CompoundOperator.OR,
            [
                Clue("e1_a", "E1", ClueType.FACT, target="Abel", status=Status.CRIMINAL),
                Clue("e1_b", "E1", ClueType.FACT, target="Wendy", status=Status.CRIMINAL),
            ],
            text="Either Abel is a Criminal or Wendy is a Criminal.",
        ),
        "A5": Clue("clue_A5", "A5", ClueType.EXACTLY, count=2, region=RegionSpec.row_region(5)),
        "B5": Clue("clue_B5", "B5", ClueType.PARITY, parity=ParityKind.ODD, region=RegionSpec.col_region("C")),
        "A1": Clue("clue_A1", "A1", ClueType.EQUAL_CRIMINALS, region=RegionSpec.row_region(1), region2=RegionSpec.row_region(5)),
        "A2": Clue("clue_A2", "A2", ClueType.SAME, target1="D2", target2="D3"),
        "C2": Clue("clue_C2", "C2", ClueType.DIFFERENT, target1="C2", target2="C3"),
        "D2": Clue("clue_D2", "D2", ClueType.SAME, target1="C4", target2="C5"),
        "E2": Clue("clue_E2", "E2", ClueType.NO, region=RegionSpec.cell_list(["E3", "E4", "E5"])),
        "D3": Clue("clue_D3", "D3", ClueType.EXACTLY, count=2, region=RegionSpec.row_region(3)),
        "E3": Clue("clue_E3", "E3", ClueType.DIFFERENT, target1="A4", target2="B4"),
        "A4": Clue("clue_A4", "A4", ClueType.EXACTLY, count=2, region=RegionSpec.row_region(4)),
        "C4": Clue("clue_C4", "C4", ClueType.SAME, target1="D4", target2="E4"),
        "D4": Clue("clue_D4", "D4", ClueType.DIFFERENT, target1="C5", target2="D5"),
        "C5": Clue("clue_C5", "C5", ClueType.SAME, target1="D5", target2="E5"),
        "D5": Clue("clue_D5", "D5", ClueType.EQUAL_CRIMINALS, region=RegionSpec.row_region(1), region2=RegionSpec.row_region(5)),
        "E5": Clue("clue_E5", "E5", ClueType.EXACTLY, count=2, region=RegionSpec.corners()),
    }

    return SecretPuzzleData(
        puzzle_id="5x5_06_figure1_showcase",
        title="5x5 Showcase — Figure 1 Compound & Connected",
        difficulty="Showcase",
        description="Models the exact clue patterns from Figure 1 of the specification (Compound AND/OR/IMPLIES, Intersection, and 1D/2D Orthogonal Connectivity).",
        board=board,
        ground_truth=truth,
        clues=clues,
        initial_revealed=("C1", "C3", "B4", "E4"),
    )


def _make_4x4_coupled_crucible() -> SecretPuzzleData:
    """Coupled overlapping 4-cell cardinality constraints with zero direct unit clauses."""
    rng = random.Random(406)
    board = PuzzleGenerator.build_board(4, rng)
    truth = {
        "A1": Status.INNOCENT,
        "B1": Status.CRIMINAL,
        "C1": Status.INNOCENT,
        "D1": Status.CRIMINAL,
        "A2": Status.CRIMINAL,
        "B2": Status.INNOCENT,
        "C2": Status.CRIMINAL,
        "D2": Status.INNOCENT,
        "A3": Status.CRIMINAL,
        "B3": Status.CRIMINAL,
        "C3": Status.CRIMINAL,
        "D3": Status.INNOCENT,
        "A4": Status.INNOCENT,
        "B4": Status.INNOCENT,
        "C4": Status.INNOCENT,
        "D4": Status.INNOCENT,
    }
    clues = {
        "A1": Clue("clue_A1", "A1", ClueType.EXACTLY, count=2, region=RegionSpec.cell_list(["B3", "C3", "D3", "B4"])),
        "B1": Clue("clue_B1", "B1", ClueType.AT_MOST, count=2, region=RegionSpec.cell_list(["B3", "C3", "D3", "D4"])),
        "C1": Clue("clue_C1", "C1", ClueType.AT_MOST, count=2, region=RegionSpec.cell_list(["B3", "C3", "B4", "D4"])),
        "D1": Clue("clue_D1", "D1", ClueType.AT_MOST, count=2, region=RegionSpec.cell_list(["B3", "D3", "B4", "D4"])),
        "A4": Clue("clue_A4", "A4", ClueType.EXACTLY, count=3, region=RegionSpec.cell_list(["A2", "B2", "C2", "D2", "A3", "C4"])),
        "D4": Clue("clue_D4", "D4", ClueType.AT_MOST, count=1, region=RegionSpec.cell_list(["C3", "D3", "B4"])),
        "B3": Clue("clue_B3", "B3", ClueType.AT_MOST, count=2, region=RegionSpec.cell_list(["A2", "B2", "C2", "D2", "C4"])),
        "A3": Clue("clue_A3", "A3", ClueType.AT_LEAST, count=2, region=RegionSpec.cell_list(["A2", "B2", "C2", "D2"])),
        "C4": Clue("clue_C4", "C4", ClueType.AT_MOST, count=1, region=RegionSpec.cell_list(["B2", "C2", "D2"])),
        "A2": Clue("clue_A2", "A2", ClueType.AT_LEAST, count=2, region=RegionSpec.cell_list(["C2", "C3", "D3"])),
        "C2": Clue("clue_C2", "C2", ClueType.AT_LEAST, count=2, region=RegionSpec.cell_list(["A2", "C3", "B4"])),
        "B2": Clue("clue_B2", "B2", ClueType.DIFFERENT, target1="C3", target2="D3"),
        "D2": Clue("clue_D2", "D2", ClueType.DIFFERENT, target1="B2", target2="C3"),
        "B4": Clue("clue_B4", "B4", ClueType.SAME, target1="B4", target2="D3"),
        "C3": Clue("clue_C3", "C3", ClueType.DIFFERENT, target1="C3", target2="D3"),
        "D3": Clue("clue_D3", "D3", ClueType.EXACTLY, count=8, region=RegionSpec.boundary(), target_status=Status.INNOCENT),
    }
    return SecretPuzzleData(
        puzzle_id="4x4_06_coupled_crucible",
        title="4x4 Coupled 1 — Overlapping Crucible (Backtrack)",
        difficulty="Coupled-Hard",
        description="Multi-wave coupled cardinality constraints with zero direct unit clauses, forcing recursive DPLL branching & backtracking.",
        board=board,
        ground_truth=truth,
        clues=clues,
        initial_revealed=("A1", "B1", "C1", "D1", "A4"),
    )


def _make_4x4_coupled_parity_matrix() -> SecretPuzzleData:
    """Couples 6-variable Tseitin XOR parity with overlapping cardinality bounds."""
    rng = random.Random(407)
    board = PuzzleGenerator.build_board(4, rng)
    truth = {
        "A1": Status.CRIMINAL,
        "B1": Status.INNOCENT,
        "C1": Status.CRIMINAL,
        "D1": Status.INNOCENT,
        "A2": Status.INNOCENT,
        "B2": Status.CRIMINAL,
        "C2": Status.INNOCENT,
        "D2": Status.CRIMINAL,
        "A3": Status.CRIMINAL,
        "B3": Status.CRIMINAL,
        "C3": Status.INNOCENT,
        "D3": Status.CRIMINAL,
        "A4": Status.INNOCENT,
        "B4": Status.INNOCENT,
        "C4": Status.INNOCENT,
        "D4": Status.INNOCENT,
    }
    clues = {
        "A1": Clue("clue_A1", "A1", ClueType.PARITY, parity=ParityKind.ODD, region=RegionSpec.cell_list(["A2", "B2", "C2", "D2", "A3", "C4"])),
        "B1": Clue("clue_B1", "B1", ClueType.EXACTLY, count=2, region=RegionSpec.cell_list(["B3", "C3", "D3", "B4"])),
        "C1": Clue("clue_C1", "C1", ClueType.AT_MOST, count=2, region=RegionSpec.cell_list(["B3", "C3", "D3", "D4"])),
        "D1": Clue("clue_D1", "D1", ClueType.AT_MOST, count=2, region=RegionSpec.cell_list(["B3", "C3", "B4", "D4"])),
        "A4": Clue("clue_A4", "A4", ClueType.AT_MOST, count=2, region=RegionSpec.cell_list(["C3", "D3", "B4", "D4"])),
        "D4": Clue("clue_D4", "D4", ClueType.AT_MOST, count=1, region=RegionSpec.cell_list(["C3", "D3", "B4"])),
        "B3": Clue("clue_B3", "B3", ClueType.EXACTLY, count=3, region=RegionSpec.cell_list(["A2", "B2", "C2", "D2", "A3"])),
        "C4": Clue("clue_C4", "C4", ClueType.AT_MOST, count=2, region=RegionSpec.cell_list(["A2", "B2", "C2", "D2"])),
        "A3": Clue("clue_A3", "A3", ClueType.AT_LEAST, count=2, region=RegionSpec.cell_list(["B2", "C2", "D2"])),
        "A2": Clue("clue_A2", "A2", ClueType.AT_MOST, count=1, region=RegionSpec.cell_list(["B2", "C2"])),
        "D2": Clue("clue_D2", "D2", ClueType.AT_LEAST, count=2, region=RegionSpec.cell_list(["B2", "D3", "B4"])),
        "B2": Clue("clue_B2", "B2", ClueType.AT_LEAST, count=2, region=RegionSpec.cell_list(["A3", "D3", "C3"])),
        "C2": Clue("clue_C2", "C2", ClueType.SAME, target1="C3", target2="B4"),
        "C3": Clue("clue_C3", "C3", ClueType.DIFFERENT, target1="C3", target2="D3"),
        "D3": Clue("clue_D3", "D3", ClueType.MORE_CRIMINALS, region=RegionSpec.row_region(3), region2=RegionSpec.row_region(4)),
        "B4": Clue("clue_B4", "B4", ClueType.PARITY, parity=ParityKind.EVEN, region=RegionSpec.col_region("B")),
    }
    return SecretPuzzleData(
        puzzle_id="4x4_07_coupled_parity_matrix",
        title="4x4 Coupled 2 — Parity & Cardinality Matrix",
        difficulty="Coupled-Hard",
        description="Couples 6-variable Tseitin XOR parity with cardinality bounds so deduction requires multi-clause DPLL backtracking.",
        board=board,
        ground_truth=truth,
        clues=clues,
        initial_revealed=("A1", "B1", "C1", "D1", "A4"),
    )


def _make_5x5_coupled_labyrinth() -> SecretPuzzleData:
    """5x5 coupled stress puzzle with a 7-cell middle band above nested non-unit cores."""
    rng = random.Random(504)
    board = PuzzleGenerator.build_board(5, rng)
    truth = {
        "A1": Status.INNOCENT,
        "B1": Status.CRIMINAL,
        "C1": Status.INNOCENT,
        "D1": Status.CRIMINAL,
        "E1": Status.INNOCENT,
        "A2": Status.CRIMINAL,
        "B2": Status.INNOCENT,
        "C2": Status.CRIMINAL,
        "D2": Status.INNOCENT,
        "E2": Status.CRIMINAL,
        "A3": Status.CRIMINAL,
        "B3": Status.INNOCENT,
        "C3": Status.CRIMINAL,
        "D3": Status.INNOCENT,
        "E3": Status.INNOCENT,
        "A4": Status.INNOCENT,
        "B4": Status.CRIMINAL,
        "C4": Status.CRIMINAL,
        "D4": Status.INNOCENT,
        "E4": Status.INNOCENT,
        "A5": Status.CRIMINAL,
        "B5": Status.INNOCENT,
        "C5": Status.INNOCENT,
        "D5": Status.CRIMINAL,
        "E5": Status.INNOCENT,
    }
    clues = {
        "A1": Clue("clue_A1", "A1", ClueType.EXACTLY, count=4, region=RegionSpec.cell_list(["A2", "B2", "C2", "D2", "E2", "A3", "B3"])),
        "B1": Clue("clue_B1", "B1", ClueType.EXACTLY, count=2, region=RegionSpec.cell_list(["B4", "C4", "D4", "E4"])),
        "C1": Clue("clue_C1", "C1", ClueType.AT_MOST, count=2, region=RegionSpec.cell_list(["B4", "C4", "D4", "E5"])),
        "D1": Clue("clue_D1", "D1", ClueType.AT_MOST, count=2, region=RegionSpec.cell_list(["B4", "C4", "E4", "E5"])),
        "E1": Clue("clue_E1", "E1", ClueType.AT_MOST, count=2, region=RegionSpec.cell_list(["B4", "D4", "E4", "E5"])),
        "E5": Clue("clue_E5", "E5", ClueType.AT_MOST, count=1, region=RegionSpec.cell_list(["C4", "D4", "E4"])),
        "B4": Clue("clue_B4", "B4", ClueType.AT_LEAST, count=4, region=RegionSpec.cell_list(["A2", "B2", "C2", "D2", "E2", "A3"])),
        "B3": Clue("clue_B3", "B3", ClueType.AT_MOST, count=3, region=RegionSpec.cell_list(["B2", "C2", "D2", "E2", "A3"])),
        "A2": Clue("clue_A2", "A2", ClueType.AT_LEAST, count=3, region=RegionSpec.cell_list(["C2", "D2", "E2", "A3"])),
        "B2": Clue("clue_B2", "B2", ClueType.AT_MOST, count=2, region=RegionSpec.cell_list(["D2", "E2", "A3"])),
        "C2": Clue("clue_C2", "C2", ClueType.AT_MOST, count=1, region=RegionSpec.cell_list(["D2", "E2"])),
        "A3": Clue("clue_A3", "A3", ClueType.AT_LEAST, count=2, region=RegionSpec.cell_list(["E2", "C4", "D4"])),
        "D2": Clue("clue_D2", "D2", ClueType.DIFFERENT, target1="C4", target2="D4"),
        "E2": Clue("clue_E2", "E2", ClueType.AT_LEAST, count=2, region=RegionSpec.cell_list(["C3", "C4", "E3"])),
        "E4": Clue("clue_E4", "E4", ClueType.NO, region=RegionSpec.cell_list(["D3", "E3", "A4"])),
        "D3": Clue("clue_D3", "D3", ClueType.EXACTLY, count=2, region=RegionSpec.row_region(5)),
        "E3": Clue("clue_E3", "E3", ClueType.NO, region=RegionSpec.cell_list(["B5", "C5"])),
        "A4": Clue("clue_A4", "A4", ClueType.SAME, target1="A5", target2="D5"),
        "C3": Clue("clue_C3", "C3", ClueType.DIFFERENT, target1="C3", target2="D4"),
        "C4": Clue("clue_C4", "C4", ClueType.PARITY, parity=ParityKind.EVEN, region=RegionSpec.row_region(4)),
        "D4": Clue("clue_D4", "D4", ClueType.DIFFERENT, target1="A5", target2="B5"),
        "A5": Clue("clue_A5", "A5", ClueType.SAME, target1="B5", target2="C5"),
        "B5": Clue("clue_B5", "B5", ClueType.DIFFERENT, target1="C5", target2="D5"),
        "C5": Clue("clue_C5", "C5", ClueType.MORE_CRIMINALS, region=RegionSpec.row_region(2), region2=RegionSpec.row_region(4)),
        "D5": Clue("clue_D5", "D5", ClueType.EXACTLY, count=1, region=RegionSpec.corners(), target_status=Status.CRIMINAL),
    }
    return SecretPuzzleData(
        puzzle_id="5x5_04_coupled_labyrinth",
        title="5x5 Stress 4 — Coupled Labyrinth (Backtrack)",
        difficulty="Coupled-Stress",
        description="5x5 coupled stress puzzle with a 7-cell unconstrained-looking middle band above nested non-unit cardinality cores.",
        board=board,
        ground_truth=truth,
        clues=clues,
        initial_revealed=("A1", "B1", "C1", "D1", "E1"),
    )


def _make_5x5_coupled_fortress() -> SecretPuzzleData:
    """Extreme 5x5 backtracking stress puzzle (~645 backtracks on Fixed Order vs ~143 on JW)."""
    rng = random.Random(505)
    board = PuzzleGenerator.build_board(5, rng)
    truth = {
        "A1": Status.CRIMINAL,
        "B1": Status.INNOCENT,
        "C1": Status.CRIMINAL,
        "D1": Status.INNOCENT,
        "E1": Status.CRIMINAL,
        "A2": Status.CRIMINAL,
        "B2": Status.INNOCENT,
        "C2": Status.CRIMINAL,
        "D2": Status.INNOCENT,
        "E2": Status.CRIMINAL,
        "A3": Status.INNOCENT,
        "B3": Status.CRIMINAL,
        "C3": Status.INNOCENT,
        "D3": Status.CRIMINAL,
        "E3": Status.INNOCENT,
        "A4": Status.INNOCENT,
        "B4": Status.CRIMINAL,
        "C4": Status.INNOCENT,
        "D4": Status.CRIMINAL,
        "E4": Status.INNOCENT,
        "A5": Status.CRIMINAL,
        "B5": Status.INNOCENT,
        "C5": Status.CRIMINAL,
        "D5": Status.INNOCENT,
        "E5": Status.INNOCENT,
    }
    clues = {
        "A1": Clue("clue_A1", "A1", ClueType.EXACTLY, count=4, region=RegionSpec.cell_list(["A2", "B2", "C2", "D2", "E2", "A3", "B3", "C3"])),
        "B1": Clue("clue_B1", "B1", ClueType.EXACTLY, count=2, region=RegionSpec.cell_list(["B4", "C4", "D4", "E4"])),
        "C1": Clue("clue_C1", "C1", ClueType.AT_MOST, count=2, region=RegionSpec.cell_list(["B4", "C4", "D4", "E5"])),
        "D1": Clue("clue_D1", "D1", ClueType.AT_MOST, count=2, region=RegionSpec.cell_list(["B4", "C4", "E4", "E5"])),
        "E1": Clue("clue_E1", "E1", ClueType.AT_MOST, count=2, region=RegionSpec.cell_list(["C4", "D4", "E4", "E5"])),
        "E5": Clue("clue_E5", "E5", ClueType.AT_MOST, count=1, region=RegionSpec.cell_list(["C4", "D4", "E4"])),
        "B4": Clue("clue_B4", "B4", ClueType.AT_LEAST, count=4, region=RegionSpec.cell_list(["A2", "B2", "C2", "D2", "E2", "A3", "B3"])),
        "C3": Clue("clue_C3", "C3", ClueType.AT_MOST, count=3, region=RegionSpec.cell_list(["B2", "C2", "D2", "E2", "A3", "B3"])),
        "A2": Clue("clue_A2", "A2", ClueType.AT_LEAST, count=3, region=RegionSpec.cell_list(["C2", "D2", "E2", "A3", "B3"])),
        "B2": Clue("clue_B2", "B2", ClueType.AT_MOST, count=2, region=RegionSpec.cell_list(["D2", "E2", "A3", "B3"])),
        "C2": Clue("clue_C2", "C2", ClueType.AT_LEAST, count=2, region=RegionSpec.cell_list(["E2", "A3", "B3"])),
        "D2": Clue("clue_D2", "D2", ClueType.AT_MOST, count=1, region=RegionSpec.cell_list(["A3", "B3"])),
        "E2": Clue("clue_E2", "E2", ClueType.AT_LEAST, count=2, region=RegionSpec.cell_list(["B3", "D4", "E4"])),
        "A3": Clue("clue_A3", "A3", ClueType.SAME, target1="C4", target2="E4"),
        "B3": Clue("clue_B3", "B3", ClueType.AT_LEAST, count=2, region=RegionSpec.cell_list(["D3", "D4", "E3"])),
        "C4": Clue("clue_C4", "C4", ClueType.NO, region=RegionSpec.cell_list(["E3", "A4", "B5", "D5"])),
        "D4": Clue("clue_D4", "D4", ClueType.EXACTLY, count=2, region=RegionSpec.row_region(5)),
        "E4": Clue("clue_E4", "E4", ClueType.DIFFERENT, target1="D3", target2="E3"),
        "D3": Clue("clue_D3", "D3", ClueType.SAME, target1="A5", target2="C5"),
        "E3": Clue("clue_E3", "E3", ClueType.DIFFERENT, target1="A4", target2="A5"),
        "A4": Clue("clue_A4", "A4", ClueType.SAME, target1="B5", target2="D5"),
        "A5": Clue("clue_A5", "A5", ClueType.DIFFERENT, target1="A5", target2="B5"),
        "B5": Clue("clue_B5", "B5", ClueType.DIFFERENT, target1="C5", target2="D5"),
        "C5": Clue("clue_C5", "C5", ClueType.PARITY, parity=ParityKind.EVEN, region=RegionSpec.row_region(5)),
        "D5": Clue("clue_D5", "D5", ClueType.EXACTLY, count=3, region=RegionSpec.corners(), target_status=Status.CRIMINAL),
    }
    return SecretPuzzleData(
        puzzle_id="5x5_05_coupled_fortress",
        title="5x5 Stress 5 — Coupled Fortress (Extreme Backtrack)",
        difficulty="Coupled-Stress",
        description="Extreme 5x5 backtracking benchmark with an 8-cell coupled band (C(8,4)=70 combinations) above nested non-unit cores.",
        board=board,
        ground_truth=truth,
        clues=clues,
        initial_revealed=("A1", "B1", "C1", "D1", "E1"),
    )


def build_all_puzzles(base_dir: Path) -> list[Path]:
    saved_paths: list[Path] = []
    tut = _make_tutorial_3x3()
    p_tut = base_dir / "3x3" / f"{tut.puzzle_id}.json"
    PuzzleLoader.save_file(tut, p_tut)
    saved_paths.append(p_tut)

    specs = [
        ("3x3", "3x3_02_neighbors_chain", "3x3 Stage 2 — Neighbor Watch", 3, 102, "Medium", False, 2, "3x3 core puzzle emphasizing neighbor and column counts."),
        ("3x3", "3x3_03_extensions_mix", "3x3 Stage 3 — Parity & Intersections", 3, 205, "Hard", True, 2, "3x3 puzzle showcasing Extension 1, 2, and 3 clues."),
        ("4x4", "4x4_01_core_patrol", "4x4 Stage 1 — Night Patrol", 4, 301, "Easy", False, 3, "4x4 puzzle using strictly the 6 core clue templates."),
        ("4x4", "4x4_02_core_precinct", "4x4 Stage 2 — Precinct Ledger", 4, 409, "Medium", False, 2, "4x4 core puzzle with 14 sequential deduction steps."),
        ("4x4", "4x4_03_ext_intersections", "4x4 Stage 3 — Crossfire", 4, 512, "Medium", True, 2, "4x4 puzzle combining intersection regions, parity, and count comparisons."),
        ("4x4", "4x4_04_ext_professions", "4x4 Stage 4 — Guild Investigation", 4, 618, "Hard", True, 1, "4x4 puzzle starting from a single card (15 deduction steps)."),
        ("4x4", "4x4_05_ext_deep_chain", "4x4 Stage 5 — Silent Witness", 4, 727, "Hard", True, 2, "4x4 puzzle featuring deep multi-wave deduction chains."),
        ("5x5", "5x5_01_core_metropolis", "5x5 Stress 1 — Metropolis (Core)", 5, 804, "Stress", False, 3, "5x5 stress puzzle (25 characters) with core cardinality encodings."),
        ("5x5", "5x5_02_ext_grand_inquest", "5x5 Stress 2 — Grand Inquest (Extensions)", 5, 915, "Stress", True, 2, "5x5 stress puzzle exercising advanced regions, comparisons, and parity."),
        ("5x5", "5x5_03_single_seed_stress", "5x5 Stress 3 — Lone Informant (24 Steps)", 5, 1029, "Stress", True, 1, "5x5 stress test starting from a single face-up informant (24 steps)."),
    ]

    for folder, pid, title, n, seed, diff, ext, n_init, desc in specs:
        puzzle = PuzzleGenerator.generate(
            puzzle_id=pid,
            title=title,
            grid_size=n,
            seed=seed,
            difficulty=diff,
            include_extensions=ext,
            num_initial_revealed=n_init,
            description=desc,
        )
        out = base_dir / folder / f"{pid}.json"
        PuzzleLoader.save_file(puzzle, out)
        saved_paths.append(out)

    # Handcrafted Coupled Backtrack & Extension 4-5 Showcase Puzzles
    for folder, special_p in [
        ("3x3", _make_3x3_compound_connected(tut.board)),
        ("4x4", _make_4x4_coupled_crucible()),
        ("4x4", _make_4x4_coupled_parity_matrix()),
        ("5x5", _make_5x5_coupled_labyrinth()),
        ("5x5", _make_5x5_coupled_fortress()),
        ("5x5", _make_5x5_figure1_showcase()),
    ]:
        out = base_dir / folder / f"{special_p.puzzle_id}.json"
        PuzzleLoader.save_file(special_p, out)
        saved_paths.append(out)

    # Diagnostic 3x3 puzzles
    amb = _make_ambiguous_3x3(tut.board)
    p_amb = base_dir / "3x3" / f"{amb.puzzle_id}.json"
    PuzzleLoader.save_file(amb, p_amb)
    saved_paths.append(p_amb)

    inc = _make_inconsistent_3x3(tut.board)
    p_inc = base_dir / "3x3" / f"{inc.puzzle_id}.json"
    PuzzleLoader.save_file(inc, p_inc)
    saved_paths.append(p_inc)

    agent = DeductiveLogicAgent(use_witness_pruning=True)
    for path in saved_paths:
        loaded = PuzzleLoader.load_file(path)
        eng = GameEngine(loaded)
        rep = agent.solve(eng)
        if "ambiguous" in loaded.puzzle_id:
            assert rep.terminal_state == AgentTerminalState.STUCK
        elif "inconsistent" in loaded.puzzle_id:
            assert rep.terminal_state == AgentTerminalState.INCONSISTENT
        else:
            assert rep.terminal_state == AgentTerminalState.SOLVED
        print(
            f"[OK] {loaded.puzzle_id:30s} | {loaded.board.grid_size}x{loaded.board.grid_size} "
            f"| steps={rep.deduction_steps:2d} | waves={rep.reveal_waves:2d} "
            f"| state={rep.terminal_state.value}"
        )

    return saved_paths


if __name__ == "__main__":
    puzzles_root = Path(__file__).resolve().parent.parent / "puzzles"
    build_all_puzzles(puzzles_root)
