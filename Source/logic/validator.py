"""Clue parameter and region validation (Section 3.2 & 4.2)."""

from __future__ import annotations

from logic.regions import RegionResolver
from models.board import BoardMetadata
from models.clue import Clue, RegionSpec
from models.enums import ClueType, CompoundOperator, ParityKind, Status


class ClueValidationError(ValueError):
    """Raised when a structured clue has invalid parameters or region references."""


class ClueValidator:
    """Validates Clue and RegionSpec instances against a BoardMetadata topology."""

    @classmethod
    def validate_region(cls, region: RegionSpec | None, board: BoardMetadata) -> tuple[str, ...]:
        """Validate `region` and return its resolved tuple of cell IDs."""
        if region is None:
            raise ClueValidationError("Clue requires a region specification, got None.")
        try:
            cells = RegionResolver.resolve(region, board)
        except (ValueError, KeyError) as exc:
            raise ClueValidationError(f"Invalid region {region}: {exc}") from exc
        return cells

    @classmethod
    def validate(cls, clue: Clue, board: BoardMetadata) -> None:
        """Validate all parameters and referenced cells/regions of `clue`."""
        if clue.owner_cell:
            try:
                board.resolve_cell_id(clue.owner_cell)
            except KeyError as exc:
                raise ClueValidationError(
                    f"Invalid owner_cell {clue.owner_cell!r} in clue {clue.clue_id!r}."
                ) from exc

        if clue.target_status not in (Status.CRIMINAL, Status.INNOCENT):
            raise ClueValidationError(
                f"Invalid target_status {clue.target_status!r} in clue {clue.clue_id!r}."
            )

        ct = clue.clue_type

        if ct == ClueType.FACT:
            if not clue.target:
                raise ClueValidationError(f"FACT clue {clue.clue_id!r} missing `target`.")
            try:
                board.resolve_cell_id(clue.target)
            except KeyError as exc:
                raise ClueValidationError(
                    f"FACT clue {clue.clue_id!r} references unknown character {clue.target!r}."
                ) from exc
            if clue.status not in (Status.CRIMINAL, Status.INNOCENT):
                raise ClueValidationError(
                    f"FACT clue {clue.clue_id!r} requires status CRIMINAL or INNOCENT, "
                    f"got {clue.status!r}."
                )
            return

        if ct in (ClueType.SAME, ClueType.DIFFERENT):
            if not clue.target1 or not clue.target2:
                raise ClueValidationError(
                    f"{ct.value} clue {clue.clue_id!r} requires `target1` and `target2`."
                )
            try:
                c1 = board.resolve_cell_id(clue.target1)
                c2 = board.resolve_cell_id(clue.target2)
            except KeyError as exc:
                raise ClueValidationError(
                    f"{ct.value} clue {clue.clue_id!r} references unknown character: {exc}"
                ) from exc
            if c1 == c2:
                raise ClueValidationError(
                    f"{ct.value} clue {clue.clue_id!r} requires two distinct people, "
                    f"both resolved to {c1}."
                )
            return

        if ct == ClueType.NO:
            if clue.count is not None and clue.count != 0:
                raise ClueValidationError(
                    f"NO clue {clue.clue_id!r} cannot specify non-zero count {clue.count}."
                )
            cls.validate_region(clue.region, board)
            return

        if ct in (ClueType.EXACTLY, ClueType.AT_LEAST, ClueType.AT_MOST):
            cells = cls.validate_region(clue.region, board)
            if clue.count is None or not isinstance(clue.count, int) or isinstance(clue.count, bool):
                raise ClueValidationError(
                    f"{ct.value} clue {clue.clue_id!r} requires integer `count`."
                )
            if not (0 <= clue.count <= len(cells)):
                raise ClueValidationError(
                    f"{ct.value} clue {clue.clue_id!r} has count k={clue.count} outside "
                    f"valid range [0, |R|={len(cells)}]."
                )
            return

        if ct in (ClueType.MORE_CRIMINALS, ClueType.EQUAL_CRIMINALS):
            cls.validate_region(clue.region, board)
            cls.validate_region(clue.region2, board)
            return

        if ct == ClueType.PARITY:
            cls.validate_region(clue.region, board)
            if clue.parity not in (ParityKind.ODD, ParityKind.EVEN):
                raise ClueValidationError(
                    f"PARITY clue {clue.clue_id!r} requires parity ODD or EVEN, "
                    f"got {clue.parity!r}."
                )
            return

        if ct == ClueType.CONNECTED:
            cells = cls.validate_region(clue.region, board)
            if len(cells) == 0:
                raise ClueValidationError(
                    f"CONNECTED clue {clue.clue_id!r} requires a non-empty region."
                )
            return

        if ct == ClueType.COMPOUND:
            if clue.operator not in (
                CompoundOperator.AND,
                CompoundOperator.OR,
                CompoundOperator.IMPLIES,
            ):
                raise ClueValidationError(
                    f"COMPOUND clue {clue.clue_id!r} requires operator AND, OR, or IMPLIES, "
                    f"got {clue.operator!r}."
                )
            if len(clue.sub_clues) < 2:
                raise ClueValidationError(
                    f"COMPOUND clue {clue.clue_id!r} requires at least 2 sub_clues."
                )
            if clue.operator == CompoundOperator.IMPLIES and len(clue.sub_clues) != 2:
                raise ClueValidationError(
                    f"IMPLIES compound clue {clue.clue_id!r} requires exactly 2 sub_clues."
                )
            if (
                clue.operator == CompoundOperator.IMPLIES
                and clue.sub_clues[0].clue_type == ClueType.CONNECTED
            ):
                raise ClueValidationError(
                    f"IMPLIES clue {clue.clue_id!r}: CONNECTED cannot appear in negated antecedent."
                )
            for sc in clue.sub_clues:
                cls.validate(sc, board)
            return

        raise ClueValidationError(f"Unsupported ClueType: {ct!r}")
