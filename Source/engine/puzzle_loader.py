"""Puzzle JSON definition, loader, and validator (Section 2.1 & 4.1)."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from logic.evaluator import SemanticEvaluator
from logic.validator import ClueValidator
from models.board import BoardMetadata, CellCoord, CharacterInfo
from models.clue import Clue
from models.enums import Status


@dataclass(frozen=True)
class SecretPuzzleData:
    """Complete puzzle specification owned exclusively by GameEngine (Section 4.1)."""

    puzzle_id: str
    title: str
    difficulty: str
    description: str
    board: BoardMetadata
    ground_truth: dict[str, Status]
    clues: dict[str, Clue]
    initial_revealed: tuple[str, ...]
    allow_inconsistent: bool = False

    def to_dict(self) -> dict[str, Any]:
        cards = []
        for ch in self.board.characters:
            cid = ch.cell_id
            clue = self.clues.get(cid)
            cards.append(
                {
                    "cell_id": cid,
                    "name": ch.name,
                    "profession": ch.profession,
                    "status": self.ground_truth[cid].value,
                    "clue": clue.to_dict(self.board) if clue else None,
                }
            )
        return {
            "puzzle_id": self.puzzle_id,
            "title": self.title,
            "difficulty": self.difficulty,
            "grid_size": self.board.grid_size,
            "description": self.description,
            "allow_inconsistent": self.allow_inconsistent,
            "initial_revealed": list(self.initial_revealed),
            "cards": cards,
        }


class PuzzleLoader:
    """Loads and validates structured Griductive puzzles from JSON files or dicts."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> SecretPuzzleData:
        puzzle_id = str(data.get("puzzle_id", "custom_puzzle")).strip()
        title = str(data.get("title", puzzle_id)).strip()
        difficulty = str(data.get("difficulty", "Standard")).strip()
        description = str(data.get("description", "")).strip()
        grid_size = int(data["grid_size"])
        allow_inconsistent = bool(data.get("allow_inconsistent", False))

        raw_cards = data["cards"]
        characters: list[CharacterInfo] = []
        ground_truth: dict[str, Status] = {}
        raw_clues_by_cell: dict[str, dict[str, Any]] = {}

        for entry in raw_cards:
            coord = CellCoord.parse(str(entry["cell_id"]), grid_size=grid_size)
            cid = coord.cell_id
            name = str(entry["name"]).strip()
            prof = str(entry.get("profession", "")).strip()
            st = Status(str(entry["status"]).strip().upper())
            if st not in (Status.CRIMINAL, Status.INNOCENT):
                raise ValueError(
                    f"Puzzle {puzzle_id}: card {cid} must have hidden status "
                    f"CRIMINAL or INNOCENT, got {st}."
                )
            characters.append(CharacterInfo(coord=coord, name=name, profession=prof))
            ground_truth[cid] = st
            if entry.get("clue") is not None:
                raw_clues_by_cell[cid] = entry["clue"]

        board = BoardMetadata.from_characters(grid_size, characters)

        # Verify alphabetical display name ordering (Section 2.1) unless relaxed
        if data.get("enforce_alphabetical_names", True):
            names = [ch.name.lower() for ch in board.characters]
            if names != sorted(names):
                raise ValueError(
                    f"Puzzle {puzzle_id}: characters must be ordered alphabetically "
                    f"by display name in row-major order; got {[ch.name for ch in board.characters]}."
                )

        clues: dict[str, Clue] = {}
        for cid, raw_clue in raw_clues_by_cell.items():
            clue = Clue.from_dict(raw_clue, default_owner=cid)
            ClueValidator.validate(clue, board)
            clues[cid] = clue

        init_rev = tuple(
            board.resolve_cell_id(str(ref)) for ref in data.get("initial_revealed", [])
        )
        if not init_rev:
            raise ValueError(
                f"Puzzle {puzzle_id}: `initial_revealed` must contain at least one card."
            )

        if not allow_inconsistent:
            for cid, clue in clues.items():
                if not SemanticEvaluator.evaluate(clue, ground_truth, board):
                    raise ValueError(
                        f"Puzzle {puzzle_id}: clue {clue.clue_id!r} on {cid} is FALSE "
                        f"under the puzzle's own ground_truth! Every clue in Griductive "
                        "must be true regardless of its owner's status."
                    )

        return SecretPuzzleData(
            puzzle_id=puzzle_id,
            title=title,
            difficulty=difficulty,
            description=description,
            board=board,
            ground_truth=ground_truth,
            clues=clues,
            initial_revealed=init_rev,
            allow_inconsistent=allow_inconsistent,
        )

    @classmethod
    def load_file(cls, path: str | Path) -> SecretPuzzleData:
        p = Path(path)
        with p.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return cls.from_dict(data)

    @staticmethod
    def save_file(puzzle: SecretPuzzleData, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as fh:
            json.dump(puzzle.to_dict(), fh, indent=2, ensure_ascii=False)
