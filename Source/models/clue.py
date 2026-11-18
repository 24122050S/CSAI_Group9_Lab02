"""Structured clue and region specifications (Section 2.1 & 3.2)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from models.board import BoardMetadata
from models.enums import ClueType, CompoundOperator, Direction, ParityKind, RegionType, Status

PROFESSION_VI_MAP: dict[str, str] = {
    "astronaut": "Phi hành gia",
    "clerk": "Thư ký",
    "cook": "Đầu bếp",
    "detective": "Thám tử",
    "farmer": "Nông dân",
    "guard": "Bảo vệ",
    "painter": "Họa sĩ",
    "citizen": "Cư dân",
}


def translate_profession_vi(prof: str) -> str:
    cleaned = prof.strip()
    if not cleaned:
        return "Cư dân"
    return PROFESSION_VI_MAP.get(cleaned.lower(), cleaned)


@dataclass(frozen=True)
class RegionSpec:
    """Structured specification of a board region (4 core types + Extension 1)."""

    region_type: RegionType
    row: int | None = None
    col: str | None = None
    target: str | None = None
    target2: str | None = None
    direction: Direction | None = None
    cells: tuple[str, ...] = ()
    profession: str | None = None
    sub_regions: tuple[RegionSpec, ...] = ()

    # --- Convenient Factory Constructors ---
    @classmethod
    def row_region(cls, row: int) -> RegionSpec:
        return cls(region_type=RegionType.ROW, row=row)

    @classmethod
    def col_region(cls, col: str) -> RegionSpec:
        return cls(region_type=RegionType.COL, col=col.strip().upper())

    @classmethod
    def neighbors(cls, target: str) -> RegionSpec:
        return cls(region_type=RegionType.NEIGHBORS, target=target.strip())

    @classmethod
    def cell_list(cls, cells: Iterable[str]) -> RegionSpec:
        return cls(region_type=RegionType.CELL_LIST, cells=tuple(c.strip() for c in cells))

    @classmethod
    def intersection(cls, r1: RegionSpec, r2: RegionSpec) -> RegionSpec:
        return cls(region_type=RegionType.INTERSECTION, sub_regions=(r1, r2))

    @classmethod
    def common_neighbors(cls, target1: str, target2: str) -> RegionSpec:
        return cls(
            region_type=RegionType.COMMON_NEIGHBORS,
            target=target1.strip(),
            target2=target2.strip(),
        )

    @classmethod
    def corners(cls) -> RegionSpec:
        return cls(region_type=RegionType.CORNERS)

    @classmethod
    def boundary(cls) -> RegionSpec:
        return cls(region_type=RegionType.BOUNDARY)

    @classmethod
    def between(cls, target1: str, target2: str) -> RegionSpec:
        return cls(
            region_type=RegionType.BETWEEN,
            target=target1.strip(),
            target2=target2.strip(),
        )

    @classmethod
    def directional(cls, target: str, direction: Direction | str) -> RegionSpec:
        dir_enum = direction if isinstance(direction, Direction) else Direction(direction.upper())
        return cls(region_type=RegionType.DIRECTIONAL, target=target.strip(), direction=dir_enum)

    @classmethod
    def by_profession(cls, profession: str) -> RegionSpec:
        return cls(region_type=RegionType.PROFESSION, profession=profession.strip())

    def describe(self, board: BoardMetadata | None = None) -> str:
        """Render a concise human-readable phrase for the region."""

        def _fmt_ref(ref: str | None) -> str:
            if not ref:
                return "?"
            if board is None:
                return ref
            try:
                ch = board.get_character(ref)
                return f"{ch.name} ({ch.cell_id})"
            except KeyError:
                return ref

        rt = self.region_type
        if rt == RegionType.ROW:
            return f"row {self.row}"
        if rt == RegionType.COL:
            return f"column {self.col}"
        if rt == RegionType.NEIGHBORS:
            return f"the neighbors of {_fmt_ref(self.target)}"
        if rt == RegionType.CELL_LIST:
            items = [_fmt_ref(c) for c in self.cells]
            return "{" + ", ".join(items) + "}"
        if rt == RegionType.INTERSECTION:
            parts = [sr.describe(board) for sr in self.sub_regions]
            return " ∩ ".join(parts)
        if rt == RegionType.COMMON_NEIGHBORS:
            return f"common neighbors of {_fmt_ref(self.target)} and {_fmt_ref(self.target2)}"
        if rt == RegionType.CORNERS:
            return "the four corners"
        if rt == RegionType.BOUNDARY:
            return "the board boundary"
        if rt == RegionType.BETWEEN:
            return f"cells between {_fmt_ref(self.target)} and {_fmt_ref(self.target2)}"
        if rt == RegionType.DIRECTIONAL:
            dir_map = {
                Direction.LEFT: "to the left of",
                Direction.RIGHT: "to the right of",
                Direction.ABOVE: "above",
                Direction.BELOW: "below",
            }
            phrase = dir_map.get(self.direction, str(self.direction))
            return f"cells {phrase} {_fmt_ref(self.target)}"
        if rt == RegionType.PROFESSION:
            return f"all {self.profession}s"
        return rt.value

    def describe_vi(self, board: BoardMetadata | None = None) -> str:
        """Render natural, easy-to-read Vietnamese description for the region."""

        def _fmt_ref(ref: str | None) -> str:
            if not ref:
                return "?"
            if board is None:
                return ref
            try:
                ch = board.get_character(ref)
                return f"{ch.name} ({ch.cell_id})"
            except KeyError:
                return ref

        rt = self.region_type
        if rt == RegionType.ROW:
            return f"hàng {self.row}"
        if rt == RegionType.COL:
            return f"cột {self.col}"
        if rt == RegionType.NEIGHBORS:
            return f"các ô xung quanh {_fmt_ref(self.target)}"
        if rt == RegionType.CELL_LIST:
            items = [_fmt_ref(c) for c in self.cells]
            return "nhóm {" + ", ".join(items) + "}"
        if rt == RegionType.INTERSECTION:
            if (
                len(self.sub_regions) == 2
                and self.sub_regions[0].region_type == RegionType.NEIGHBORS
                and self.sub_regions[1].region_type in (RegionType.COL, RegionType.ROW)
            ):
                return f"{self.sub_regions[0].describe_vi(board)} thuộc {self.sub_regions[1].describe_vi(board)}"
            parts = [sr.describe_vi(board) for sr in self.sub_regions]
            return "phần giao (" + " ∩ ".join(parts) + ")"
        if rt == RegionType.COMMON_NEIGHBORS:
            return f"các ô kề chung của {_fmt_ref(self.target)} và {_fmt_ref(self.target2)}"
        if rt == RegionType.CORNERS:
            return "4 ô góc bàn cờ"
        if rt == RegionType.BOUNDARY:
            return "viền ngoài bàn cờ"
        if rt == RegionType.BETWEEN:
            return f"các ô nằm giữa {_fmt_ref(self.target)} và {_fmt_ref(self.target2)}"
        if rt == RegionType.DIRECTIONAL:
            dir_map = {
                Direction.LEFT: "bên trái",
                Direction.RIGHT: "bên phải",
                Direction.ABOVE: "phía trên",
                Direction.BELOW: "phía dưới",
            }
            phrase = dir_map.get(self.direction, str(self.direction))
            return f"các ô {phrase} {_fmt_ref(self.target)}"
        if rt == RegionType.PROFESSION:
            job_vi = translate_profession_vi(self.profession or "")
            return f"những người làm nghề {job_vi}"
        return rt.value

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"type": self.region_type.value}
        if self.row is not None:
            data["row"] = self.row
        if self.col is not None:
            data["col"] = self.col
        if self.target is not None:
            data["target"] = self.target
        if self.target2 is not None:
            data["target2"] = self.target2
        if self.direction is not None:
            data["direction"] = self.direction.value
        if self.cells:
            data["cells"] = list(self.cells)
        if self.profession is not None:
            data["profession"] = self.profession
        if self.sub_regions:
            data["sub_regions"] = [sr.to_dict() for sr in self.sub_regions]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegionSpec:
        rt = RegionType(data["type"].strip().upper())
        direction = (
            Direction(data["direction"].strip().upper())
            if data.get("direction") is not None
            else None
        )
        cells = tuple(str(c).strip() for c in data.get("cells", []))
        sub_regions = tuple(cls.from_dict(sr) for sr in data.get("sub_regions", []))
        return cls(
            region_type=rt,
            row=int(data["row"]) if data.get("row") is not None else None,
            col=str(data["col"]).strip().upper() if data.get("col") is not None else None,
            target=str(data["target"]).strip() if data.get("target") is not None else None,
            target2=str(data["target2"]).strip() if data.get("target2") is not None else None,
            direction=direction,
            cells=cells,
            profession=str(data["profession"]).strip()
            if data.get("profession") is not None
            else None,
            sub_regions=sub_regions,
        )


@dataclass(frozen=True)
class Clue:
    """Immutable structured clue attached to a card (Section 3.2)."""

    clue_id: str
    owner_cell: str
    clue_type: ClueType
    text: str = ""
    # FACT parameters
    target: str | None = None
    status: Status | None = None
    # SAME / DIFFERENT parameters
    target1: str | None = None
    target2: str | None = None
    # Counting / Parity / Comparison / Connected parameters
    count: int | None = None
    region: RegionSpec | None = None
    region2: RegionSpec | None = None
    parity: ParityKind | None = None
    target_status: Status = Status.CRIMINAL
    # Compound parameters (Extension 4)
    operator: CompoundOperator | None = None
    sub_clues: tuple[Clue, ...] = ()

    @classmethod
    def compound(
        cls,
        clue_id: str,
        owner_cell: str,
        operator: CompoundOperator | str,
        sub_clues: Iterable[Clue],
        text: str = "",
    ) -> Clue:
        op_enum = (
            operator
            if isinstance(operator, CompoundOperator)
            else CompoundOperator(str(operator).strip().upper())
        )
        return cls(
            clue_id=clue_id,
            owner_cell=owner_cell,
            clue_type=ClueType.COMPOUND,
            operator=op_enum,
            sub_clues=tuple(sub_clues),
            text=text,
        )

    @classmethod
    def connected(
        cls,
        clue_id: str,
        owner_cell: str,
        region: RegionSpec,
        target_status: Status = Status.CRIMINAL,
        text: str = "",
    ) -> Clue:
        return cls(
            clue_id=clue_id,
            owner_cell=owner_cell,
            clue_type=ClueType.CONNECTED,
            region=region,
            target_status=target_status,
            text=text,
        )

    def effective_clue_type(self) -> ClueType:
        """Normalize NO(region) to EXACTLY(0, region) per Section 3.2."""
        if self.clue_type == ClueType.NO:
            return ClueType.EXACTLY
        return self.clue_type

    def effective_count(self) -> int | None:
        """Return 0 when ClueType.NO is used, otherwise self.count."""
        if self.clue_type == ClueType.NO:
            return 0
        return self.count

    def render_text(self, board: BoardMetadata | None = None) -> str:
        """Return explicit display text if set, else synthesize readable English."""
        if self.text.strip():
            return self.text.strip()

        def _name(ref: str | None) -> str:
            if not ref:
                return "?"
            if board is None:
                return ref
            try:
                return board.get_character(ref).name
            except KeyError:
                return ref

        role_plural = "criminals" if self.target_status == Status.CRIMINAL else "innocents"
        role_singular = "a Criminal" if self.target_status == Status.CRIMINAL else "Innocent"
        ct = self.clue_type

        if ct == ClueType.FACT:
            st_word = "a Criminal" if self.status == Status.CRIMINAL else "Innocent"
            return f"{_name(self.target)} is {st_word}."
        if ct == ClueType.SAME:
            return f"{_name(self.target1)} and {_name(self.target2)} have the same status."
        if ct == ClueType.DIFFERENT:
            return f"{_name(self.target1)} and {_name(self.target2)} have different statuses."
        if ct == ClueType.NO:
            reg_str = self.region.describe(board) if self.region else "?"
            return f"There are no {role_plural} in {reg_str}."
        if ct == ClueType.EXACTLY:
            reg_str = self.region.describe(board) if self.region else "?"
            if self.count == 0:
                return f"There are no {role_plural} in {reg_str}."
            if self.count == 1:
                return f"Exactly 1 person in {reg_str} is {role_singular}."
            return f"Exactly {self.count} people in {reg_str} are {role_plural}."
        if ct == ClueType.AT_LEAST:
            reg_str = self.region.describe(board) if self.region else "?"
            return f"At least {self.count} people in {reg_str} are {role_plural}."
        if ct == ClueType.AT_MOST:
            reg_str = self.region.describe(board) if self.region else "?"
            return f"At most {self.count} people in {reg_str} are {role_plural}."
        if ct == ClueType.MORE_CRIMINALS:
            r1 = self.region.describe(board) if self.region else "?"
            r2 = self.region2.describe(board) if self.region2 else "?"
            return f"There are more {role_plural} in {r1} than in {r2}."
        if ct == ClueType.EQUAL_CRIMINALS:
            r1 = self.region.describe(board) if self.region else "?"
            r2 = self.region2.describe(board) if self.region2 else "?"
            return f"{r1.capitalize()} and {r2} have the same number of {role_plural}."
        if ct == ClueType.PARITY:
            reg_str = self.region.describe(board) if self.region else "?"
            p_word = "an odd" if self.parity == ParityKind.ODD else "an even"
            return f"There is {p_word} number of {role_plural} in {reg_str}."
        if ct == ClueType.CONNECTED:
            reg_str = self.region.describe(board) if self.region else "?"
            return f"All {role_plural} in {reg_str} are orthogonally connected."
        if ct == ClueType.COMPOUND:
            parts = [sc.render_text(board).rstrip(".") for sc in self.sub_clues]
            if self.operator == CompoundOperator.AND:
                return " and ".join(parts) + "."
            if self.operator == CompoundOperator.OR:
                return "Either " + " or ".join(parts) + "."
            if self.operator == CompoundOperator.IMPLIES and len(parts) == 2:
                return f"If {parts[0][0].lower() + parts[0][1:]}, then {parts[1][0].lower() + parts[1][1:]}."
            return f" {self.operator.value if self.operator else 'AND'} ".join(parts) + "."
        return ct.value

    def render_text_vi(self, board: BoardMetadata | None = None) -> str:
        """Synthesize crystal-clear Vietnamese clue text directly from structured parameters."""

        def _name(ref: str | None) -> str:
            if not ref:
                return "?"
            if board is None:
                return ref
            try:
                ch = board.get_character(ref)
                return f"{ch.name} ({ch.cell_id})"
            except KeyError:
                return ref

        role_vi = "Tội phạm" if self.target_status == Status.CRIMINAL else "người Vô tội"
        ct = self.clue_type

        if ct == ClueType.FACT:
            st_vi = "Tội phạm" if self.status == Status.CRIMINAL else "người Vô tội"
            return f"{_name(self.target)} là {st_vi}."
        if ct == ClueType.SAME:
            return f"{_name(self.target1)} và {_name(self.target2)} cùng phe với nhau."
        if ct == ClueType.DIFFERENT:
            return f"{_name(self.target1)} và {_name(self.target2)} khác phe nhau."
        if ct == ClueType.NO:
            reg_vi = self.region.describe_vi(board) if self.region else "?"
            return f"Không có {role_vi} nào ở {reg_vi}."
        if ct == ClueType.EXACTLY:
            reg_vi = self.region.describe_vi(board) if self.region else "?"
            if self.count == 0:
                return f"Không có {role_vi} nào ở {reg_vi}."
            return f"Có đúng {self.count} {role_vi} ở {reg_vi}."
        if ct == ClueType.AT_LEAST:
            reg_vi = self.region.describe_vi(board) if self.region else "?"
            return f"Có ít nhất {self.count} {role_vi} ở {reg_vi}."
        if ct == ClueType.AT_MOST:
            reg_vi = self.region.describe_vi(board) if self.region else "?"
            return f"Có tối đa {self.count} {role_vi} ở {reg_vi}."
        if ct == ClueType.MORE_CRIMINALS:
            r1 = self.region.describe_vi(board) if self.region else "?"
            r2 = self.region2.describe_vi(board) if self.region2 else "?"
            return f"Số {role_vi} ở {r1} nhiều hơn ở {r2}."
        if ct == ClueType.EQUAL_CRIMINALS:
            r1 = self.region.describe_vi(board) if self.region else "?"
            r2 = self.region2.describe_vi(board) if self.region2 else "?"
            return f"Số {role_vi} ở {r1} bằng với ở {r2}."
        if ct == ClueType.PARITY:
            reg_vi = self.region.describe_vi(board) if self.region else "?"
            p_vi = "số lẻ" if self.parity == ParityKind.ODD else "số chẵn"
            return f"Số {role_vi} ở {reg_vi} là một {p_vi}."
        if ct == ClueType.CONNECTED:
            reg_vi = self.region.describe_vi(board) if self.region else "?"
            return f"Các {role_vi} ở {reg_vi} đứng liền kề nhau (liên thông cạnh)."
        if ct == ClueType.COMPOUND:
            parts = [sc.render_text_vi(board).rstrip(".") for sc in self.sub_clues]
            if self.operator == CompoundOperator.AND:
                lowered = [parts[0]] + [p[0].lower() + p[1:] if p else p for p in parts[1:]]
                return "; đồng thời ".join(lowered) + "."
            if self.operator == CompoundOperator.OR:
                lowered = [p[0].lower() + p[1:] if p else p for p in parts]
                return "Hoặc " + ", hoặc ".join(lowered) + "."
            if self.operator == CompoundOperator.IMPLIES and len(parts) == 2:
                p0 = parts[0][0].lower() + parts[0][1:] if parts[0] else ""
                p1 = parts[1][0].lower() + parts[1][1:] if parts[1] else ""
                return f"Nếu {p0}, thì {p1}."
            return " và ".join(parts) + "."
        return ct.value

    def to_dict(self, board: BoardMetadata | None = None) -> dict[str, Any]:
        data: dict[str, Any] = {
            "clue_id": self.clue_id,
            "owner_cell": self.owner_cell,
            "type": self.clue_type.value,
            "text": self.render_text(board),
            "text_vi": self.render_text_vi(board),
        }
        if self.target is not None:
            data["target"] = self.target
        if self.status is not None:
            data["status"] = self.status.value
        if self.target1 is not None:
            data["target1"] = self.target1
        if self.target2 is not None:
            data["target2"] = self.target2
        if self.count is not None:
            data["count"] = self.count
        if self.region is not None:
            data["region"] = self.region.to_dict()
        if self.region2 is not None:
            data["region2"] = self.region2.to_dict()
        if self.parity is not None:
            data["parity"] = self.parity.value
        if self.target_status != Status.CRIMINAL:
            data["target_status"] = self.target_status.value
        if self.operator is not None:
            data["operator"] = self.operator.value
        if self.sub_clues:
            data["sub_clues"] = [sc.to_dict(board) for sc in self.sub_clues]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any], default_owner: str = "") -> Clue:
        owner = str(data.get("owner_cell", default_owner)).strip().upper()
        clue_id = str(data.get("clue_id", f"clue_{owner}")).strip()
        ct = ClueType(str(data["type"]).strip().upper())
        status = Status(data["status"].strip().upper()) if data.get("status") else None
        target_status = (
            Status(data["target_status"].strip().upper())
            if data.get("target_status")
            else Status.CRIMINAL
        )
        parity = ParityKind(data["parity"].strip().upper()) if data.get("parity") else None
        operator = (
            CompoundOperator(data["operator"].strip().upper())
            if data.get("operator")
            else None
        )
        sub_clues = tuple(
            cls.from_dict(
                sc,
                default_owner=owner,
            )
            for sc in data.get("sub_clues", [])
        )
        region = RegionSpec.from_dict(data["region"]) if data.get("region") else None
        region2 = RegionSpec.from_dict(data["region2"]) if data.get("region2") else None
        count = int(data["count"]) if data.get("count") is not None else None
        if ct == ClueType.NO and count is None:
            count = 0
        return cls(
            clue_id=clue_id,
            owner_cell=owner,
            clue_type=ct,
            text=str(data.get("text", "")),
            target=str(data["target"]).strip() if data.get("target") is not None else None,
            status=status,
            target1=str(data["target1"]).strip() if data.get("target1") is not None else None,
            target2=str(data["target2"]).strip() if data.get("target2") is not None else None,
            count=count,
            region=region,
            region2=region2,
            parity=parity,
            target_status=target_status,
            operator=operator,
            sub_clues=sub_clues,
        )
