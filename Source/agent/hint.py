"""No-cheat Hint Engine with Minimal Unsatisfiable Subset (MUS) clue extraction (Section 4.1 & 4.4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent.deductive_agent import DeductiveLogicAgent
from logic.cnf_encoder import CNFEncoder
from models.enums import AgentTerminalState, EncodingMode, Status
from models.state import PublicGameState
from solver.dpll import DPLLSolver


@dataclass(frozen=True)
class HintResult:
    """Hint computed strictly from PublicGameState without reading hidden labels."""

    available: bool
    terminal_state: AgentTerminalState
    target_cell: str | None = None
    target_name: str | None = None
    forced_status: Status | None = None
    relevant_clue_ids: tuple[str, ...] = ()
    relevant_clue_cells: tuple[str, ...] = ()
    supporting_verdict_cells: tuple[str, ...] = ()
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "terminal_state": self.terminal_state.value,
            "target_cell": self.target_cell,
            "target_name": self.target_name,
            "forced_status": self.forced_status.value if self.forced_status else None,
            "relevant_clue_ids": list(self.relevant_clue_ids),
            "relevant_clue_cells": list(self.relevant_clue_cells),
            "supporting_verdict_cells": list(self.supporting_verdict_cells),
            "message": self.message,
        }


class HintEngine:
    """Finds the next logically provable character and the minimal revealed clues proving it."""

    @staticmethod
    def get_hint(
        state: PublicGameState,
        encoding_mode: EncodingMode = EncodingMode.COMBINATORIAL,
    ) -> HintResult:
        if state.is_solved:
            return HintResult(
                available=False,
                terminal_state=AgentTerminalState.SOLVED,
                message="The puzzle is already completely solved!",
            )

        agent = DeductiveLogicAgent(
            encoding_mode=encoding_mode,
            use_witness_pruning=True,
        )
        term_state, classifications, _, _ = agent.classify_all_unresolved(state)

        if term_state == AgentTerminalState.INCONSISTENT:
            return HintResult(
                available=False,
                terminal_state=AgentTerminalState.INCONSISTENT,
                message="Current public knowledge base is logically inconsistent (UNSAT).",
            )

        forced_cells = [
            cid
            for cid in state.unresolved_cell_ids()
            if classifications.get(cid) in (Status.CRIMINAL, Status.INNOCENT)
        ]
        if not forced_cells:
            return HintResult(
                available=False,
                terminal_state=AgentTerminalState.STUCK,
                message="No character's status is currently forced by the revealed clues.",
            )

        target_cell = forced_cells[0]
        forced_status = classifications[target_cell]
        target_char = state.board.get_character(target_cell)

        # Deletion-based MUS extraction to pinpoint minimal revealed clues & proved verdicts
        kept_clues = list(state.revealed_clues())
        kept_verdicts = dict(state.proved_verdicts())
        solver = DPLLSolver()

        def _is_still_entailed(clues_subset: list, verdicts_subset: dict[str, Status]) -> bool:
            enc = CNFEncoder(state.board, encoding_mode=encoding_mode)
            kb = enc.build_knowledge_base(clues_subset, verdicts_subset)
            vid = kb.variables.var_for(target_cell)
            opposite_lit = -vid if forced_status == Status.CRIMINAL else vid
            res = solver.solve(
                kb.clauses,
                num_vars=kb.variables.total_vars,
                assumptions=[opposite_lit],
            )
            return not res.is_sat

        # Minimize revealed clues
        for clue in list(kept_clues):
            trial_clues = [c for c in kept_clues if c.clue_id != clue.clue_id]
            if _is_still_entailed(trial_clues, kept_verdicts):
                kept_clues = trial_clues

        # Minimize supporting proved verdicts
        for v_cell in list(kept_verdicts.keys()):
            trial_verdicts = {k: v for k, v in kept_verdicts.items() if k != v_cell}
            if _is_still_entailed(kept_clues, trial_verdicts):
                kept_verdicts = trial_verdicts

        clue_ids = tuple(c.clue_id for c in kept_clues)
        clue_cells = tuple(c.owner_cell for c in kept_clues if c.owner_cell)
        verdict_cells = tuple(kept_verdicts.keys())

        if clue_cells:
            src_desc = ", ".join(
                f"{state.board.get_character(cid).name} ({cid})" for cid in clue_cells
            )
            msg = (
                f"Hint: {target_char.name} ({target_cell}) can be proved next "
                f"using the clue(s) from {src_desc}."
            )
        else:
            msg = f"Hint: {target_char.name} ({target_cell}) can be logically proved next."

        return HintResult(
            available=True,
            terminal_state=AgentTerminalState.IN_PROGRESS,
            target_cell=target_cell,
            target_name=target_char.name,
            forced_status=forced_status,
            relevant_clue_ids=clue_ids,
            relevant_clue_cells=clue_cells,
            supporting_verdict_cells=verdict_cells,
            message=msg,
        )
