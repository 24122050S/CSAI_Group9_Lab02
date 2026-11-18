"""Unit tests for board coordinates, region resolution, and clue parameter validation."""

from __future__ import annotations

import unittest

from logic.regions import RegionResolver
from logic.validator import ClueValidationError, ClueValidator
from models.board import BoardMetadata, CellCoord, CharacterInfo
from models.clue import Clue, RegionSpec
from models.enums import ClueType, Direction, ParityKind, Status


def make_sample_3x3_board() -> BoardMetadata:
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
    chars = [
        CharacterInfo(coord=CellCoord.parse(cid, 3), name=name, profession=job)
        for cid, name, job in names_jobs
    ]
    return BoardMetadata.from_characters(3, chars)


class TestRegionsAndValidation(unittest.TestCase):
    def setUp(self) -> None:
        self.board = make_sample_3x3_board()

    def test_row_and_col_regions(self) -> None:
        self.assertEqual(
            RegionResolver.resolve(RegionSpec.row_region(2), self.board),
            ("A2", "B2", "C2"),
        )
        self.assertEqual(
            RegionResolver.resolve(RegionSpec.col_region("C"), self.board),
            ("C1", "C2", "C3"),
        )

    def test_neighbors_corner_edge_interior(self) -> None:
        # Corner A1 -> 3 neighbors
        self.assertEqual(
            RegionResolver.resolve(RegionSpec.neighbors("A1"), self.board),
            ("B1", "A2", "B2"),
        )
        # Edge B1 -> 5 neighbors (resolvable by character name 'Bea' too)
        self.assertEqual(
            RegionResolver.resolve(RegionSpec.neighbors("Bea"), self.board),
            ("A1", "C1", "A2", "B2", "C2"),
        )
        # Interior B2 -> 8 neighbors, excluding B2 itself
        self.assertEqual(
            RegionResolver.resolve(RegionSpec.neighbors("B2"), self.board),
            ("A1", "B1", "C1", "A2", "C2", "A3", "B3", "C3"),
        )

    def test_explicit_cell_list_and_duplicates(self) -> None:
        self.assertEqual(
            RegionResolver.resolve(RegionSpec.cell_list(["C3", "Abel", "B1"]), self.board),
            ("A1", "B1", "C3"),
        )
        dup_clue = Clue(
            clue_id="c_dup",
            owner_cell="A1",
            clue_type=ClueType.EXACTLY,
            count=1,
            region=RegionSpec.cell_list(["A1", "Abel"]),
        )
        with self.assertRaises(ClueValidationError):
            ClueValidator.validate(dup_clue, self.board)

    def test_extension_1_advanced_regions(self) -> None:
        # Intersection of Neighbors(Eliza/B2) and Column C -> C1, C2, C3
        inter = RegionSpec.intersection(
            RegionSpec.neighbors("Eliza"),
            RegionSpec.col_region("C"),
        )
        self.assertEqual(RegionResolver.resolve(inter, self.board), ("C1", "C2", "C3"))

        # Common neighbors of A1 and C1 -> B1, B2
        cn = RegionSpec.common_neighbors("A1", "C1")
        self.assertEqual(RegionResolver.resolve(cn, self.board), ("B1", "B2"))

        # Corners -> A1, C1, A3, C3
        self.assertEqual(
            RegionResolver.resolve(RegionSpec.corners(), self.board),
            ("A1", "C1", "A3", "C3"),
        )

        # Boundary -> all except interior B2
        self.assertEqual(
            RegionResolver.resolve(RegionSpec.boundary(), self.board),
            ("A1", "B1", "C1", "A2", "C2", "A3", "B3", "C3"),
        )

        # Between A1 and C1 -> B1
        self.assertEqual(
            RegionResolver.resolve(RegionSpec.between("A1", "C1"), self.board),
            ("B1",),
        )

        # Directional: to the right of A2 -> B2, C2
        self.assertEqual(
            RegionResolver.resolve(
                RegionSpec.directional("A2", Direction.RIGHT), self.board
            ),
            ("B2", "C2"),
        )

        # Profession: Cook -> A1, C1, B3
        self.assertEqual(
            RegionResolver.resolve(RegionSpec.by_profession("Cook"), self.board),
            ("A1", "C1", "B3"),
        )

    def test_validator_rejects_invalid_parameters(self) -> None:
        # k > |R|
        bad_count = Clue(
            clue_id="bad1",
            owner_cell="A1",
            clue_type=ClueType.EXACTLY,
            count=4,
            region=RegionSpec.row_region(1),
        )
        with self.assertRaises(ClueValidationError):
            ClueValidator.validate(bad_count, self.board)

        # SAME with identical person
        bad_same = Clue(
            clue_id="bad2",
            owner_cell="A1",
            clue_type=ClueType.SAME,
            target1="A1",
            target2="Abel",
        )
        with self.assertRaises(ClueValidationError):
            ClueValidator.validate(bad_same, self.board)


if __name__ == "__main__":
    unittest.main()
