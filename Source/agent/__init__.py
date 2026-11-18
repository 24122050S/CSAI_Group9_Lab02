"""Deductive Logic Agent, Hint Engine, Trace, and Uniqueness Checker package."""

from agent.deductive_agent import DeductiveLogicAgent, PublicEngineProtocol
from agent.hint import HintEngine, HintResult
from agent.trace import AgentSolveReport, DeductionStepTrace, SATQueryRecord
from agent.uniqueness import UniquenessChecker, UniquenessReport

__all__ = [
    "AgentSolveReport",
    "DeductiveLogicAgent",
    "DeductionStepTrace",
    "HintEngine",
    "HintResult",
    "PublicEngineProtocol",
    "SATQueryRecord",
    "UniquenessChecker",
    "UniquenessReport",
]
