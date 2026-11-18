"""Deductive Logic Agent built on top of CNFEncoder and DPLLSolver (Section 3.4 & 4.4)."""

from __future__ import annotations

import time
from typing import Protocol

from agent.trace import AgentSolveReport, DeductionStepTrace, SATQueryRecord
from logic.cnf_encoder import CNFEncoder, EncodedKnowledgeBase
from models.clue import Clue
from models.enums import AgentTerminalState, EncodingMode, Status, VerdictStatus
from models.state import PublicGameState
from solver.dpll import BranchingHeuristic, DPLLSolver, SolverTimeoutError
from solver.stats import SolverStats


class VerdictSubmissionProtocol(Protocol):
    """Minimal result object returned by GameEngine.submit_verdict."""

    @property
    def status_code(self) -> VerdictStatus: ...

    @property
    def revealed_clue(self) -> Clue | None: ...


class PublicEngineProtocol(Protocol):
    """Strict public-only interface through which LogicAgent interacts with GameEngine.

    Guarantees at the type and runtime level that LogicAgent can ONLY read PublicGameState
    and submit verdicts—never inspecting hidden statuses or unrevealed clues (Section 4.1).
    """

    def get_public_state(self) -> PublicGameState: ...

    def submit_verdict(self, cell_ref: str, verdict: Status) -> VerdictSubmissionProtocol: ...


