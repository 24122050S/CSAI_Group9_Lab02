"""Region resolution for the 4 core region types and Extension 1 advanced regions."""

from __future__ import annotations

from models.board import BoardMetadata, CellCoord, col_letter_to_index
from models.clue import Clue, RegionSpec
from models.enums import ClueType, Direction, RegionType


class RegionResolver:
    """Resolves structured RegionSpec instances into canonical row-major tuples of cell IDs."""

    @staticmethod
    def _neighbors_of_coord(coord: CellCoord, grid_size: int) -> tuple[CellCoord, ...]:
        coords: list[CellCoord] = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr = coord.row + dr
                nc = coord.col_idx + dc
                if 1 <= nr <= grid_size and 0 <= nc < grid_size:
                    coords.append(CellCoord(row=nr, col_idx=nc))
        coords.sort()
        return tuple(coords)

    @classmethod
    def resolve(cls, region: RegionSpec, board: BoardMetadata) -> tuple[str, ...]:
        """Return distinct cell IDs belonging to `region` in canonical row-major order."""
        n = board.grid_size
        rt = region.region_type

        if rt == RegionType.ROW:
            if region.row is None or not (1 <= region.row <= n):
                raise ValueError(f"Invalid row {region.row!r} for {n}x{n} board.")
            return tuple(
                CellCoord(row=region.row, col_idx=c).cell_id for c in range(n)
            )

        if rt == RegionType.COL:
            if region.col is None:
                raise ValueError("Column region requires `col` letter.")
            c_idx = col_letter_to_index(region.col)
            if not (0 <= c_idx < n):
                raise ValueError(f"Invalid column {region.col!r} for {n}x{n} board.")
            return tuple(
                CellCoord(row=r, col_idx=c_idx).cell_id for r in range(1, n + 1)
            )

        if rt == RegionType.NEIGHBORS:
            if not region.target:
                raise ValueError("NEIGHBORS region requires `target`.")
            ch = board.get_character(region.target)
            return tuple(c.cell_id for c in cls._neighbors_of_coord(ch.coord, n))

        if rt == RegionType.CELL_LIST:
            if not region.cells:
                raise ValueError("CELL_LIST region must specify at least one cell.")
            coords: list[CellCoord] = []
            seen: set[str] = set()
            for raw in region.cells:
                ch = board.get_character(raw)
                if ch.cell_id in seen:
                    raise ValueError(
                        f"Duplicate cell {ch.cell_id!r} in explicit CELL_LIST region."
                    )
                seen.add(ch.cell_id)
                coords.append(ch.coord)
            coords.sort()
            return tuple(c.cell_id for c in coords)

        # --- Extension 1: Advanced Region Expressions ---
        if rt == RegionType.INTERSECTION:
            if len(region.sub_regions) < 2:
                raise ValueError("INTERSECTION region requires at least 2 sub_regions.")
            sets = [set(cls.resolve(sr, board)) for sr in region.sub_regions]
            common = set.intersection(*sets)
            return tuple(cid for cid in board.cell_ids if cid in common)

        if rt == RegionType.COMMON_NEIGHBORS:
            if not region.target or not region.target2:
                raise ValueError("COMMON_NEIGHBORS requires `target` and `target2`.")
            ch1 = board.get_character(region.target)
            ch2 = board.get_character(region.target2)
            if ch1.cell_id == ch2.cell_id:
                raise ValueError("COMMON_NEIGHBORS targets must be distinct.")
            n1 = {c.cell_id for c in cls._neighbors_of_coord(ch1.coord, n)}
            n2 = {c.cell_id for c in cls._neighbors_of_coord(ch2.coord, n)}
            common = n1 & n2
            return tuple(cid for cid in board.cell_ids if cid in common)

        if rt == RegionType.CORNERS:
            corners = sorted(
                {
                    CellCoord(1, 0),
                    CellCoord(1, n - 1),
                    CellCoord(n, 0),
                    CellCoord(n, n - 1),
                }
            )
            return tuple(c.cell_id for c in corners)

        if rt == RegionType.BOUNDARY:
            coords = [
                ch.coord
                for ch in board.characters
                if ch.coord.row in (1, n) or ch.coord.col_idx in (0, n - 1)
            ]
            return tuple(c.cell_id for c in coords)

        if rt == RegionType.BETWEEN:
            if not region.target or not region.target2:
                raise ValueError("BETWEEN requires `target` and `target2`.")
            c1 = board.get_character(region.target).coord
            c2 = board.get_character(region.target2).coord
            if c1 == c2:
                raise ValueError("BETWEEN targets must be distinct.")
            if c1.row == c2.row:
                lo, hi = min(c1.col_idx, c2.col_idx), max(c1.col_idx, c2.col_idx)
                return tuple(
                    CellCoord(row=c1.row, col_idx=ci).cell_id for ci in range(lo + 1, hi)
                )
            if c1.col_idx == c2.col_idx:
                lo, hi = min(c1.row, c2.row), max(c1.row, c2.row)
                return tuple(
                    CellCoord(row=ri, col_idx=c1.col_idx).cell_id
                    for ri in range(lo + 1, hi)
                )
            raise ValueError(
                f"BETWEEN targets {c1.cell_id} and {c2.cell_id} must share a row or column."
            )

        if rt == RegionType.DIRECTIONAL:
            if not region.target or region.direction is None:
                raise ValueError("DIRECTIONAL requires `target` and `direction`.")
            c0 = board.get_character(region.target).coord
            d = region.direction
            if d == Direction.LEFT:
                return tuple(
                    CellCoord(row=c0.row, col_idx=ci).cell_id for ci in range(0, c0.col_idx)
                )
            if d == Direction.RIGHT:
                return tuple(
                    CellCoord(row=c0.row, col_idx=ci).cell_id
                    for ci in range(c0.col_idx + 1, n)
                )
            if d == Direction.ABOVE:
                return tuple(
                    CellCoord(row=ri, col_idx=c0.col_idx).cell_id for ri in range(1, c0.row)
                )
            if d == Direction.BELOW:
                return tuple(
                    CellCoord(row=ri, col_idx=c0.col_idx).cell_id
                    for ri in range(c0.row + 1, n + 1)
                )
            raise ValueError(f"Unsupported direction: {d}")

        if rt == RegionType.PROFESSION:
            if not region.profession or not region.profession.strip():
                raise ValueError("PROFESSION region requires non-empty `profession`.")
            prof_lower = region.profession.strip().lower()
            return tuple(
                ch.cell_id
                for ch in board.characters
                if ch.profession.strip().lower() == prof_lower
            )

        raise ValueError(f"Unsupported RegionType: {rt}")

    @staticmethod
    def orthogonal_neighbors_within(
        cells: tuple[str, ...],
        board: BoardMetadata,
    ) -> dict[int, tuple[int, ...]]:
        """Build 0-based index adjacency list for orthogonal (4-connected) grid edges inside `cells`."""
        coords = [board.get_character(cid).coord for cid in cells]
        adj: dict[int, list[int]] = {i: [] for i in range(len(cells))}
        for i in range(len(cells)):
            for j in range(i + 1, len(cells)):
                dist = abs(coords[i].row - coords[j].row) + abs(
                    coords[i].col_idx - coords[j].col_idx
                )
                if dist == 1:
                    adj[i].append(j)
                    adj[j].append(i)
        return {i: tuple(neighbors) for i, neighbors in adj.items()}

    @classmethod
    def referenced_cells(cls, clue: Clue, board: BoardMetadata) -> dict[str, list[str]]:
        """Return highlighted cell groups referenced/counted by `clue` (for GUI Section 4.1).

        Returns:
            {"primary": [...], "secondary": [...]}
        """
        ct = clue.clue_type
        if ct == ClueType.FACT and clue.target:
            return {"primary": [board.resolve_cell_id(clue.target)], "secondary": []}

        if ct in (ClueType.SAME, ClueType.DIFFERENT) and clue.target1 and clue.target2:
            c1 = board.resolve_cell_id(clue.target1)
            c2 = board.resolve_cell_id(clue.target2)
            ordered = [cid for cid in board.cell_ids if cid in {c1, c2}]
            return {"primary": ordered, "secondary": []}

        if ct in (
            ClueType.EXACTLY,
            ClueType.NO,
            ClueType.AT_LEAST,
            ClueType.AT_MOST,
            ClueType.PARITY,
            ClueType.CONNECTED,
        ):
            if clue.region is None:
                return {"primary": [], "secondary": []}
            return {"primary": list(cls.resolve(clue.region, board)), "secondary": []}

        if ct in (ClueType.MORE_CRIMINALS, ClueType.EQUAL_CRIMINALS):
            p = list(cls.resolve(clue.region, board)) if clue.region else []
            s = list(cls.resolve(clue.region2, board)) if clue.region2 else []
            return {"primary": p, "secondary": s}

        if ct == ClueType.COMPOUND and clue.sub_clues:
            g0 = cls.referenced_cells(clue.sub_clues[0], board)
            prim_set = set(g0["primary"]) | set(g0["secondary"])
            sec_set: set[str] = set()
            for sc in clue.sub_clues[1:]:
                gi = cls.referenced_cells(sc, board)
                sec_set |= set(gi["primary"]) | set(gi["secondary"])
            sec_set -= prim_set
            return {
                "primary": [cid for cid in board.cell_ids if cid in prim_set],
                "secondary": [cid for cid in board.cell_ids if cid in sec_set],
            }

        return {"primary": [], "secondary": []}
