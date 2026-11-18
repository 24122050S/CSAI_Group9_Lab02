"""Deterministic no-guess Griductive puzzle synthesizer and verifier."""

from __future__ import annotations

import random

from agent.deductive_agent import DeductiveLogicAgent
from agent.uniqueness import UniquenessChecker
from engine.game_engine import GameEngine
from engine.puzzle_loader import SecretPuzzleData
from logic.evaluator import SemanticEvaluator
from logic.regions import RegionResolver
from models.board import BoardMetadata, CellCoord, CharacterInfo
from models.clue import Clue, RegionSpec
from models.enums import (
    AgentTerminalState,
    ClueType,
    Direction,
    ParityKind,
    Status,
)

# 25 alphabetical character names (matching Griductive style in Figure 1 of specification)
ALPHABETICAL_NAMES: tuple[str, ...] = (
    "Abel",
    "Bea",
    "Clara",
    "Derek",
    "Eliza",
    "Franz",
    "Grant",
    "Hannah",
    "Ivy",
    "Jonas",
    "Karl",
    "Leo",
    "Mara",
    "Noah",
    "Owen",
    "Priya",
    "Quilla",
    "Roy",
    "Sophia",
    "Tom",
    "Uma",
    "Victor",
    "Wendy",
    "Xavier",
    "Yara",
)

PROFESSIONS_POOL: tuple[str, ...] = (
    "Astronaut",
    "Clerk",
    "Cook",
    "Detective",
    "Farmer",
    "Guard",
    "Painter",
)


