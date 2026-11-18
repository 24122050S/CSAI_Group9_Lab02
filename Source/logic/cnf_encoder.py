"""Automatic CNF Encoder for clues and public knowledge base KB_t (Section 3.3 & 4.2)."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Sequence

from logic.regions import RegionResolver
from logic.validator import ClueValidator
from logic.variables import VariableManager
from models.board import BoardMetadata
from models.clue import Clue
from models.enums import ClueType, CompoundOperator, EncodingMode, ParityKind, Status
from models.state import PublicGameState

Clause = tuple[int, ...]
CNFFormula = list[Clause]


@dataclass(frozen=True)
class EncodedKnowledgeBase:
    """Compiled CNF knowledge base KB_t together with variable & clause counts (Section 4.2)."""

    board: BoardMetadata
    variables: VariableManager
    clauses: tuple[Clause, ...]
    encoding_mode: EncodingMode
    num_primary_vars: int
    num_aux_vars: int
    num_clauses: int
    active_clue_ids: tuple[str, ...]
    proved_verdict_cells: tuple[str, ...]


class CNFEncoder:
    """Reusable automatic converter from structured Griductive clues to CNF.

    Strictly operates on public board topology, revealed clues, and proved verdicts.
    Never accesses hidden labels or unrevealed clues (Section 4.2).
    """

    def __init__(
        self,
        board: BoardMetadata,
        encoding_mode: EncodingMode = EncodingMode.COMBINATORIAL,
    ) -> None:
        self._board = board
        self._encoding_mode = encoding_mode
        self._vm = VariableManager(board)

    @property
    def board(self) -> BoardMetadata:
        return self._board

    @property
    def variables(self) -> VariableManager:
        return self._vm

    @property
    def encoding_mode(self) -> EncodingMode:
        return self._encoding_mode

    # ------------------------------------------------------------------
    # Cardinality Encodings over arbitrary literal sequences
    # ------------------------------------------------------------------
    def _encode_at_most_combinatorial(self, k: int, literals: Sequence[int]) -> CNFFormula:
        n = len(literals)
        if k < 0:
            return [()]  # Unsatisfiable empty clause
        if k >= n:
            return []  # Trivially satisfied
        if k == 0:
            return [(-lit,) for lit in literals]
        # Every (k + 1)-subset cannot have all literals True simultaneously
        return [tuple(-lit for lit in subset) for subset in combinations(literals, k + 1)]

    def _encode_at_most_sequential(self, k: int, literals: Sequence[int]) -> CNFFormula:
        """Sinz (2005) Sequential Counter encoding for sum(literals) <= k."""
        n = len(literals)
        if k < 0:
            return [()]
        if k >= n:
            return []
        if k == 0:
            return [(-lit,) for lit in literals]

        # Here 1 <= k < n, so n >= 2. Allocate s[i][j] for i in 0..n-2, j in 0..k-1
        s: list[list[int]] = [
            [self._vm.new_aux_var("sc") for _ in range(k)] for _ in range(n - 1)
        ]
        clauses: CNFFormula = []

        # Base step i = 0 (first literal)
        clauses.append((-literals[0], s[0][0]))
        for j in range(1, k):
            clauses.append((-s[0][j],))

        # Inductive steps i = 1 .. n - 2
        for i in range(1, n - 1):
            lit_i = literals[i]
            clauses.append((-lit_i, s[i][0]))
            clauses.append((-s[i - 1][0], s[i][0]))
            for j in range(1, k):
                clauses.append((-lit_i, -s[i - 1][j - 1], s[i][j]))
                clauses.append((-s[i - 1][j], s[i][j]))
            clauses.append((-lit_i, -s[i - 1][k - 1]))

        # Final literal i = n - 1
        clauses.append((-literals[n - 1], -s[n - 2][k - 1]))
        return clauses

    def encode_at_most(self, k: int, literals: Sequence[int]) -> CNFFormula:
        """Encode sum_{l in literals} l <= k according to self.encoding_mode."""
        if self._encoding_mode == EncodingMode.SEQUENTIAL:
            return self._encode_at_most_sequential(k, literals)
        return self._encode_at_most_combinatorial(k, literals)

    def encode_at_least(self, k: int, literals: Sequence[int]) -> CNFFormula:
        """Encode sum_{l in literals} l >= k."""
        n = len(literals)
        if k <= 0:
            return []
        if k > n:
            return [()]
        if k == n:
            return [(lit,) for lit in literals]

        if self._encoding_mode == EncodingMode.SEQUENTIAL:
            # sum(l) >= k  <=>  sum(-l) <= n - k
            negated = [-lit for lit in literals]
            return self._encode_at_most_sequential(n - k, negated)

        # Direct combinatorial: every (n - k + 1)-subset must contain at least one True literal
        subset_size = n - k + 1
        return [tuple(subset) for subset in combinations(literals, subset_size)]

    def encode_exactly(self, k: int, literals: Sequence[int]) -> CNFFormula:
        """Encode sum_{l in literals} l == k."""
        n = len(literals)
        if k < 0 or k > n:
            return [()]
        if k == 0:
            return [(-lit,) for lit in literals]
        if k == n:
            return [(lit,) for lit in literals]
        return self.encode_at_most(k, literals) + self.encode_at_least(k, literals)

    def _encode_parity(self, literals: Sequence[int], parity: ParityKind) -> CNFFormula:
        """Encode XOR chain over `literals` using Tseitin auxiliary variables (Extension 3)."""
        n = len(literals)
        want_odd = parity == ParityKind.ODD
        if n == 0:
            return [()] if want_odd else []
        if n == 1:
            return [(literals[0],)] if want_odd else [(-literals[0],)]
        if n == 2:
            a, b = literals[0], literals[1]
            if want_odd:
                return [(a, b), (-a, -b)]
            return [(-a, b), (a, -b)]

        clauses: CNFFormula = []
        acc = literals[0]
        for idx in range(1, n - 1):
            b = literals[idx]
            z = self._vm.new_aux_var("xor")
            # z <-> (acc XOR b)
            clauses.append((-acc, -b, -z))
            clauses.append((-acc, b, z))
            clauses.append((acc, -b, z))
            clauses.append((acc, b, -z))
            acc = z

        last = literals[n - 1]
        if want_odd:
            clauses.append((acc, last))
            clauses.append((-acc, -last))
        else:
            clauses.append((-acc, last))
            clauses.append((acc, -last))
        return clauses

    def _region_literals(self, cells: Iterable[str], target_status: Status) -> list[int]:
        return [self._vm.literal_for_status(cid, target_status) for cid in cells]

    # ------------------------------------------------------------------
    # Extension 4 & 5 Helpers: Disjunction Relaxation, Structural Negation, 2D Connectivity
    # ------------------------------------------------------------------
    def _encode_disjunction(self, branches: Sequence[CNFFormula]) -> CNFFormula:
        """Encode (F_1 v F_2 v ... v F_q) soundly even when sub-formulas use auxiliary vars."""
        # If any branch is empty [], it is trivially True -> whole disjunction is True!
        for b in branches:
            if len(b) == 0:
                return []

        # Drop unsatisfiable branches containing an empty clause ()
        satisfiable_branches = [b for b in branches if not any(len(cl) == 0 for cl in b)]
        if not satisfiable_branches:
            return [()]
        if len(satisfiable_branches) == 1:
            return list(satisfiable_branches[0])

        selectors = [self._vm.new_aux_var("or_sel") for _ in satisfiable_branches]
        clauses: CNFFormula = [tuple(selectors)]
        for sel, formula in zip(selectors, satisfiable_branches):
            for cl in formula:
                clauses.append((-sel,) + cl)
        return clauses

    def _encode_negated_clue(self, clue: Clue) -> CNFFormula:
        """Encode ~clue into an equisatisfiable CNF formula (used by IMPLIES and nested COMPOUND)."""
        ct = clue.effective_clue_type()
        k = clue.effective_count()

        if ct == ClueType.FACT:
            opp = Status.INNOCENT if clue.status == Status.CRIMINAL else Status.CRIMINAL
            return [(self._vm.literal_for_status(clue.target, opp),)]  # type: ignore[arg-type]

        if ct == ClueType.SAME:
            return self.encode_clue(
                Clue(f"neg_{clue.clue_id}", clue.owner_cell, ClueType.DIFFERENT, target1=clue.target1, target2=clue.target2)
            )

        if ct == ClueType.DIFFERENT:
            return self.encode_clue(
                Clue(f"neg_{clue.clue_id}", clue.owner_cell, ClueType.SAME, target1=clue.target1, target2=clue.target2)
            )

        if ct == ClueType.AT_LEAST:
            cells = RegionResolver.resolve(clue.region, self._board)  # type: ignore[arg-type]
            lits = self._region_literals(cells, clue.target_status)
            return self.encode_at_most((k or 0) - 1, lits)

        if ct == ClueType.AT_MOST:
            cells = RegionResolver.resolve(clue.region, self._board)  # type: ignore[arg-type]
            lits = self._region_literals(cells, clue.target_status)
            return self.encode_at_least((k or 0) + 1, lits)

        if ct == ClueType.EXACTLY:
            cells = RegionResolver.resolve(clue.region, self._board)  # type: ignore[arg-type]
            lits = self._region_literals(cells, clue.target_status)
            kk = k or 0
            return self._encode_disjunction(
                [self.encode_at_most(kk - 1, lits), self.encode_at_least(kk + 1, lits)]
            )

        if ct == ClueType.PARITY:
            opp_p = ParityKind.EVEN if clue.parity == ParityKind.ODD else ParityKind.ODD
            cells = RegionResolver.resolve(clue.region, self._board)  # type: ignore[arg-type]
            lits = self._region_literals(cells, clue.target_status)
            return self._encode_parity(lits, opp_p)

        if ct == ClueType.MORE_CRIMINALS:
            # ~(count(R1) > count(R2))  <=>  (count(R2) > count(R1)) v (count(R1) == count(R2))
            b1 = self.encode_clue(
                Clue(
                    f"neg1_{clue.clue_id}",
                    clue.owner_cell,
                    ClueType.MORE_CRIMINALS,
                    region=clue.region2,
                    region2=clue.region,
                    target_status=clue.target_status,
                )
            )
            b2 = self.encode_clue(
                Clue(
                    f"neg2_{clue.clue_id}",
                    clue.owner_cell,
                    ClueType.EQUAL_CRIMINALS,
                    region=clue.region,
                    region2=clue.region2,
                    target_status=clue.target_status,
                )
            )
            return self._encode_disjunction([b1, b2])

        if ct == ClueType.EQUAL_CRIMINALS:
            b1 = self.encode_clue(
                Clue(
                    f"neg1_{clue.clue_id}",
                    clue.owner_cell,
                    ClueType.MORE_CRIMINALS,
                    region=clue.region,
                    region2=clue.region2,
                    target_status=clue.target_status,
                )
            )
            b2 = self.encode_clue(
                Clue(
                    f"neg2_{clue.clue_id}",
                    clue.owner_cell,
                    ClueType.MORE_CRIMINALS,
                    region=clue.region2,
                    region2=clue.region,
                    target_status=clue.target_status,
                )
            )
            return self._encode_disjunction([b1, b2])

        if ct == ClueType.COMPOUND:
            if clue.operator == CompoundOperator.AND:
                return self._encode_disjunction(
                    [self._encode_negated_clue(sc) for sc in clue.sub_clues]
                )
            if clue.operator == CompoundOperator.OR:
                out: CNFFormula = []
                for sc in clue.sub_clues:
                    out.extend(self._encode_negated_clue(sc))
                return out
            if clue.operator == CompoundOperator.IMPLIES:
                # ~(A -> B) === A ^ ~B
                return self.encode_clue(clue.sub_clues[0]) + self._encode_negated_clue(
                    clue.sub_clues[1]
                )

        raise ValueError(f"Negation not supported for ClueType {clue.clue_type}")

    def _encode_connected(self, cells: tuple[str, ...], target_status: Status) -> CNFFormula:
        """Encode orthogonal (4-grid) connectivity of active `target_status` cells in `cells`.

        - Fast 0-aux-var path encoding when `cells` forms a simple contiguous 1D chain:
          forbids any (1 ... 0 ... 1) triple via (~l_a v l_b v ~l_c).
        - Exact Canonical-Root + BFS Layered Reachability encoding for general 2D regions.
        """
        m = len(cells)
        if m <= 1:
            return []

        lits = self._region_literals(cells, target_status)
        adj = RegionResolver.orthogonal_neighbors_within(cells, self._board)

        # Check if `cells` in canonical order forms a contiguous 1D path 0 - 1 - ... - (m-1)
        is_simple_chain = (
            adj[0] == (1,)
            and adj[m - 1] == (m - 2,)
            and all(set(adj[i]) == {i - 1, i + 1} for i in range(1, m - 1))
        )
        if is_simple_chain:
            return [
                (-lits[a], lits[b], -lits[c])
                for a in range(m)
                for b in range(a + 1, m)
                for c in range(b + 1, m)
            ]

        # General 2D region: Canonical minimum-index root r_i + (m-1)-step BFS reachability
        clauses: CNFFormula = []
        roots: list[int] = []
        for i in range(m):
            ri = self._vm.new_aux_var("conn_root")
            roots.append(ri)
            clauses.append((-ri, lits[i]))
            for p in range(i):
                clauses.append((-ri, -lits[p]))
            # (l_i ^ bigwedge_{p<i} ~l_p) -> r_i
            clauses.append(tuple([lits[p] for p in range(i)] + [-lits[i], ri]))

        prev_reach = roots
        for _step in range(1, m):
            curr_reach = [self._vm.new_aux_var("conn_reach") for _ in range(m)]
            for i in range(m):
                # Reachable only if active in S
                clauses.append((-curr_reach[i], lits[i]))
                # Reachable at step t only if already reached at t-1 or adjacent to t-1
                clauses.append(
                    tuple([-curr_reach[i], prev_reach[i]] + [prev_reach[nb] for nb in adj[i]])
                )
            prev_reach = curr_reach

        # Every active vertex in S must be reached from the canonical root within m-1 steps
        for i in range(m):
            clauses.append((-lits[i], prev_reach[i]))

        return clauses

    # ------------------------------------------------------------------
    # Clue -> CNF Conversion
    # ------------------------------------------------------------------
    def encode_clue(self, clue: Clue) -> CNFFormula:
        """Validate `clue` and convert it automatically to a list of CNF clauses."""
        ClueValidator.validate(clue, self._board)
        ct = clue.effective_clue_type()
        k = clue.effective_count()

        if ct == ClueType.FACT:
            lit = self._vm.literal_for_status(clue.target, clue.status)  # type: ignore[arg-type]
            return [(lit,)]

        if ct == ClueType.SAME:
            v1 = self._vm.var_for(clue.target1)  # type: ignore[arg-type]
            v2 = self._vm.var_for(clue.target2)  # type: ignore[arg-type]
            # C_1 <-> C_2  ===  (~C_1 v C_2) ^ (C_1 v ~C_2)
            return [(-v1, v2), (v1, -v2)]

        if ct == ClueType.DIFFERENT:
            v1 = self._vm.var_for(clue.target1)  # type: ignore[arg-type]
            v2 = self._vm.var_for(clue.target2)  # type: ignore[arg-type]
            # C_1 XOR C_2  ===  (C_1 v C_2) ^ (~C_1 v ~C_2)
            return [(v1, v2), (-v1, -v2)]

        if ct == ClueType.EXACTLY:
            cells = RegionResolver.resolve(clue.region, self._board)  # type: ignore[arg-type]
            lits = self._region_literals(cells, clue.target_status)
            return self.encode_exactly(k, lits)  # type: ignore[arg-type]

        if ct == ClueType.AT_LEAST:
            cells = RegionResolver.resolve(clue.region, self._board)  # type: ignore[arg-type]
            lits = self._region_literals(cells, clue.target_status)
            return self.encode_at_least(k, lits)  # type: ignore[arg-type]

        if ct == ClueType.AT_MOST:
            cells = RegionResolver.resolve(clue.region, self._board)  # type: ignore[arg-type]
            lits = self._region_literals(cells, clue.target_status)
            return self.encode_at_most(k, lits)  # type: ignore[arg-type]

        # --- Extension 2: Regional Count Comparison ---
        if ct in (ClueType.MORE_CRIMINALS, ClueType.EQUAL_CRIMINALS):
            r1 = RegionResolver.resolve(clue.region, self._board)  # type: ignore[arg-type]
            r2 = RegionResolver.resolve(clue.region2, self._board)  # type: ignore[arg-type]
            set1, set2 = set(r1), set(r2)
            # Cancel overlapping cells that contribute identically to both sides
            only1 = [cid for cid in r1 if cid not in set2]
            only2 = [cid for cid in r2 if cid not in set1]

            lits1 = self._region_literals(only1, clue.target_status)
            # Introduce explicit negated auxiliary variables neg_j <-> ~lit_j for R2 \ R1
            neg_lits2: list[int] = []
            aux_equiv_clauses: CNFFormula = []
            for lit_j in self._region_literals(only2, clue.target_status):
                aux_neg = self._vm.new_aux_var("cmp_neg")
                # aux_neg <-> -lit_j  ===  (~aux_neg v ~lit_j) ^ (aux_neg v lit_j)
                aux_equiv_clauses.append((-aux_neg, -lit_j))
                aux_equiv_clauses.append((aux_neg, lit_j))
                neg_lits2.append(aux_neg)

            combined = lits1 + neg_lits2
            if ct == ClueType.MORE_CRIMINALS:
                # sum(only1) - sum(only2) >= 1  <=>  sum(only1) + sum(~only2) >= |only2| + 1
                return aux_equiv_clauses + self.encode_at_least(len(only2) + 1, combined)
            # sum(only1) == sum(only2)  <=>  sum(only1) + sum(~only2) == |only2|
            return aux_equiv_clauses + self.encode_exactly(len(only2), combined)

        # --- Extension 3: Parity Constraint ---
        if ct == ClueType.PARITY:
            cells = RegionResolver.resolve(clue.region, self._board)  # type: ignore[arg-type]
            lits = self._region_literals(cells, clue.target_status)
            return self._encode_parity(lits, clue.parity)  # type: ignore[arg-type]

        # --- Extension 4: Compound Clues (AND, OR, IMPLIES) ---
        if ct == ClueType.COMPOUND:
            if clue.operator == CompoundOperator.AND:
                out_clauses: CNFFormula = []
                for sc in clue.sub_clues:
                    out_clauses.extend(self.encode_clue(sc))
                return out_clauses
            if clue.operator == CompoundOperator.OR:
                return self._encode_disjunction([self.encode_clue(sc) for sc in clue.sub_clues])
            if clue.operator == CompoundOperator.IMPLIES:
                # A -> B  ===  ~A v B
                neg_a = self._encode_negated_clue(clue.sub_clues[0])
                pos_b = self.encode_clue(clue.sub_clues[1])
                return self._encode_disjunction([neg_a, pos_b])
            raise ValueError(f"Unsupported CompoundOperator: {clue.operator}")

        # --- Extension 5: Orthogonal Connectivity Constraint ---
        if ct == ClueType.CONNECTED:
            cells = RegionResolver.resolve(clue.region, self._board)  # type: ignore[arg-type]
            return self._encode_connected(cells, clue.target_status)

        raise ValueError(f"Unsupported ClueType in CNFEncoder: {clue.clue_type}")

    def encode_verdict_unit_clause(self, cell_ref: str, status: Status) -> Clause:
        """Encode a proved verdict as a unit clause [C_i] or [¬C_i]."""
        return (self._vm.literal_for_status(cell_ref, status),)

    # ------------------------------------------------------------------
    # Knowledge Base KB_t Construction (Section 4.2)
    # ------------------------------------------------------------------
    def build_knowledge_base(
        self,
        revealed_clues: Iterable[Clue],
        proved_verdicts: dict[str, Status] | None = None,
    ) -> EncodedKnowledgeBase:
        """Build KB_t = CNF(revealed_clues) ^ unit clauses for proved verdicts."""
        self._vm.reset_auxiliary_vars()
        clauses: CNFFormula = []
        clue_ids: list[str] = []

        for clue in revealed_clues:
            clauses.extend(self.encode_clue(clue))
            clue_ids.append(clue.clue_id)

        proved_cells: list[str] = []
        if proved_verdicts:
            # Sort in canonical board order for strict determinism
            for cid in self._board.cell_ids:
                if cid in proved_verdicts:
                    clauses.append(self.encode_verdict_unit_clause(cid, proved_verdicts[cid]))
                    proved_cells.append(cid)

        return EncodedKnowledgeBase(
            board=self._board,
            variables=self._vm,
            clauses=tuple(clauses),
            encoding_mode=self._encoding_mode,
            num_primary_vars=self._vm.num_primary_vars,
            num_aux_vars=self._vm.num_aux_vars,
            num_clauses=len(clauses),
            active_clue_ids=tuple(clue_ids),
            proved_verdict_cells=tuple(proved_cells),
        )

    def build_from_public_state(self, state: PublicGameState) -> EncodedKnowledgeBase:
        """Build KB_t directly from a PublicGameState (strictly no hidden information)."""
        return self.build_knowledge_base(
            revealed_clues=state.revealed_clues(),
            proved_verdicts=state.proved_verdicts(),
        )
