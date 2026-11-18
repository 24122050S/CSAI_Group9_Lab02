"""Deterministic propositional variable mapping and auxiliary variable registry (Section 3.1 & 4.2)."""

from __future__ import annotations

from models.board import BoardMetadata
from models.enums import Status


class VariableManager:
    """Bijective deterministic mapping between board characters and primary Boolean variables.

    Convention (Section 3.1):
    - Primary variables C_i occupy integer IDs 1 .. N^2 in canonical row-major order.
      C_i = True  <=> character i is CRIMINAL
      C_i = False <=> character i is INNOCENT
    - Auxiliary variables introduced by cardinality or extension encodings occupy IDs
      strictly > N^2 and are tracked in a separate registry.
    """

    def __init__(self, board: BoardMetadata) -> None:
        self._board = board
        self._cell_to_var: dict[str, int] = {}
        self._var_to_cell: dict[int, str] = {}

        for idx, ch in enumerate(board.characters, start=1):
            self._cell_to_var[ch.cell_id] = idx
            self._var_to_cell[idx] = ch.cell_id

        self._num_primary = len(board.characters)
        self._aux_labels: dict[int, str] = {}
        self._next_var_id = self._num_primary + 1

    @property
    def board(self) -> BoardMetadata:
        return self._board

    @property
    def num_primary_vars(self) -> int:
        return self._num_primary

    @property
    def num_aux_vars(self) -> int:
        return len(self._aux_labels)

    @property
    def total_vars(self) -> int:
        return self._num_primary + len(self._aux_labels)

    @property
    def primary_var_ids(self) -> tuple[int, ...]:
        return tuple(range(1, self._num_primary + 1))

    def is_primary(self, var_id: int) -> bool:
        return 1 <= var_id <= self._num_primary

    def is_auxiliary(self, var_id: int) -> bool:
        return var_id in self._aux_labels

    def var_for(self, ref: str) -> int:
        """Return primary variable ID (1..N^2) for a cell coordinate ('C2') or character name."""
        cell_id = self._board.resolve_cell_id(ref)
        return self._cell_to_var[cell_id]

    def cell_for(self, var_id: int) -> str:
        """Return canonical cell ID ('C2') for a primary variable ID."""
        if not self.is_primary(var_id):
            raise KeyError(f"Variable {var_id} is not a primary character variable.")
        return self._var_to_cell[var_id]

    def literal_for_status(self, ref: str, status: Status) -> int:
        """Return +C_i for CRIMINAL or -C_i for INNOCENT."""
        v = self.var_for(ref)
        if status == Status.CRIMINAL:
            return v
        if status == Status.INNOCENT:
            return -v
        raise ValueError(f"Cannot create unit literal for non-definite status: {status}")

    def new_aux_var(self, label: str = "aux") -> int:
        """Allocate a fresh auxiliary variable strictly separate from primary variables C_i."""
        vid = self._next_var_id
        self._next_var_id += 1
        self._aux_labels[vid] = f"{label}_{vid}"
        return vid

    def reset_auxiliary_vars(self) -> None:
        """Clear allocated auxiliary variables (keeping primary variable map intact)."""
        self._aux_labels.clear()
        self._next_var_id = self._num_primary + 1

    def format_literal(self, lit: int) -> str:
        """Human-readable representation of a literal (e.g. 'C_A1' or '¬C_A1')."""
        if lit == 0:
            raise ValueError("0 is not a valid DIMACS literal.")
        vid = abs(lit)
        prefix = "" if lit > 0 else "¬"
        if self.is_primary(vid):
            cell_id = self._var_to_cell[vid]
            return f"{prefix}C_{cell_id}"
        aux_name = self._aux_labels.get(vid, f"aux_{vid}")
        return f"{prefix}{aux_name}"

    def extract_primary_statuses(self, model: dict[int, bool]) -> dict[str, Status]:
        """Convert a SAT assignment dict {var_id: bool} into {cell_id: CRIMINAL|INNOCENT}."""
        result: dict[str, Status] = {}
        for vid in range(1, self._num_primary + 1):
            if vid not in model:
                raise KeyError(f"Primary variable {vid} missing from solver assignment.")
            cell_id = self._var_to_cell[vid]
            result[cell_id] = Status.CRIMINAL if model[vid] else Status.INNOCENT
        return result