class DeductiveLogicAgent:
    """No-guess propositional deduction agent for Griductive (Section 4.4)."""

    def __init__(
        self,
        encoding_mode: EncodingMode = EncodingMode.COMBINATORIAL,
        heuristic: BranchingHeuristic = BranchingHeuristic.FIXED_ORDER,
        use_pure_literal: bool = False,
        use_witness_pruning: bool = False,
        timeout_sec: float | None = None,
    ) -> None:
        self.encoding_mode = encoding_mode
        self.heuristic = heuristic
        self.use_pure_literal = use_pure_literal
        self.use_witness_pruning = use_witness_pruning
        self.timeout_sec = timeout_sec

    def _make_solver(self, remaining_timeout: float | None = None) -> DPLLSolver:
        eff_timeout = remaining_timeout if remaining_timeout is not None else self.timeout_sec
        return DPLLSolver(
            heuristic=self.heuristic,
            use_pure_literal=self.use_pure_literal,
            timeout_sec=eff_timeout,
        )

    def classify_single_cell(
        self,
        state: PublicGameState,
        cell_ref: str,
    ) -> tuple[AgentTerminalState, Status, list[SATQueryRecord], EncodedKnowledgeBase]:
        """Classify a single unresolved character as CRIMINAL, INNOCENT, UNKNOWN, or INCONSISTENT.

        Follows Section 3.4 directly:
        - KB_t |= C_i   <=> KB_t ^ ~C_i is UNSAT
        - KB_t |= ~C_i  <=> KB_t ^ C_i  is UNSAT
        - Both UNSAT    <=> KB_t itself is INCONSISTENT
        - Both SAT      <=> UNKNOWN
        """
        encoder = CNFEncoder(state.board, encoding_mode=self.encoding_mode)
        kb = encoder.build_from_public_state(state)
        solver = self._make_solver()

        cell_id = state.board.resolve_cell_id(cell_ref)
        vid = kb.variables.var_for(cell_id)
        queries: list[SATQueryRecord] = []

        # Query 1: KB_t ^ ~C_i (refutation test for CRIMINAL)
        res_not_c = solver.solve(kb.clauses, num_vars=kb.variables.total_vars, assumptions=[-vid])
        queries.append(
            SATQueryRecord(
                query_label=f"KB_t ∧ ¬C_{cell_id}",
                cell_id=cell_id,
                assumed_literal=f"¬C_{cell_id}",
                is_sat=res_not_c.is_sat,
                stats=res_not_c.stats,
            )
        )

        # Query 2: KB_t ^ C_i (refutation test for INNOCENT)
        res_c = solver.solve(kb.clauses, num_vars=kb.variables.total_vars, assumptions=[vid])
        queries.append(
            SATQueryRecord(
                query_label=f"KB_t ∧ C_{cell_id}",
                cell_id=cell_id,
                assumed_literal=f"C_{cell_id}",
                is_sat=res_c.is_sat,
                stats=res_c.stats,
            )
        )

        if not res_not_c.is_sat and not res_c.is_sat:
            return AgentTerminalState.INCONSISTENT, Status.UNKNOWN, queries, kb
        if not res_not_c.is_sat:
            return AgentTerminalState.IN_PROGRESS, Status.CRIMINAL, queries, kb
        if not res_c.is_sat:
            return AgentTerminalState.IN_PROGRESS, Status.INNOCENT, queries, kb
        return AgentTerminalState.IN_PROGRESS, Status.UNKNOWN, queries, kb

    def classify_all_unresolved(
        self,
        state: PublicGameState,
        remaining_timeout: float | None = None,
    ) -> tuple[AgentTerminalState, dict[str, Status], list[SATQueryRecord], EncodedKnowledgeBase]:
        """Classify every unresolved cell in deterministic row-major order."""
        encoder = CNFEncoder(state.board, encoding_mode=self.encoding_mode)
        kb = encoder.build_from_public_state(state)
        solver = self._make_solver(remaining_timeout)

        queries: list[SATQueryRecord] = []
        classifications: dict[str, Status] = {}

        # Step 0: Check base consistency of KB_t
        base_res = solver.solve(kb.clauses, num_vars=kb.variables.total_vars)
        queries.append(
            SATQueryRecord(
                query_label="KB_t consistency",
                cell_id=None,
                assumed_literal=None,
                is_sat=base_res.is_sat,
                stats=base_res.stats,
            )
        )
        if not base_res.is_sat or base_res.assignment is None:
            return AgentTerminalState.INCONSISTENT, classifications, queries, kb

        unresolved = state.unresolved_cell_ids()
        if not unresolved:
            return AgentTerminalState.SOLVED, classifications, queries, kb

        if self.use_witness_pruning:
            # Witness-guided pruning: accumulate models seen so far to skip redundant SAT calls
            seen_true: set[str] = set()
            seen_false: set[str] = set()

            def _record_witness(model: dict[int, bool]) -> None:
                for cid in unresolved:
                    v = kb.variables.var_for(cid)
                    if model[v]:
                        seen_true.add(cid)
                    else:
                        seen_false.add(cid)

            _record_witness(base_res.assignment)

            for cid in unresolved:
                if cid in seen_true and cid in seen_false:
                    classifications[cid] = Status.UNKNOWN
                    continue

                vid = kb.variables.var_for(cid)
                if cid in seen_true:
                    # C_cid=True is already satisfiable; test if ~C_cid is UNSAT
                    res = solver.solve(
                        kb.clauses, num_vars=kb.variables.total_vars, assumptions=[-vid]
                    )
                    queries.append(
                        SATQueryRecord(
                            query_label=f"KB_t ∧ ¬C_{cid}",
                            cell_id=cid,
                            assumed_literal=f"¬C_{cid}",
                            is_sat=res.is_sat,
                            stats=res.stats,
                        )
                    )
                    if not res.is_sat:
                        classifications[cid] = Status.CRIMINAL
                    else:
                        classifications[cid] = Status.UNKNOWN
                        if res.assignment is not None:
                            _record_witness(res.assignment)
                else:
                    # C_cid=False is already satisfiable; test if C_cid is UNSAT
                    res = solver.solve(
                        kb.clauses, num_vars=kb.variables.total_vars, assumptions=[vid]
                    )
                    queries.append(
                        SATQueryRecord(
                            query_label=f"KB_t ∧ C_{cid}",
                            cell_id=cid,
                            assumed_literal=f"C_{cid}",
                            is_sat=res.is_sat,
                            stats=res.stats,
                        )
                    )
                    if not res.is_sat:
                        classifications[cid] = Status.INNOCENT
                    else:
                        classifications[cid] = Status.UNKNOWN
                        if res.assignment is not None:
                            _record_witness(res.assignment)
        else:
            # Standard explicit refutation mode: test ~C_i and C_i explicitly for each cell
            for cid in unresolved:
                vid = kb.variables.var_for(cid)
                res_neg = solver.solve(
                    kb.clauses, num_vars=kb.variables.total_vars, assumptions=[-vid]
                )
                queries.append(
                    SATQueryRecord(
                        query_label=f"KB_t ∧ ¬C_{cid}",
                        cell_id=cid,
                        assumed_literal=f"¬C_{cid}",
                        is_sat=res_neg.is_sat,
                        stats=res_neg.stats,
                    )
                )
                if not res_neg.is_sat:
                    classifications[cid] = Status.CRIMINAL
                    continue

                res_pos = solver.solve(
                    kb.clauses, num_vars=kb.variables.total_vars, assumptions=[vid]
                )
                queries.append(
                    SATQueryRecord(
                        query_label=f"KB_t ∧ C_{cid}",
                        cell_id=cid,
                        assumed_literal=f"C_{cid}",
                        is_sat=res_pos.is_sat,
                        stats=res_pos.stats,
                    )
                )
                if not res_pos.is_sat:
                    classifications[cid] = Status.INNOCENT
                else:
                    classifications[cid] = Status.UNKNOWN

        forced = [
            cid
            for cid in unresolved
            if classifications[cid] in (Status.CRIMINAL, Status.INNOCENT)
        ]
        if not forced:
            return AgentTerminalState.STUCK, classifications, queries, kb
        return AgentTerminalState.IN_PROGRESS, classifications, queries, kb

    def step(
        self,
        engine: PublicEngineProtocol,
        step_index: int | None = None,
        remaining_timeout: float | None = None,
    ) -> DeductionStepTrace:
        """Execute one deterministic no-guess deduction step against `engine`."""
        state = engine.get_public_state()
        step_num = step_index if step_index is not None else (state.step_number + 1)

        term_state, classifications, queries, kb = self.classify_all_unresolved(
            state, remaining_timeout=remaining_timeout
        )

        step_stats = SolverStats()
        for q in queries:
            step_stats.merge(q.stats)

        if term_state in (
            AgentTerminalState.INCONSISTENT,
            AgentTerminalState.STUCK,
            AgentTerminalState.SOLVED,
        ):
            return DeductionStepTrace(
                step_number=step_num,
                active_clue_ids=kb.active_clue_ids,
                num_primary_vars=kb.num_primary_vars,
                num_aux_vars=kb.num_aux_vars,
                num_clauses=kb.num_clauses,
                sat_queries=tuple(queries),
                classifications=classifications,
                forced_count_in_step=0,
                chosen_cell=None,
                chosen_character=None,
                verdict=None,
                newly_revealed_clue_id=None,
                newly_revealed_clue_text=None,
                step_stats=step_stats,
                terminal_state=term_state,
            )

        # Deterministic selection: first forced character in row-major order (Section 2.2)
        forced_cells = [
            cid
            for cid in state.unresolved_cell_ids()
            if classifications.get(cid) in (Status.CRIMINAL, Status.INNOCENT)
        ]
        chosen_cell = forced_cells[0]
        chosen_verdict = classifications[chosen_cell]
        chosen_char = state.board.get_character(chosen_cell).name

        outcome = engine.submit_verdict(chosen_cell, chosen_verdict)
        if outcome.status_code != VerdictStatus.ACCEPTED:
            # Should only happen if puzzle's hidden ground truth contradicts a revealed clue
            return DeductionStepTrace(
                step_number=step_num,
                active_clue_ids=kb.active_clue_ids,
                num_primary_vars=kb.num_primary_vars,
                num_aux_vars=kb.num_aux_vars,
                num_clauses=kb.num_clauses,
                sat_queries=tuple(queries),
                classifications=classifications,
                forced_count_in_step=len(forced_cells),
                chosen_cell=chosen_cell,
                chosen_character=chosen_char,
                verdict=chosen_verdict,
                newly_revealed_clue_id=None,
                newly_revealed_clue_text=None,
                step_stats=step_stats,
                terminal_state=AgentTerminalState.INCONSISTENT,
            )

        new_state = engine.get_public_state()
        next_term = (
            AgentTerminalState.SOLVED
            if new_state.is_solved
            else AgentTerminalState.IN_PROGRESS
        )
        new_clue = outcome.revealed_clue

        return DeductionStepTrace(
            step_number=step_num,
            active_clue_ids=kb.active_clue_ids,
            num_primary_vars=kb.num_primary_vars,
            num_aux_vars=kb.num_aux_vars,
            num_clauses=kb.num_clauses,
            sat_queries=tuple(queries),
            classifications=classifications,
            forced_count_in_step=len(forced_cells),
            chosen_cell=chosen_cell,
            chosen_character=chosen_char,
            verdict=chosen_verdict,
            newly_revealed_clue_id=new_clue.clue_id if new_clue else None,
            newly_revealed_clue_text=new_clue.render_text(state.board) if new_clue else None,
            step_stats=step_stats,
            terminal_state=next_term,
        )

    def solve(self, engine: PublicEngineProtocol) -> AgentSolveReport:
        """Run the full deduction loop until SOLVED, STUCK, INCONSISTENT, or timeout."""
        wall_start = time.perf_counter()
        init_state = engine.get_public_state()
        steps: list[DeductionStepTrace] = []
        total_stats = SolverStats()
        total_sat_calls = 0

        peak_primary = init_state.grid_size * init_state.grid_size
        peak_aux = 0
        peak_clauses = 0

        reveal_waves = 0
        current_wave_frontier: set[str] = set()

        if init_state.is_solved:
            enc = CNFEncoder(init_state.board, encoding_mode=self.encoding_mode)
            kb = enc.build_from_public_state(init_state)
            return AgentSolveReport(
                puzzle_id=init_state.puzzle_id,
                terminal_state=AgentTerminalState.SOLVED,
                steps=(),
                deduction_steps=0,
                reveal_waves=0,
                total_sat_calls=0,
                peak_primary_vars=kb.num_primary_vars,
                peak_aux_vars=kb.num_aux_vars,
                peak_clauses=kb.num_clauses,
                final_primary_vars=kb.num_primary_vars,
                final_aux_vars=kb.num_aux_vars,
                final_clauses=kb.num_clauses,
                total_stats=total_stats,
                wall_runtime_sec=time.perf_counter() - wall_start,
            )

        step_idx = 1
        timed_out = False
        err_msg = ""
        final_term = AgentTerminalState.IN_PROGRESS

        while True:
            rem_timeout: float | None = None
            if self.timeout_sec is not None:
                elapsed = time.perf_counter() - wall_start
                rem_timeout = self.timeout_sec - elapsed
                if rem_timeout <= 0:
                    timed_out = True
                    err_msg = f"Agent exceeded timeout of {self.timeout_sec:.2f}s."
                    final_term = AgentTerminalState.STUCK
                    break

            try:
                trace = self.step(
                    engine, step_index=step_idx, remaining_timeout=rem_timeout
                )
            except SolverTimeoutError as exc:
                timed_out = True
                err_msg = str(exc)
                final_term = AgentTerminalState.STUCK
                break

            steps.append(trace)
            total_stats.merge(trace.step_stats)
            total_sat_calls += len(trace.sat_queries)
            peak_primary = max(peak_primary, trace.num_primary_vars)
            peak_aux = max(peak_aux, trace.num_aux_vars)
            peak_clauses = max(peak_clauses, trace.num_clauses)

            if trace.chosen_cell is not None:
                # Track parallel reveal waves accurately
                if trace.chosen_cell not in current_wave_frontier:
                    reveal_waves += 1
                    current_wave_frontier = {
                        cid
                        for cid, st in trace.classifications.items()
                        if st in (Status.CRIMINAL, Status.INNOCENT)
                    }
                current_wave_frontier.discard(trace.chosen_cell)

            final_term = trace.terminal_state
            if final_term in (
                AgentTerminalState.SOLVED,
                AgentTerminalState.STUCK,
                AgentTerminalState.INCONSISTENT,
            ):
                break
            step_idx += 1

        end_state = engine.get_public_state()
        final_enc = CNFEncoder(end_state.board, encoding_mode=self.encoding_mode)
        final_kb = final_enc.build_from_public_state(end_state)
        peak_aux = max(peak_aux, final_kb.num_aux_vars)
        peak_clauses = max(peak_clauses, final_kb.num_clauses)

        deduction_steps = sum(1 for s in steps if s.chosen_cell is not None)

        return AgentSolveReport(
            puzzle_id=init_state.puzzle_id,
            terminal_state=final_term,
            steps=tuple(steps),
            deduction_steps=deduction_steps,
            reveal_waves=reveal_waves,
            total_sat_calls=total_sat_calls,
            peak_primary_vars=peak_primary,
            peak_aux_vars=peak_aux,
            peak_clauses=peak_clauses,
            final_primary_vars=final_kb.num_primary_vars,
            final_aux_vars=final_kb.num_aux_vars,
            final_clauses=final_kb.num_clauses,
            total_stats=total_stats,
            wall_runtime_sec=time.perf_counter() - wall_start,
            timed_out=timed_out,
            error_message=err_msg,
        )
