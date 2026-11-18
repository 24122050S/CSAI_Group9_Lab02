"""GameEngine owning secret puzzle data and enforcing no-guess verdict validation (Section 4.1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent.deductive_agent import DeductiveLogicAgent
from agent.uniqueness import UniquenessChecker, UniquenessReport
from engine.puzzle_loader import SecretPuzzleData
from logic.regions import RegionResolver
from models.board import BoardMetadata
from models.clue import Clue
from models.enums import AgentTerminalState, EncodingMode, Status, VerdictStatus
from models.state import PublicCellState, PublicGameState


@dataclass(frozen=True)
class VerdictSubmissionResult:
    """Response returned by GameEngine when a player or agent submits a verdict."""

    status_code: VerdictStatus
    cell_id: str
    character_name: str
    submitted_verdict: Status
    accepted_status: Status | None = None
    revealed_clue: Clue | None = None
    message: str = ""

    def to_dict(self, board: BoardMetadata | None = None) -> dict[str, Any]:
        return {
            "status_code": self.status_code.value,
            "cell_id": self.cell_id,
            "character_name": self.character_name,
            "submitted_verdict": self.submitted_verdict.value,
            "accepted_status": self.accepted_status.value if self.accepted_status else None,
            "revealed_clue": (
                self.revealed_clue.to_dict(board) if self.revealed_clue else None
            ),
            "message": self.message,
        }


class GameEngine:
    """Owns the complete puzzle, hidden solution, and unrevealed clues (Section 4.1).

    Architectural separation:
    - Hidden ground truth (`__ground_truth`) and unrevealed clues (`__clues`) are stored
      in private name-mangled attributes.
    - `get_public_state()` emits an immutable `PublicGameState` containing ONLY revealed
      clues and proved verdicts.
    """

    def __init__(
        self,
        puzzle: SecretPuzzleData,
        encoding_mode: EncodingMode = EncodingMode.COMBINATORIAL,
    ) -> None:
        self.__puzzle = puzzle
        self.__ground_truth: dict[str, Status] = dict(puzzle.ground_truth)
        self.__clues: dict[str, Clue] = dict(puzzle.clues)
        self._encoding_mode = encoding_mode
        self._revealed: set[str] = set(puzzle.initial_revealed)
        self._step_number: int = 0

    @property
    def puzzle_id(self) -> str:
        return self.__puzzle.puzzle_id

    @property
    def title(self) -> str:
        return self.__puzzle.title

    @property
    def difficulty(self) -> str:
        return self.__puzzle.difficulty

    @property
    def description(self) -> str:
        return self.__puzzle.description

    @property
    def board(self) -> BoardMetadata:
        return self.__puzzle.board

    def restart(self) -> PublicGameState:
        """Reset the puzzle to its initial opening cards (Section 4.1 Restart control)."""
        self._revealed = set(self.__puzzle.initial_revealed)
        self._step_number = 0
        return self.get_public_state()

    def get_public_state(self) -> PublicGameState:
        """Construct an immutable PublicGameState with zero unrevealed data."""
        public_cells: list[PublicCellState] = []
        for ch in self.__puzzle.board.characters:
            cid = ch.cell_id
            if cid in self._revealed:
                public_cells.append(
                    PublicCellState(
                        character=ch,
                        is_revealed=True,
                        status=self.__ground_truth[cid],
                        clue=self.__clues.get(cid),
                    )
                )
            else:
                public_cells.append(
                    PublicCellState(
                        character=ch,
                        is_revealed=False,
                        status=Status.UNKNOWN,
                        clue=None,
                    )
                )

        return PublicGameState(
            puzzle_id=self.__puzzle.puzzle_id,
            title=self.__puzzle.title,
            board=self.__puzzle.board,
            cells=tuple(public_cells),
            step_number=self._step_number,
        )

    def submit_verdict(
        self,
        cell_ref: str,
        verdict: Status,
    ) -> VerdictSubmissionResult:
        """Validate a proposed CRIMINAL or INNOCENT verdict against public KB_t (Section 2.2 & 4.1)."""
        if verdict not in (Status.CRIMINAL, Status.INNOCENT):
            raise ValueError(f"Submitted verdict must be CRIMINAL or INNOCENT, got {verdict}.")

        ch = self.__puzzle.board.get_character(cell_ref)
        cid = ch.cell_id

        if cid in self._revealed:
            return VerdictSubmissionResult(
                status_code=VerdictStatus.ALREADY_REVEALED,
                cell_id=cid,
                character_name=ch.name,
                submitted_verdict=verdict,
                accepted_status=self.__ground_truth[cid],
                revealed_clue=self.__clues.get(cid),
                message=f"{ch.name} ({cid}) is already revealed.",
            )

        # Entailment check strictly over current public KB_t
        public_state = self.get_public_state()
        verifier = DeductiveLogicAgent(encoding_mode=self._encoding_mode)
        term_state, entailed_status, _, _ = verifier.classify_single_cell(public_state, cid)

        if term_state == AgentTerminalState.INCONSISTENT:
            return VerdictSubmissionResult(
                status_code=VerdictStatus.INCONSISTENT_KB,
                cell_id=cid,
                character_name=ch.name,
                submitted_verdict=verdict,
                message="Current public knowledge base KB_t is logically inconsistent (UNSAT).",
            )

        if entailed_status == Status.UNKNOWN:
            # Neither status is currently forced -> reject WITHOUT revealing hidden clue!
            return VerdictSubmissionResult(
                status_code=VerdictStatus.NOT_PROVABLE,
                cell_id=cid,
                character_name=ch.name,
                submitted_verdict=verdict,
                message=(
                    f"NOT_PROVABLE: Neither CRIMINAL nor INNOCENT is logically forced for "
                    f"{ch.name} ({cid}) from current public clues. No guessing allowed!"
                ),
            )

        if entailed_status != verdict:
            # Opposite status is currently forced -> reject as CONTRADICTED!
            return VerdictSubmissionResult(
                status_code=VerdictStatus.CONTRADICTED,
                cell_id=cid,
                character_name=ch.name,
                submitted_verdict=verdict,
                message=(
                    f"CONTRADICTED: Current public knowledge forces the opposite verdict "
                    f"for {ch.name} ({cid})!"
                ),
            )

        # Verdict is logically forced; also verify consistency with puzzle ground truth
        true_hidden = self.__ground_truth[cid]
        if verdict != true_hidden:
            return VerdictSubmissionResult(
                status_code=VerdictStatus.INCONSISTENT_KB,
                cell_id=cid,
                character_name=ch.name,
                submitted_verdict=verdict,
                message=(
                    f"Puzzle authoring error: entailed verdict {verdict.value} disagrees "
                    f"with hidden ground truth on {cid}."
                ),
            )

        # Accept verdict, mark status, flip card, and reveal clue
        self._revealed.add(cid)
        self._step_number += 1
        new_clue = self.__clues.get(cid)

        return VerdictSubmissionResult(
            status_code=VerdictStatus.ACCEPTED,
            cell_id=cid,
            character_name=ch.name,
            submitted_verdict=verdict,
            accepted_status=true_hidden,
            revealed_clue=new_clue,
            message=(
                f"ACCEPTED: {ch.name} ({cid}) is proved {true_hidden.value}!"
                + (
                    f" New clue revealed: \"{new_clue.render_text(self.board)}\""
                    if new_clue
                    else ""
                )
            ),
        )

    def get_revealed_clue_highlights(self, cell_ref: str) -> dict[str, Any]:
        """Highlight cells referenced/counted by a revealed card's clue (Section 4.1)."""
        ch = self.__puzzle.board.get_character(cell_ref)
        cid = ch.cell_id
        if cid not in self._revealed:
            raise PermissionError(
                f"Cannot highlight clue of unrevealed card {cid}; card is still face-down."
            )
        clue = self.__clues.get(cid)
        if clue is None:
            return {
                "owner_cell": cid,
                "clue_id": None,
                "text": "",
                "primary": [],
                "secondary": [],
            }
        groups = RegionResolver.referenced_cells(clue, self.__puzzle.board)
        return {
            "owner_cell": cid,
            "clue_id": clue.clue_id,
            "text": clue.render_text(self.__puzzle.board),
            "text_vi": clue.render_text_vi(self.__puzzle.board),
            "primary": groups["primary"],
            "secondary": groups["secondary"],
        }

    def check_complete_uniqueness(
        self,
        include_opening_verdicts: bool = True,
        encoding_mode: EncodingMode | None = None,
    ) -> UniquenessReport:
        """Run the separate uniqueness check over the puzzle's complete clue set (Section 4.4)."""
        init_verdicts = (
            {cid: self.__ground_truth[cid] for cid in self.__puzzle.initial_revealed}
            if include_opening_verdicts
            else None
        )
        return UniquenessChecker.check(
            board=self.__puzzle.board,
            all_clues=self.__clues.values(),
            initial_verdicts=init_verdicts,
            encoding_mode=encoding_mode or self._encoding_mode,
        )
