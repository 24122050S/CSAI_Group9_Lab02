"""Logical representation, validation, evaluation, and CNF encoding package."""

from logic.cnf_encoder import Clause, CNFEncoder, CNFFormula, EncodedKnowledgeBase
from logic.evaluator import SemanticEvaluator
from logic.regions import RegionResolver
from logic.validator import ClueValidationError, ClueValidator
from logic.variables import VariableManager

__all__ = [
    "CNFEncoder",
    "CNFFormula",
    "Clause",
    "ClueValidationError",
    "ClueValidator",
    "EncodedKnowledgeBase",
    "RegionResolver",
    "SemanticEvaluator",
    "VariableManager",
]