class PuzzleGenerator:
    """Synthesizes and strictly verifies no-guess solvable Griductive puzzles."""

    @staticmethod
    def build_board(grid_size: int, rng: random.Random) -> BoardMetadata:
        total = grid_size * grid_size
        if total > len(ALPHABETICAL_NAMES):
            raise ValueError(f"Grid size {grid_size} exceeds 25 alphabetical names.")
        names = ALPHABETICAL_NAMES[:total]
        chars: list[CharacterInfo] = []
        idx = 0
        for r in range(1, grid_size + 1):
            for c in range(grid_size):
                job = rng.choice(PROFESSIONS_POOL)
                chars.append(
                    CharacterInfo(
                        coord=CellCoord(row=r, col_idx=c),
                        name=names[idx],
                        profession=job,
                    )
                )
                idx += 1
        return BoardMetadata.from_characters(grid_size, chars)

    @staticmethod
    def candidate_clues_for_owner(
        owner_cell: str,
        board: BoardMetadata,
        truth: dict[str, Status],
        include_extensions: bool,
        rng: random.Random,
    ) -> list[Clue]:
        """Generate candidate true clues that `owner_cell` could hold."""
        n = board.grid_size
        candidates: list[Clue] = []
        cid_counter = 0

        def next_id() -> str:
            nonlocal cid_counter
            cid_counter += 1
            return f"cand_{owner_cell}_{cid_counter}"

        def count_crim(reg: RegionSpec) -> tuple[int, int]:
            cells = RegionResolver.resolve(reg, board)
            c_cnt = sum(1 for c in cells if truth[c] == Status.CRIMINAL)
            return c_cnt, len(cells)

        # Core regions: rows, cols, neighbors, small explicit cell lists
        regions: list[RegionSpec] = []
        for r in range(1, n + 1):
            regions.append(RegionSpec.row_region(r))
        for c_idx in range(n):
            col_let = chr(ord("A") + c_idx)
            regions.append(RegionSpec.col_region(col_let))
        for ch in board.characters:
            regions.append(RegionSpec.neighbors(ch.cell_id))
        for _ in range(6):
            sample_sz = rng.choice([2, 3])
            picked = rng.sample(board.cell_ids, sample_sz)
            regions.append(RegionSpec.cell_list(picked))

        if include_extensions:
            regions.append(RegionSpec.corners())
            regions.append(RegionSpec.boundary())
            # Intersections (like Figure 1 C1: neighbors ∩ column)
            for _ in range(5):
                ch = rng.choice(board.characters)
                col_let = chr(ord("A") + rng.randrange(n))
                inter = RegionSpec.intersection(
                    RegionSpec.neighbors(ch.cell_id),
                    RegionSpec.col_region(col_let),
                )
                if len(RegionResolver.resolve(inter, board)) >= 2:
                    regions.append(inter)
            # Common neighbors
            for _ in range(4):
                c1, c2 = rng.sample(board.cell_ids, 2)
                cn = RegionSpec.common_neighbors(c1, c2)
                if len(RegionResolver.resolve(cn, board)) >= 2:
                    regions.append(cn)
            # Directional rays
            for _ in range(4):
                ch = rng.choice(board.characters)
                d = rng.choice(list(Direction))
                dr = RegionSpec.directional(ch.cell_id, d)
                if len(RegionResolver.resolve(dr, board)) >= 2:
                    regions.append(dr)
            # Profession regions
            jobs_present = sorted({ch.profession for ch in board.characters})
            for job in jobs_present:
                pr = RegionSpec.by_profession(job)
                if len(RegionResolver.resolve(pr, board)) >= 2:
                    regions.append(pr)

        for reg in regions:
            k_crim, sz = count_crim(reg)
            if sz == 0:
                continue
            if k_crim == 0:
                candidates.append(
                    Clue(f"clue_{owner_cell}", owner_cell, ClueType.NO, region=reg)
                )
            else:
                candidates.append(
                    Clue(
                        f"clue_{owner_cell}",
                        owner_cell,
                        ClueType.EXACTLY,
                        count=k_crim,
                        region=reg,
                    )
                )
            # Tight AT_LEAST / AT_MOST bounds
            if k_crim >= 1:
                candidates.append(
                    Clue(
                        f"clue_{owner_cell}",
                        owner_cell,
                        ClueType.AT_LEAST,
                        count=k_crim,
                        region=reg,
                    )
                )
            if k_crim < sz:
                candidates.append(
                    Clue(
                        f"clue_{owner_cell}",
                        owner_cell,
                        ClueType.AT_MOST,
                        count=k_crim,
                        region=reg,
                    )
                )
            # Innocent-phrased EXACTLY variant
            k_inno = sz - k_crim
            if 0 < k_inno < sz and rng.random() < 0.35:
                candidates.append(
                    Clue(
                        f"clue_{owner_cell}",
                        owner_cell,
                        ClueType.EXACTLY,
                        count=k_inno,
                        region=reg,
                        target_status=Status.INNOCENT,
                    )
                )

            if include_extensions and sz >= 3:
                par = ParityKind.ODD if (k_crim % 2 == 1) else ParityKind.EVEN
                candidates.append(
                    Clue(
                        f"clue_{owner_cell}",
                        owner_cell,
                        ClueType.PARITY,
                        region=reg,
                        parity=par,
                    )
                )

        # Binary clues SAME and DIFFERENT
        other_pairs = [
            rng.sample(board.cell_ids, 2) for _ in range(min(14, n * n))
        ]
        for c1, c2 in other_pairs:
            if truth[c1] == truth[c2]:
                candidates.append(
                    Clue(
                        f"clue_{owner_cell}",
                        owner_cell,
                        ClueType.SAME,
                        target1=c1,
                        target2=c2,
                    )
                )
            else:
                candidates.append(
                    Clue(
                        f"clue_{owner_cell}",
                        owner_cell,
                        ClueType.DIFFERENT,
                        target1=c1,
                        target2=c2,
                    )
                )

        # Regional comparisons (Extension 2)
        if include_extensions:
            row_col_regs = [RegionSpec.row_region(r) for r in range(1, n + 1)] + [
                RegionSpec.col_region(chr(ord("A") + c)) for c in range(n)
            ]
            for _ in range(8):
                r1, r2 = rng.sample(row_col_regs, 2)
                c1, _ = count_crim(r1)
                c2, _ = count_crim(r2)
                if c1 > c2:
                    candidates.append(
                        Clue(
                            f"clue_{owner_cell}",
                            owner_cell,
                            ClueType.MORE_CRIMINALS,
                            region=r1,
                            region2=r2,
                        )
                    )
                elif c1 == c2:
                    candidates.append(
                        Clue(
                            f"clue_{owner_cell}",
                            owner_cell,
                            ClueType.EQUAL_CRIMINALS,
                            region=r1,
                            region2=r2,
                        )
                    )

        # Occasionally include direct FACT clues (placed at lower priority)
        for target_cid in rng.sample(board.cell_ids, min(4, len(board.cell_ids))):
            if target_cid != owner_cell:
                candidates.append(
                    Clue(
                        f"clue_{owner_cell}",
                        owner_cell,
                        ClueType.FACT,
                        target=target_cid,
                        status=truth[target_cid],
                    )
                )

        _ = next_id  # Silence unused helper if IDs standardized to clue_<cell>
        return candidates

    @classmethod
    def generate(
        cls,
        puzzle_id: str,
        title: str,
        grid_size: int,
        seed: int,
        difficulty: str = "Medium",
        include_extensions: bool = True,
        num_initial_revealed: int = 2,
        description: str = "",
    ) -> SecretPuzzleData:
        """Construct a guaranteed unique, 100% no-guess solvable Griductive puzzle."""
        rng = random.Random(seed)
        agent = DeductiveLogicAgent(use_witness_pruning=True)

        for _attempt in range(40):
            board = cls.build_board(grid_size, rng)
            # Balanced random ground truth (between 35% and 65% criminals)
            total = grid_size * grid_size
            num_crim = rng.randint(max(2, int(total * 0.35)), min(total - 2, int(total * 0.65)))
            crim_cells = set(rng.sample(board.cell_ids, num_crim))
            truth = {
                cid: (Status.CRIMINAL if cid in crim_cells else Status.INNOCENT)
                for cid in board.cell_ids
            }

            initial_revealed = tuple(sorted(rng.sample(board.cell_ids, num_initial_revealed), key=lambda c: CellCoord.parse(c)))
            revealed_set: set[str] = set(initial_revealed)
            assigned_clues: dict[str, Clue] = {}
            frontier_queue: list[str] = list(initial_revealed)

            success = True
            while len(revealed_set) < total:
                # Check which cells are already forced by current assigned clues + revealed_set
                known_verdicts = {cid: truth[cid] for cid in revealed_set}
                active_clues = [assigned_clues[cid] for cid in revealed_set if cid in assigned_clues]

                # Build temporary puzzle snapshot to query forced cells
                from logic.cnf_encoder import CNFEncoder
                from solver.dpll import DPLLSolver

                enc = CNFEncoder(board)
                kb = enc.build_knowledge_base(active_clues, known_verdicts)
                solver = DPLLSolver()
                unresolved = [cid for cid in board.cell_ids if cid not in revealed_set]

                forced_now: list[str] = []
                for cid in unresolved:
                    vid = kb.variables.var_for(cid)
                    opp_lit = -vid if truth[cid] == Status.CRIMINAL else vid
                    if not solver.solve(kb.clauses, num_vars=kb.variables.total_vars, assumptions=[opp_lit]).is_sat:
                        forced_now.append(cid)

                if forced_now:
                    # Pick the deterministic row-major forced cell just like DeductiveLogicAgent!
                    next_cell = forced_now[0]
                    revealed_set.add(next_cell)
                    frontier_queue.append(next_cell)
                    continue

                # Need to attach a clue to an already-revealed clue-less card in frontier_queue
                clue_less = [cid for cid in frontier_queue if cid not in assigned_clues]
                if not clue_less:
                    success = False
                    break

                owner = clue_less[0]
                cands = cls.candidate_clues_for_owner(
                    owner, board, truth, include_extensions=include_extensions, rng=rng
                )
                # Prefer non-FACT clues that unlock 1..2 new cells (deep deduction waves!)
                rng.shuffle(cands)
                cands.sort(key=lambda c: 1 if c.clue_type == ClueType.FACT else 0)

                picked_clue: Clue | None = None
                fallback_informative: Clue | None = None

                for cand in cands:
                    trial_clues = active_clues + [cand]
                    enc_t = CNFEncoder(board)
                    kb_t = enc_t.build_knowledge_base(trial_clues, known_verdicts)
                    newly_forced = 0
                    for cid in unresolved:
                        vid = kb_t.variables.var_for(cid)
                        opp_lit = -vid if truth[cid] == Status.CRIMINAL else vid
                        if not solver.solve(kb_t.clauses, num_vars=kb_t.variables.total_vars, assumptions=[opp_lit]).is_sat:
                            newly_forced += 1
                    if 1 <= newly_forced <= 2 and cand.clue_type != ClueType.FACT:
                        picked_clue = cand
                        break
                    if newly_forced >= 1 and picked_clue is None:
                        picked_clue = cand
                    elif fallback_informative is None and cand.clue_type != ClueType.FACT:
                        fallback_informative = cand

                chosen = picked_clue or fallback_informative
                if chosen is None:
                    success = False
                    break
                assigned_clues[owner] = chosen

            if not success:
                continue

            # Assign true, non-FACT flavor clues to any remaining revealed cards (e.g. last card)
            for cid in board.cell_ids:
                if cid not in assigned_clues:
                    cands = [
                        c
                        for c in cls.candidate_clues_for_owner(
                            cid, board, truth, include_extensions=include_extensions, rng=rng
                        )
                        if c.clue_type != ClueType.FACT
                    ]
                    if cands:
                        assigned_clues[cid] = rng.choice(cands)

            puzzle = SecretPuzzleData(
                puzzle_id=puzzle_id,
                title=title,
                difficulty=difficulty,
                description=description,
                board=board,
                ground_truth=truth,
                clues=assigned_clues,
                initial_revealed=initial_revealed,
            )

            # Strict end-to-end verification:
            # 1. All clues semantically true
            if not SemanticEvaluator.evaluate_all(assigned_clues.values(), truth, board):
                continue
            # 2. Complete clue set + opening verdicts has UNIQUE global solution
            uniq = UniquenessChecker.check(
                board,
                assigned_clues.values(),
                initial_verdicts={cid: truth[cid] for cid in initial_revealed},
            )
            if not (uniq.is_consistent and uniq.is_unique):
                continue
            # 3. DeductiveLogicAgent solves 100% of cells without guessing!
            eng = GameEngine(puzzle)
            rep = agent.solve(eng)
            if rep.terminal_state == AgentTerminalState.SOLVED and eng.get_public_state().is_solved:
                return puzzle

        raise RuntimeError(f"Failed to synthesize valid puzzle {puzzle_id} after 40 attempts.")
