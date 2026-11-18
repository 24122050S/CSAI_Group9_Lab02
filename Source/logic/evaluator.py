"""Direct Semantic Evaluator for all clue templates without calling CNFEncoder (Section 4.2)."""

from __future__ import annotations

from collections import deque
from typing import Iterable, Mapping

from logic.regions import RegionResolver
from logic.validator import ClueValidator
from logic.variables import VariableManager
from models.board import BoardMetadata
from models.clue import Clue
from models.enums import ClueType, CompoundOperator, ParityKind, Status


class SemanticEvaluator:
    """Directly evaluates structured clues against a complete Truth/Status assignment.

    Per Section 4.2:
    "At least one direct semantic evaluator must be implemented for each required clue template.
    Given a complete assignment, this evaluator states whether the clue is true without calling
    the CNF encoder."
    """

    @staticmethod
    def normalize_assignment(
        assignment: Mapping[str, Status | bool] | Mapping[int, bool],
        board: BoardMetadata,
    ) -> dict[str, bool]:
        """Normalize a complete assignment into {cell_id: is_criminal_bool}."""
        vm = VariableManager(board)
        normalized: dict[str, bool] = {}

        for key, val in assignment.items():
            if isinstance(key, int):
                if not vm.is_primary(key):
                    continue  # Ignore auxiliary variables if passed from a SAT model
                cell_id = vm.cell_for(key)
            else:
                cell_id = board.resolve_cell_id(str(key))

            if isinstance(val, Status):
                if val == Status.CRIMINAL:
                    normalized[cell_id] = True
                elif val == Status.INNOCENT:
                    normalized[cell_id] = False
                else:
                    raise ValueError(
                        f"Complete assignment cannot contain UNKNOWN for cell {cell_id}."
                    )
            elif isinstance(val, bool):
                normalized[cell_id] = val
            else:
                raise TypeError(f"Unsupported assignment value {val!r} for {key!r}.")

        missing = [cid for cid in board.cell_ids if cid not in normalized]
        if missing:
            raise ValueError(
                f"Assignment is incomplete; missing primary cells: {missing}"
            )
        return normalized

    @staticmethod
    def _count_matching(
        cells: Iterable[str],
        is_criminal_map: dict[str, bool],
        target_status: Status,
    ) -> int:
        want_bool = target_status == Status.CRIMINAL
        return sum(1 for cid in cells if is_criminal_map[cid] == want_bool)

    @classmethod
    def evaluate(
        cls,
        clue: Clue,
        assignment: Mapping[str, Status | bool] | Mapping[int, bool],
        board: BoardMetadata,
    ) -> bool:
        """Return True iff `clue` holds under the complete `assignment`."""
        ClueValidator.validate(clue, board)
        is_crim = cls.normalize_assignment(assignment, board)

        ct = clue.effective_clue_type()
        k = clue.effective_count()

        if ct == ClueType.FACT:
            cid = board.resolve_cell_id(clue.target)  # type: ignore[arg-type]
            return is_crim[cid] == (clue.status == Status.CRIMINAL)

        if ct == ClueType.SAME:
            c1 = board.resolve_cell_id(clue.target1)  # type: ignore[arg-type]
            c2 = board.resolve_cell_id(clue.target2)  # type: ignore[arg-type]
            return is_crim[c1] == is_crim[c2]

        if ct == ClueType.DIFFERENT:
            c1 = board.resolve_cell_id(clue.target1)  # type: ignore[arg-type]
            c2 = board.resolve_cell_id(clue.target2)  # type: ignore[arg-type]
            return is_crim[c1] != is_crim[c2]

        if ct == ClueType.EXACTLY:
            cells = RegionResolver.resolve(clue.region, board)  # type: ignore[arg-type]
            actual = cls._count_matching(cells, is_crim, clue.target_status)
            return actual == k

        if ct == ClueType.AT_LEAST:
            cells = RegionResolver.resolve(clue.region, board)  # type: ignore[arg-type]
            actual = cls._count_matching(cells, is_crim, clue.target_status)
            return actual >= k  # type: ignore[operator]

        if ct == ClueType.AT_MOST:
            cells = RegionResolver.resolve(clue.region, board)  # type: ignore[arg-type]
            actual = cls._count_matching(cells, is_crim, clue.target_status)
            return actual <= k  # type: ignore[operator]

        # --- Extension 2: Regional Count Comparison ---
        if ct == ClueType.MORE_CRIMINALS:
            r1 = RegionResolver.resolve(clue.region, board)  # type: ignore[arg-type]
            r2 = RegionResolver.resolve(clue.region2, board)  # type: ignore[arg-type]
            c1 = cls._count_matching(r1, is_crim, clue.target_status)
            c2 = cls._count_matching(r2, is_crim, clue.target_status)
            return c1 > c2

        if ct == ClueType.EQUAL_CRIMINALS:
            r1 = RegionResolver.resolve(clue.region, board)  # type: ignore[arg-type]
            r2 = RegionResolver.resolve(clue.region2, board)  # type: ignore[arg-type]
            c1 = cls._count_matching(r1, is_crim, clue.target_status)
            c2 = cls._count_matching(r2, is_crim, clue.target_status)
            return c1 == c2

        # --- Extension 3: Parity Constraint ---
        if ct == ClueType.PARITY:
            cells = RegionResolver.resolve(clue.region, board)  # type: ignore[arg-type]
            actual = cls._count_matching(cells, is_crim, clue.target_status)
            if clue.parity == ParityKind.ODD:
                return (actual % 2) == 1
            return (actual % 2) == 0

        # --- Extension 4: Compound Clues (AND, OR, IMPLIES) ---
        if ct == ClueType.COMPOUND:
            vals = [cls.evaluate(sc, is_crim, board) for sc in clue.sub_clues]
            if clue.operator == CompoundOperator.AND:
                return all(vals)
            if clue.operator == CompoundOperator.OR:
                return any(vals)
            if clue.operator == CompoundOperator.IMPLIES:
                return (not vals[0]) or vals[1]
            raise ValueError(f"Unsupported CompoundOperator: {clue.operator}")

        # --- Extension 5: Orthogonal Connectivity Constraint ---
        if ct == ClueType.CONNECTED:
            cells = RegionResolver.resolve(clue.region, board)  # type: ignore[arg-type]
            want_bool = clue.target_status == Status.CRIMINAL
            active_indices = [
                idx for idx, cid in enumerate(cells) if is_crim[cid] == want_bool
            ]
            if len(active_indices) <= 1:
                return True
            active_set = set(active_indices)
            adj = RegionResolver.orthogonal_neighbors_within(cells, board)
            visited = {active_indices[0]}
            queue: deque[int] = deque([active_indices[0]])
            while queue:
                curr = queue.popleft()
                for nb in adj[curr]:
                    if nb in active_set and nb not in visited:
                        visited.add(nb)
                        queue.append(nb)
            return len(visited) == len(active_set)

        raise ValueError(f"Unsupported ClueType in SemanticEvaluator: {clue.clue_type}")

    @classmethod
    def evaluate_all(
        cls,
        clues: Iterable[Clue],
        assignment: Mapping[str, Status | bool] | Mapping[int, bool],
        board: BoardMetadata,
    ) -> bool:
        """Return True iff every clue in `clues` holds under `assignment`."""
        is_crim = cls.normalize_assignment(assignment, board)
        return all(cls.evaluate(clue, is_crim, board) for clue in clues)
