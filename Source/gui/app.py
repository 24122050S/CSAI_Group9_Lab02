"""Flask web application bridging the browser GUI with GameEngine and DeductiveLogicAgent."""

from __future__ import annotations

import socket
import threading
import webbrowser
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

from agent.deductive_agent import DeductiveLogicAgent
from agent.hint import HintEngine
from agent.trace import DeductionStepTrace
from engine.game_engine import GameEngine
from engine.puzzle_loader import PuzzleLoader, SecretPuzzleData
from logic.cnf_encoder import CNFEncoder
from models.enums import AgentTerminalState, EncodingMode, Status, VerdictStatus
from solver.dpll import BranchingHeuristic
from solver.stats import SolverStats


class GUISessionState:
    """Server-side game & telemetry state maintaining strict Engine/Agent separation."""

    def __init__(self, puzzles_dir: Path) -> None:
        self.puzzles_dir = puzzles_dir
        self.encoding_mode = EncodingMode.COMBINATORIAL
        self.heuristic = BranchingHeuristic.FIXED_ORDER
        self.use_pure_literal = False
        self.use_witness_pruning = False

        self.catalog: dict[str, Path] = {}
        self.refresh_catalog()

        default_pid = (
            "3x3_01_core_intro"
            if "3x3_01_core_intro" in self.catalog
            else next(iter(self.catalog))
        )
        self.engine: GameEngine = self._load_engine_by_id(default_pid)
        self.traces: list[DeductionStepTrace] = []
        self.cumulative_stats = SolverStats()
        self.total_sat_calls = 0

    def refresh_catalog(self) -> None:
        self.catalog.clear()
        if not self.puzzles_dir.exists():
            return
        for path in sorted(self.puzzles_dir.rglob("*.json")):
            try:
                p = PuzzleLoader.load_file(path)
                self.catalog[p.puzzle_id] = path
            except Exception:
                continue

    def _load_engine_by_id(self, puzzle_id: str) -> GameEngine:
        if puzzle_id not in self.catalog:
            self.refresh_catalog()
        path = self.catalog[puzzle_id]
        puzzle = PuzzleLoader.load_file(path)
        return GameEngine(puzzle, encoding_mode=self.encoding_mode)

    def load_puzzle_id(self, puzzle_id: str) -> None:
        self.engine = self._load_engine_by_id(puzzle_id)
        self.reset_telemetry()

    def load_custom_puzzle(self, raw_data: dict[str, Any]) -> SecretPuzzleData:
        puzzle = PuzzleLoader.from_dict(raw_data)
        self.engine = GameEngine(puzzle, encoding_mode=self.encoding_mode)
        self.reset_telemetry()
        return puzzle

    def restart(self) -> None:
        self.engine.restart()
        self.reset_telemetry()

    def reset_telemetry(self) -> None:
        self.traces.clear()
        self.cumulative_stats = SolverStats()
        self.total_sat_calls = 0

    def make_agent(self) -> DeductiveLogicAgent:
        return DeductiveLogicAgent(
            encoding_mode=self.encoding_mode,
            heuristic=self.heuristic,
            use_pure_literal=self.use_pure_literal,
            use_witness_pruning=self.use_witness_pruning,
            timeout_sec=30.0,
        )

    def build_cnf_inspection(self) -> dict[str, Any]:
        """Build detailed symbolic & DIMACS view of current public KB_t (zero hidden data)."""
        pub_state = self.engine.get_public_state()
        enc = CNFEncoder(pub_state.board, encoding_mode=self.encoding_mode)
        vm = enc.variables

        def fmt_clause(cl: tuple[int, ...]) -> str:
            if not cl:
                return "⊥ (empty clause)"
            return "(" + " ∨ ".join(vm.format_literal(lit) for lit in cl) + ")"

        clue_groups: list[dict[str, Any]] = []
        all_clauses: list[tuple[int, ...]] = []

        for clue in pub_state.revealed_clues():
            c_clauses = enc.encode_clue(clue)
            all_clauses.extend(c_clauses)
            owner_name = pub_state.board.get_character(clue.owner_cell).name if clue.owner_cell else ""
            clue_groups.append(
                {
                    "clue_id": clue.clue_id,
                    "owner_cell": clue.owner_cell,
                    "owner_name": owner_name,
                    "clue_type": clue.clue_type.value,
                    "text": clue.render_text(pub_state.board),
                    "text_vi": clue.render_text_vi(pub_state.board),
                    "clause_count": len(c_clauses),
                    "symbolic_clauses": [fmt_clause(cl) for cl in c_clauses],
                    "dimacs_clauses": [" ".join(str(x) for x in cl) + " 0" for cl in c_clauses],
                }
            )

        verdict_clauses: list[dict[str, Any]] = []
        proved = pub_state.proved_verdicts()
        for cid in pub_state.board.cell_ids:
            if cid in proved:
                ucl = enc.encode_verdict_unit_clause(cid, proved[cid])
                all_clauses.append(ucl)
                ch = pub_state.board.get_character(cid)
                verdict_clauses.append(
                    {
                        "cell_id": cid,
                        "name": ch.name,
                        "status": proved[cid].value,
                        "symbolic": fmt_clause(ucl),
                        "dimacs": f"{ucl[0]} 0",
                    }
                )

        primary_map = [
            {
                "var_id": vm.var_for(ch.cell_id),
                "symbol": f"C_{ch.cell_id}",
                "cell_id": ch.cell_id,
                "name": ch.name,
                "profession": ch.profession,
            }
            for ch in pub_state.board.characters
        ]
        aux_map = [
            {"var_id": vid, "symbol": vm.format_literal(vid)}
            for vid in range(vm.num_primary_vars + 1, vm.total_vars + 1)
        ]

        dimacs_lines = [
            f"c Griductive Solver Public Knowledge Base KB_t (Step {pub_state.step_number})",
            f"c Puzzle: {pub_state.puzzle_id} | Encoding: {self.encoding_mode.value}",
            f"c Primary vars: 1..{vm.num_primary_vars} | Auxiliary vars: {vm.num_aux_vars}",
            f"p cnf {vm.total_vars} {len(all_clauses)}",
        ]
        for cl in all_clauses:
            dimacs_lines.append(" ".join(str(x) for x in cl) + " 0")

        return {
            "puzzle_id": pub_state.puzzle_id,
            "step_number": pub_state.step_number,
            "encoding_mode": self.encoding_mode.value,
            "num_primary_vars": vm.num_primary_vars,
            "num_aux_vars": vm.num_aux_vars,
            "total_vars": vm.total_vars,
            "num_clauses": len(all_clauses),
            "primary_variables": primary_map,
            "auxiliary_variables": aux_map,
            "clue_groups": clue_groups,
            "verdict_unit_clauses": verdict_clauses,
            "dimacs_text": "\n".join(dimacs_lines) + "\n",
        }

    def build_payload(self) -> dict[str, Any]:
        pub_state = self.engine.get_public_state()
        enc = CNFEncoder(pub_state.board, encoding_mode=self.encoding_mode)
        kb = enc.build_from_public_state(pub_state)
        return {
            "state": pub_state.to_dict(),
            "difficulty": self.engine.difficulty,
            "description": self.engine.description,
            "kb_metrics": {
                "encoding_mode": self.encoding_mode.value,
                "num_primary_vars": kb.num_primary_vars,
                "num_aux_vars": kb.num_aux_vars,
                "num_clauses": kb.num_clauses,
                "active_clues": len(kb.active_clue_ids),
                "proved_verdicts": len(kb.proved_verdict_cells),
            },
            "solver_settings": {
                "encoding_mode": self.encoding_mode.value,
                "heuristic": self.heuristic.value,
                "use_pure_literal": self.use_pure_literal,
                "use_witness_pruning": self.use_witness_pruning,
            },
            "telemetry": {
                "total_sat_calls": self.total_sat_calls,
                "stats": self.cumulative_stats.to_dict(),
                "traces": [t.to_dict() for t in self.traces],
            },
        }


