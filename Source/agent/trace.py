"""Structured deduction trace models for the Deductive Logic Agent (Section 4.4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.enums import AgentTerminalState, Status
from solver.stats import SolverStats


@dataclass(frozen=True)
class SATQueryRecord:
    """Single SAT query executed during entailment checking at deduction step t."""

    query_label: str
    cell_id: str | None
    assumed_literal: str | None
    is_sat: bool
    stats: SolverStats

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_label": self.query_label,
            "cell_id": self.cell_id,
            "assumed_literal": self.assumed_literal,
            "result": "SAT" if self.is_sat else "UNSAT",
            "stats": self.stats.to_dict(),
        }


@dataclass(frozen=True)
class DeductionStepTrace:
    """Complete audit record for deduction step t (Section 4.4).

    Contains:
    - step_number
    - active_clue_ids
    - variable & clause counts of KB_t
    - sat_queries executed
    - verdict (cell_id, character_name, CRIMINAL/INNOCENT)
    - newly_revealed_clue (id and rendered text)
    """

    step_number: int
    active_clue_ids: tuple[str, ...]
    num_primary_vars: int
    num_aux_vars: int
    num_clauses: int
    sat_queries: tuple[SATQueryRecord, ...]
    classifications: dict[str, Status]
    forced_count_in_step: int
    chosen_cell: str | None
    chosen_character: str | None
    verdict: Status | None
    newly_revealed_clue_id: str | None
    newly_revealed_clue_text: str | None
    step_stats: SolverStats
    terminal_state: AgentTerminalState

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_number": self.step_number,
            "active_clue_ids": list(self.active_clue_ids),
            "num_primary_vars": self.num_primary_vars,
            "num_aux_vars": self.num_aux_vars,
            "num_clauses": self.num_clauses,
            "sat_queries_count": len(self.sat_queries),
            "sat_queries": [q.to_dict() for q in self.sat_queries],
            "classifications": {k: v.value for k, v in self.classifications.items()},
            "forced_count_in_step": self.forced_count_in_step,
            "chosen_cell": self.chosen_cell,
            "chosen_character": self.chosen_character,
            "verdict": self.verdict.value if self.verdict else None,
            "newly_revealed_clue_id": self.newly_revealed_clue_id,
            "newly_revealed_clue_text": self.newly_revealed_clue_text,
            "step_stats": self.step_stats.to_dict(),
            "terminal_state": self.terminal_state.value,
        }


@dataclass(frozen=True)
class AgentSolveReport:
    """Aggregate report returned after running the DeductiveLogicAgent to termination."""

    puzzle_id: str
    terminal_state: AgentTerminalState
    steps: tuple[DeductionStepTrace, ...]
    deduction_steps: int
    reveal_waves: int
    total_sat_calls: int
    peak_primary_vars: int
    peak_aux_vars: int
    peak_clauses: int
    final_primary_vars: int
    final_aux_vars: int
    final_clauses: int
    total_stats: SolverStats
    wall_runtime_sec: float
    timed_out: bool = False
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "puzzle_id": self.puzzle_id,
            "terminal_state": self.terminal_state.value,
            "deduction_steps": self.deduction_steps,
            "reveal_waves": self.reveal_waves,
            "total_sat_calls": self.total_sat_calls,
            "peak_primary_vars": self.peak_primary_vars,
            "peak_aux_vars": self.peak_aux_vars,
            "peak_clauses": self.peak_clauses,
            "final_primary_vars": self.final_primary_vars,
            "final_aux_vars": self.final_aux_vars,
            "final_clauses": self.final_clauses,
            "total_stats": self.total_stats.to_dict(),
            "wall_runtime_sec": round(self.wall_runtime_sec, 6),
            "wall_runtime_ms": round(self.wall_runtime_sec * 1000.0, 3),
            "timed_out": self.timed_out,
            "error_message": self.error_message,
            "steps": [s.to_dict() for s in self.steps],
        }
