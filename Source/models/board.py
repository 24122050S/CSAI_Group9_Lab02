"""Board coordinates and public character metadata (Section 2.1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


def col_index_to_letter(col_idx: int) -> str:
    """Convert 0-based column index (0 -> 'A', 1 -> 'B', ...) to uppercase letter."""
    if not (0 <= col_idx < 26):
        raise ValueError(f"Column index out of supported range [0, 25]: {col_idx}")
    return chr(ord("A") + col_idx)


def col_letter_to_index(col_letter: str) -> int:
    """Convert column letter ('A' -> 0, 'B' -> 1, ...) to 0-based index."""
    cleaned = col_letter.strip().upper()
    if len(cleaned) != 1 or not ("A" <= cleaned <= "Z"):
        raise ValueError(f"Invalid column letter: {col_letter!r}")
    return ord(cleaned) - ord("A")


@dataclass(frozen=True, order=True)
class CellCoord:
    """Grid coordinate ordered deterministically in row-major order (Section 2.1 & 2.2).

    Note: `row` (1..N) comes before `col_idx` (0..N-1) so default tuple ordering
    is naturally row-major: A1, B1, C1, ..., A2, B2, C2, ...
    """

    row: int  # 1-based row number from top to bottom (1..N)
    col_idx: int  # 0-based column index from left to right (0..N-1)

    @property
    def col(self) -> str:
        """Column letter ('A', 'B', ...)."""
        return col_index_to_letter(self.col_idx)

    @property
    def row_idx(self) -> int:
        """0-based row index (0..N-1)."""
        return self.row - 1

    @property
    def cell_id(self) -> str:
        """Standard coordinate string such as 'C2' (column C, row 2)."""
        return f"{self.col}{self.row}"

    @classmethod
    def parse(cls, text: str, grid_size: int | None = None) -> CellCoord:
        """Parse a coordinate string like 'C2' and optionally validate against grid_size."""
        cleaned = text.strip().upper()
        if len(cleaned) < 2 or not cleaned[0].isalpha() or not cleaned[1:].isdigit():
            raise ValueError(f"Invalid cell coordinate {text!r}; expected format like 'C2'.")
        col_idx = col_letter_to_index(cleaned[0])
        row = int(cleaned[1:])
        if row < 1:
            raise ValueError(f"Row must be >= 1 in coordinate {text!r}.")
        if grid_size is not None:
            if not (1 <= row <= grid_size) or not (0 <= col_idx < grid_size):
                max_col = col_index_to_letter(grid_size - 1)
                raise ValueError(
                    f"Coordinate {cleaned!r} out of bounds for {grid_size}x{grid_size} grid "
                    f"(valid columns A..{max_col}, rows 1..{grid_size})."
                )
        return cls(row=row, col_idx=col_idx)


@dataclass(frozen=True)
class CharacterInfo:
    """Publicly visible identity of a character on the board (no hidden status/clue)."""

    coord: CellCoord
    name: str
    profession: str = ""

    @property
    def cell_id(self) -> str:
        return self.coord.cell_id

    @property
    def row(self) -> int:
        return self.coord.row

    @property
    def col(self) -> str:
        return self.coord.col

    def to_dict(self) -> dict:
        return {
            "cell_id": self.cell_id,
            "row": self.row,
            "col": self.col,
            "name": self.name,
            "profession": self.profession,
        }


@dataclass(frozen=True)
class BoardMetadata:
    """Immutable public topology and character roster of an N x N Griductive board."""

    grid_size: int
    characters: tuple[CharacterInfo, ...]  # Always stored in row-major order

    def __post_init__(self) -> None:
        if self.grid_size < 2:
            raise ValueError(f"grid_size must be >= 2, got {self.grid_size}")
        expected_count = self.grid_size * self.grid_size
        if len(self.characters) != expected_count:
            raise ValueError(
                f"Expected {expected_count} characters for {self.grid_size}x{self.grid_size} "
                f"board, got {len(self.characters)}."
            )
        # Ensure canonical row-major ordering and distinct coordinates/names
        sorted_chars = tuple(sorted(self.characters, key=lambda ch: ch.coord))
        object.__setattr__(self, "characters", sorted_chars)

        seen_cells: set[str] = set()
        seen_names: set[str] = set()
        for r in range(1, self.grid_size + 1):
            for c_idx in range(self.grid_size):
                idx = (r - 1) * self.grid_size + c_idx
                ch = self.characters[idx]
                expected_coord = CellCoord(row=r, col_idx=c_idx)
                if ch.coord != expected_coord:
                    raise ValueError(
                        f"Missing or duplicate cell at {expected_coord.cell_id}; "
                        f"found {ch.cell_id}."
                    )
                seen_cells.add(ch.cell_id)
                norm_name = ch.name.strip().lower()
                if not norm_name:
                    raise ValueError(f"Empty character name at {ch.cell_id}.")
                if norm_name in seen_names:
                    raise ValueError(f"Duplicate character name: {ch.name!r}.")
                seen_names.add(norm_name)

    @classmethod
    def from_characters(cls, grid_size: int, characters: Iterable[CharacterInfo]) -> BoardMetadata:
        return cls(grid_size=grid_size, characters=tuple(characters))

    @property
    def cell_ids(self) -> tuple[str, ...]:
        """All cell IDs in deterministic row-major order."""
        return tuple(ch.cell_id for ch in self.characters)

    def get_character(self, ref: str) -> CharacterInfo:
        """Resolve either a cell ID ('C2') or a character display name ('Clara')."""
        cleaned = ref.strip()
        upper = cleaned.upper()
        for ch in self.characters:
            if ch.cell_id == upper:
                return ch
        lower = cleaned.lower()
        for ch in self.characters:
            if ch.name.strip().lower() == lower:
                return ch
        raise KeyError(f"Unknown cell coordinate or character reference: {ref!r}")

    def resolve_cell_id(self, ref: str) -> str:
        """Resolve a cell ID or character name to its canonical cell ID (e.g. 'C2')."""
        return self.get_character(ref).cell_id
