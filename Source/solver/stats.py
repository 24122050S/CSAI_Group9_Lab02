"""Performance and search statistics for the custom DPLL SAT Solver (Section 4.3 & 4.5)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SolverStats:
    """Mutable accumulator for DPLL search statistics."""

    decisions: int = 0
    propagations: int = 0
    backtracks: int = 0
    pure_eliminations: int = 0
    runtime_sec: float = 0.0

    @property
    def runtime_ms(self) -> float:
        return self.runtime_sec * 1000.0

    def merge(self, other: SolverStats) -> None:
        """Accumulate statistics from another DPLL run."""
        self.decisions += other.decisions
        self.propagations += other.propagations
        self.backtracks += other.backtracks
        self.pure_eliminations += other.pure_eliminations
        self.runtime_sec += other.runtime_sec

    def copy(self) -> SolverStats:
        return SolverStats(
            decisions=self.decisions,
            propagations=self.propagations,
            backtracks=self.backtracks,
            pure_eliminations=self.pure_eliminations,
            runtime_sec=self.runtime_sec,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "decisions": self.decisions,
            "propagations": self.propagations,
            "backtracks": self.backtracks,
            "pure_eliminations": self.pure_eliminations,
            "runtime_sec": round(self.runtime_sec, 6),
            "runtime_ms": round(self.runtime_ms, 3),
        }


@dataclass(frozen=True)
class DPLLResult:
    """Return value of a DPLL SAT call (Section 4.3)."""

    is_sat: bool
    assignment: dict[int, bool] | None
    stats: SolverStats

    def to_dict(self) -> dict[str, Any]:
        return {
            "result": "SAT" if self.is_sat else "UNSAT",
            "stats": self.stats.to_dict(),
        }
