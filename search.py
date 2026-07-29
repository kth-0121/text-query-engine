"""Interactive user interface and presentation for text-query results."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from evaluator import EvaluationResult, QueryEvaluator
from indexer import load_document_indexes
from parser import QueryNode, parse_query
from storage import load_pickle

INDEX_DIR = Path("index")
MASTER_PATH = INDEX_DIR / "master.pkl"
FILE_INDEX_DIR = INDEX_DIR / "files"


def _walk_words(expression: QueryNode, words: list[str]) -> None:
    if expression[0] == "WORD":
        if expression[1] not in words:
            words.append(expression[1])
    elif expression[0] == "NOT":
        _walk_words(expression[1], words)
    else:
        _walk_words(expression[1], words)
        _walk_words(expression[2], words)


def _phrase_alternatives(expression: QueryNode) -> list[tuple[str, QueryNode]]:
    """Expand OR branches to report each exact adjacent phrase occurrence."""
    if expression[0] == "WORD":
        return [(str(expression[1]), expression)]
    if expression[0] == "OR":
        return _phrase_alternatives(expression[1]) + _phrase_alternatives(expression[2])
    if expression[0] == "AND":
        return [
            (f"{left_label} && {right_label}", ("AND", left, right))
            for left_label, left in _phrase_alternatives(expression[1])
            for right_label, right in _phrase_alternatives(expression[2])
        ]
    return []


def _walk_phrase_nodes(expression: QueryNode, nodes: list[QueryNode]) -> None:
    if expression[0] == "NOT":
        _walk_phrase_nodes(expression[1], nodes)
    elif expression[0] in {"AND", "OR"}:
        _walk_phrase_nodes(expression[1], nodes)
        _walk_phrase_nodes(expression[2], nodes)
        if expression[0] == "AND":
            nodes.append(expression)


def print_statistics(expression: QueryNode, evaluator: QueryEvaluator) -> None:
    """Show individual-word and exact-adjacent-phrase occurrence counts."""
    words: list[str] = []
    _walk_words(expression, words)
    for word in words:
        count = len(evaluator.master_index.get(word, set()))
        print(f"{word}: {count} {'occurrence' if count == 1 else 'occurrences'}")

    phrases: list[QueryNode] = []
    _walk_phrase_nodes(expression, phrases)
    shown: set[str] = set()
    for phrase in phrases:
        for label, alternative in _phrase_alternatives(phrase):
            if label not in shown:
                shown.add(label)
                count = evaluator.evaluate(alternative).occurrence_count
                print(f"{label}: {count} {'occurrence' if count == 1 else 'occurrences'}")


def print_results(result: EvaluationResult, documents: dict[str, dict[str, Any]]) -> None:
    """Print each matching original line once, ordered by file then line number."""
    for filename, line_number in sorted(result.lines, key=lambda item: (item[0].casefold(), item[1])):
        document = documents[filename]
        lines = document["lines"]
        if 1 <= line_number <= len(lines):
            print(f"({line_number}) {filename}: {lines[line_number - 1]}")


def main() -> None:
    """Start the interactive Boolean query loop."""
    master = load_pickle(MASTER_PATH, {})
    documents = load_document_indexes(FILE_INDEX_DIR)
    if not isinstance(master, dict) or not documents:
        print("No usable index found. Please run main.py to build the index first.")
        return
    evaluator = QueryEvaluator(master, documents)

    while True:
        print("\nEnter a Boolean query.")
        query = input("To quit, enter '.' => ").strip()
        if query == ".":
            print("Ok, bye!")
            return
        if not query:
            print("Please enter a query.")
            continue
        try:
            expression = parse_query(query)
            result = evaluator.evaluate(expression)
        except ValueError as error:
            print(f"Invalid query: {error}")
            continue

        print()
        print_statistics(expression, evaluator)
        if not result.lines:
            print(f"No results found for: {query}")
            continue
        print(f"\nFound {len(result.lines)} matching line(s).")
        if input("Display matching lines? (Y/n) => ").strip().casefold() not in {"n", "no"}:
            print_results(result, documents)
