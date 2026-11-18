"""Immutable public game state DTO enforcing zero hidden-state leakage (Section 4.1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.board import BoardMetadata, CharacterInfo
from models.clue import Clue
from models.enums import Status


@dataclass(frozen=True)
class PublicCellState:
    """Public view of a single cell on the board.

    Invariant enforced at construction:
    - If `is_revealed` is False, `status` MUST be Status.UNKNOWN and `clue` MUST be None.
    - If `is_revealed` is True, `status` MUST be CRIMINAL or INNOCENT.
    """

    character: CharacterInfo
    is_revealed: bool
    status: Status = Status.UNKNOWN
    clue: Clue | None = None

    def __post_init__(self) -> None:
        if not self.is_revealed:
            if self.status != Status.UNKNOWN or self.clue is not None:
                raise ValueError(
                    f"Security violation on unrevealed cell {self.character.cell_id}: "
                    "unrevealed cells cannot carry status or clue data in PublicCellState."
                )
        else:
            if self.status not in (Status.CRIMINAL, Status.INNOCENT):
                raise ValueError(
                    f"Revealed cell {self.character.cell_id} must have CRIMINAL or INNOCENT "
                    f"status, got {self.status}."
                )

    @property
    def cell_id(self) -> str:
        return self.character.cell_id

    def to_dict(self, board: BoardMetadata | None = None) -> dict[str, Any]:
        return {
            "cell_id": self.character.cell_id,
            "row": self.character.row,
            "col": self.character.col,
            "name": self.character.name,
            "profession": self.character.profession,
            "is_revealed": self.is_revealed,
            "status": self.status.value,
            "clue": self.clue.to_dict(board) if (self.is_revealed and self.clue) else None,
        }


@dataclass(frozen=True)
class PublicGameState:
    """Complete public knowledge state KB_t passed to LogicAgent and GUI (Section 2.2 & 4.1)."""

    puzzle_id: str
    title: str
    board: BoardMetadata
    cells: tuple[PublicCellState, ...]
    step_number: int = 0

    def __post_init__(self) -> None:
        if len(self.cells) != len(self.board.characters):
            raise ValueError("PublicGameState cells count does not match BoardMetadata.")
        sorted_cells = tuple(sorted(self.cells, key=lambda c: c.character.coord))
        object.__setattr__(self, "cells", sorted_cells)

    @property
    def grid_size(self) -> int:
        return self.board.grid_size

    @property
    def is_solved(self) -> bool:
        return all(c.is_revealed for c in self.cells)

    def get_cell(self, ref: str) -> PublicCellState:
        target_id = self.board.resolve_cell_id(ref)
        for cell in self.cells:
            if cell.cell_id == target_id:
                return cell
        raise KeyError(f"Cell not found: {ref!r}")

    def revealed_clues(self) -> tuple[Clue, ...]:
        """Return all currently face-up clues in deterministic row-major order."""
        return tuple(c.clue for c in self.cells if c.is_revealed and c.clue is not None)

    def proved_verdicts(self) -> dict[str, Status]:
        """Return mapping cell_id -> Status (CRIMINAL/INNOCENT) for all revealed cards."""
        return {c.cell_id: c.status for c in self.cells if c.is_revealed}

    def unresolved_cell_ids(self) -> tuple[str, ...]:
        """Return unrevealed cell IDs in deterministic row-major order."""
        return tuple(c.cell_id for c in self.cells if not c.is_revealed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "puzzle_id": self.puzzle_id,
            "title": self.title,
            "grid_size": self.grid_size,
            "step_number": self.step_number,
            "is_solved": self.is_solved,
            "revealed_count": sum(1 for c in self.cells if c.is_revealed),
            "total_cells": len(self.cells),
            "cells": [c.to_dict(self.board) for c in self.cells],
        }
