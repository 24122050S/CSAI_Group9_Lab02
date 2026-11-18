"""Core enumerations for the Griductive Solver system."""

from enum import Enum


class Status(str, Enum):
    """Character status in Griductive."""

    CRIMINAL = "CRIMINAL"
    INNOCENT = "INNOCENT"
    UNKNOWN = "UNKNOWN"


class VerdictStatus(str, Enum):
    """Outcome of submitting a verdict to the GameEngine (Section 2.2 & 4.1)."""

    ACCEPTED = "ACCEPTED"
    NOT_PROVABLE = "NOT_PROVABLE"
    CONTRADICTED = "CONTRADICTED"
    ALREADY_REVEALED = "ALREADY_REVEALED"
    INCONSISTENT_KB = "INCONSISTENT_KB"


class AgentTerminalState(str, Enum):
    """Terminal or active state of the Deductive Logic Agent (Section 4.4)."""

    IN_PROGRESS = "IN_PROGRESS"
    SOLVED = "SOLVED"
    STUCK = "STUCK"  # Remaining unresolved cells are all UNKNOWN (ambiguous)
    INCONSISTENT = "INCONSISTENT"  # Current KB_t is UNSAT


class RegionType(str, Enum):
    """Supported clue region types (4 required core types + Extension 1 advanced regions)."""

    # --- Required Core Regions (Section 2.1 & 3.2) ---
    ROW = "ROW"
    COL = "COL"
    NEIGHBORS = "NEIGHBORS"
    CELL_LIST = "CELL_LIST"

    # --- Extension 1: Advanced Region Expressions (Section 3.2) ---
    INTERSECTION = "INTERSECTION"
    COMMON_NEIGHBORS = "COMMON_NEIGHBORS"
    CORNERS = "CORNERS"
    BOUNDARY = "BOUNDARY"
    BETWEEN = "BETWEEN"
    DIRECTIONAL = "DIRECTIONAL"
    PROFESSION = "PROFESSION"


class Direction(str, Enum):
    """Orthogonal ray directions from a reference cell (used by DIRECTIONAL region)."""

    LEFT = "LEFT"
    RIGHT = "RIGHT"
    ABOVE = "ABOVE"
    BELOW = "BELOW"


class ClueType(str, Enum):
    """Supported structured clue templates (6 core templates + Extensions 2 & 3)."""

    # --- 6 Required Core Templates (Section 3.2, Table 1) ---
    FACT = "FACT"
    SAME = "SAME"
    DIFFERENT = "DIFFERENT"
    EXACTLY = "EXACTLY"
    AT_LEAST = "AT_LEAST"
    AT_MOST = "AT_MOST"
    NO = "NO"  # Alias rendered as EXACTLY(0, region) per Section 3.2

    # --- Extension 2: Regional Count Comparison (Section 3.2) ---
    MORE_CRIMINALS = "MORE_CRIMINALS"
    EQUAL_CRIMINALS = "EQUAL_CRIMINALS"

    # --- Extension 3: Parity Constraint (Section 3.2) ---
    PARITY = "PARITY"

    # --- Extension 4: Compound Clues (Section 3.2 & Figure 1 A5) ---
    COMPOUND = "COMPOUND"

    # --- Extension 5: Orthogonal Connectivity Constraint (Section 3.2 & Figure 1 D5) ---
    CONNECTED = "CONNECTED"


class CompoundOperator(str, Enum):
    """Logical connectives for Extension 4 compound clues."""

    AND = "AND"
    OR = "OR"
    IMPLIES = "IMPLIES"


class ParityKind(str, Enum):
    """Parity constraint types for Extension 3."""

    ODD = "ODD"
    EVEN = "EVEN"


class EncodingMode(str, Enum):
    """Cardinality CNF encoding mode (Section 3.3 & 4.5 comparisons)."""

    COMBINATORIAL = "COMBINATORIAL"  # Direct subset encoding (0 auxiliary variables)
    SEQUENTIAL = "SEQUENTIAL"  # Sinz (2005) sequential counter (uses auxiliary variables)