def create_app(puzzles_dir: Path | None = None) -> Flask:
    base_dir = Path(__file__).resolve().parent
    resolved_puzzles = puzzles_dir or (base_dir.parent / "puzzles")

    app = Flask(
        __name__,
        template_folder=str(base_dir / "templates"),
        static_folder=str(base_dir / "static"),
    )
    session = GUISessionState(resolved_puzzles)

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/api/puzzles")
    def list_puzzles():
        session.refresh_catalog()
        items = []
        for pid, path in session.catalog.items():
            p = PuzzleLoader.load_file(path)
            items.append(
                {
                    "puzzle_id": pid,
                    "title": p.title,
                    "grid_size": p.board.grid_size,
                    "difficulty": p.difficulty,
                    "description": p.description,
                }
            )
        return jsonify({"puzzles": items, "current_puzzle_id": session.engine.puzzle_id})

    @app.get("/api/state")
    def get_state():
        return jsonify(session.build_payload())

    @app.get("/api/cnf")
    def inspect_cnf():
        return jsonify({"ok": True, "cnf": session.build_cnf_inspection()})

    @app.post("/api/load")
    def load_puzzle():
        body = request.get_json(force=True) or {}
        try:
            if "puzzle_json" in body and body["puzzle_json"] is not None:
                session.load_custom_puzzle(body["puzzle_json"])
            else:
                pid = str(body.get("puzzle_id", "")).strip()
                session.load_puzzle_id(pid)
            return jsonify({"ok": True, **session.build_payload()})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.post("/api/restart")
    def restart_puzzle():
        session.restart()
        return jsonify({"ok": True, **session.build_payload()})

    @app.post("/api/settings")
    def update_settings():
        body = request.get_json(force=True) or {}
        try:
            if "encoding_mode" in body:
                session.encoding_mode = EncodingMode(str(body["encoding_mode"]).upper())
                session.engine._encoding_mode = session.encoding_mode
            if "heuristic" in body:
                session.heuristic = BranchingHeuristic(str(body["heuristic"]).upper())
            if "use_pure_literal" in body:
                session.use_pure_literal = bool(body["use_pure_literal"])
            if "use_witness_pruning" in body:
                session.use_witness_pruning = bool(body["use_witness_pruning"])
            return jsonify({"ok": True, **session.build_payload()})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.post("/api/verdict")
    def submit_verdict():
        body = request.get_json(force=True) or {}
        try:
            cell_id = str(body["cell_id"]).strip()
            verdict = Status(str(body["verdict"]).strip().upper())

            # Pre-capture public entailment proof on KB_t so manual moves also log into Trace!
            pre_state = session.engine.get_public_state()
            resolved_cid = pre_state.board.resolve_cell_id(cell_id)
            already_open = pre_state.get_cell(resolved_cid).is_revealed

            agent = session.make_agent()
            _, entailed_st, sat_queries, kb_pre = agent.classify_single_cell(
                pre_state, resolved_cid
            )

            res = session.engine.submit_verdict(resolved_cid, verdict)

            if not already_open:
                step_stats = SolverStats()
                for q in sat_queries:
                    step_stats.merge(q.stats)
                session.cumulative_stats.merge(step_stats)
                session.total_sat_calls += len(sat_queries)

                if res.status_code == VerdictStatus.ACCEPTED:
                    post_state = session.engine.get_public_state()
                    new_clue = res.revealed_clue
                    manual_trace = DeductionStepTrace(
                        step_number=len(session.traces) + 1,
                        active_clue_ids=kb_pre.active_clue_ids,
                        num_primary_vars=kb_pre.num_primary_vars,
                        num_aux_vars=kb_pre.num_aux_vars,
                        num_clauses=kb_pre.num_clauses,
                        sat_queries=tuple(sat_queries),
                        classifications={resolved_cid: entailed_st},
                        forced_count_in_step=1,
                        chosen_cell=resolved_cid,
                        chosen_character= f"{res.character_name} [Manual]",
                        verdict=verdict,
                        newly_revealed_clue_id=new_clue.clue_id if new_clue else None,
                        newly_revealed_clue_text=(
                            new_clue.render_text(pre_state.board) if new_clue else None
                        ),
                        step_stats=step_stats,
                        terminal_state=(
                            AgentTerminalState.SOLVED
                            if post_state.is_solved
                            else AgentTerminalState.IN_PROGRESS
                        ),
                    )
                    session.traces.append(manual_trace)

            return jsonify(
                {
                    "ok": True,
                    "submission": res.to_dict(session.engine.board),
                    **session.build_payload(),
                }
            )
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/highlight/<cell_id>")
    def highlight_clue(cell_id: str):
        try:
            hl = session.engine.get_revealed_clue_highlights(cell_id)
            return jsonify({"ok": True, "highlight": hl})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.post("/api/hint")
    def get_hint():
        pub_state = session.engine.get_public_state()
        hint = HintEngine.get_hint(pub_state, encoding_mode=session.encoding_mode)
        return jsonify({"ok": True, "hint": hint.to_dict()})

    @app.post("/api/step")
    def step_solve():
        agent = session.make_agent()
        step_num = len(session.traces) + 1
        trace = agent.step(session.engine, step_index=step_num)
        session.traces.append(trace)
        session.cumulative_stats.merge(trace.step_stats)
        session.total_sat_calls += len(trace.sat_queries)
        return jsonify(
            {
                "ok": True,
                "step_trace": trace.to_dict(),
                **session.build_payload(),
            }
        )

    @app.post("/api/auto_solve")
    def auto_solve():
        agent = session.make_agent()
        report = agent.solve(session.engine)
        offset = len(session.traces)
        for idx, tr in enumerate(report.steps, start=1):
            adjusted = DeductionStepTrace(
                step_number=offset + idx,
                active_clue_ids=tr.active_clue_ids,
                num_primary_vars=tr.num_primary_vars,
                num_aux_vars=tr.num_aux_vars,
                num_clauses=tr.num_clauses,
                sat_queries=tr.sat_queries,
                classifications=tr.classifications,
                forced_count_in_step=tr.forced_count_in_step,
                chosen_cell=tr.chosen_cell,
                chosen_character=tr.chosen_character,
                verdict=tr.verdict,
                newly_revealed_clue_id=tr.newly_revealed_clue_id,
                newly_revealed_clue_text=tr.newly_revealed_clue_text,
                step_stats=tr.step_stats,
                terminal_state=tr.terminal_state,
            )
            session.traces.append(adjusted)
        session.cumulative_stats.merge(report.total_stats)
        session.total_sat_calls += report.total_sat_calls
        return jsonify(
            {
                "ok": True,
                "report": report.to_dict(),
                **session.build_payload(),
            }
        )

    @app.post("/api/uniqueness")
    def check_uniqueness():
        uniq = session.engine.check_complete_uniqueness(
            include_opening_verdicts=True,
            encoding_mode=session.encoding_mode,
        )
        return jsonify({"ok": True, "uniqueness": uniq.to_dict()})

    return app


def _find_free_port(preferred: int = 5050) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", preferred)) != 0:
            return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def launch_gui(host: str = "127.0.0.1", port: int | None = None, open_browser: bool = True) -> None:
    chosen_port = port or _find_free_port(5050)
    url = f"http://{host}:{chosen_port}"
    app = create_app()

    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    print(f"\n  Griductive Solver GUI running at: {url}")
    print("  Press Ctrl+C to stop the server.\n")
    app.run(host=host, port=chosen_port, debug=False, use_reloader=False)
