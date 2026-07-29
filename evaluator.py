"""Evaluate Boolean query ASTs against an inverted index."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from parser import QueryNode

LineKey = tuple[str, int]
Span = tuple[str, int, int, int]  # filename, line, first token position, last position


@dataclass
class EvaluationResult:
    """Logical matching lines and concrete word/phrase occurrences."""
    lines: set[LineKey] = field(default_factory=set)
    spans: set[Span] = field(default_factory=set)

    @property
    def occurrence_count(self) -> int:
        """Count concrete word/phrase occurrences (not duplicate output lines)."""
        return len(self.spans)


class QueryEvaluator:
    """Evaluate words, phrases, OR, and NOT without scanning document text."""

    def __init__(self, master_index: dict[str, set[tuple[str, int, int]]], documents: dict[str, dict[str, Any]]) -> None:
        self.master_index = master_index
        self.all_lines: set[LineKey] = {
            (filename, line_number)
            for filename, document in documents.items()
            for line_number in document.get("line_numbers", range(1, len(document.get("lines", [])) + 1))
        }

    def evaluate(self, expression: QueryNode) -> EvaluationResult:
        """Evaluate a parsed expression."""
        operator = expression[0]
        if operator == "WORD":
            return self._word_result(expression[1])
        if operator == "NOT":
            child = self.evaluate(expression[1])
            return EvaluationResult(lines=self.all_lines - child.lines)
        if operator == "OR":
            left, right = self.evaluate(expression[1]), self.evaluate(expression[2])
            return EvaluationResult(lines=left.lines | right.lines, spans=left.spans | right.spans)
        if operator == "AND":
            return self._evaluate_and(expression)
        raise ValueError(f"Unknown query operator: {operator}")

    def _word_result(self, word: object) -> EvaluationResult:
        spans = {(filename, line, position, position) for filename, line, position in self.master_index.get(str(word), set())}
        return EvaluationResult(lines={(filename, line) for filename, line, _, _ in spans}, spans=spans)

    def _evaluate_and(self, expression: QueryNode) -> EvaluationResult:
        left_expression, right_expression = expression[1], expression[2]
        left, right = self.evaluate(left_expression), self.evaluate(right_expression)

        # NOT has no text span to be adjacent to.  When it is used with &&,
        # retain conventional Boolean line intersection rather than inventing
        # a position for a missing word.
        if self._contains_not(left_expression) or self._contains_not(right_expression):
            shared = left.lines & right.lines
            return EvaluationResult(lines=shared, spans={span for span in left.spans | right.spans if span[:2] in shared})

        right_starts = {(filename, line, start): end for filename, line, start, end in right.spans}
        spans = {
            (filename, line, start, right_starts[(filename, line, end + 1)])
            for filename, line, start, end in left.spans
            if (filename, line, end + 1) in right_starts
        }
        return EvaluationResult(lines={(filename, line) for filename, line, _, _ in spans}, spans=spans)

    @staticmethod
    def _contains_not(expression: QueryNode) -> bool:
        if expression[0] == "NOT":
            return True
        return expression[0] in {"AND", "OR"} and (
            QueryEvaluator._contains_not(expression[1]) or QueryEvaluator._contains_not(expression[2])
        )
