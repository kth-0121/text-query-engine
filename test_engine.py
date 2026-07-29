"""Self-contained regression tests for the Text Query Engine."""

from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from build_index import build_index
from evaluator import QueryEvaluator
from indexer import load_document_indexes
from parser import parse_query
from search import print_results
from storage import load_pickle


class TextQueryEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.documents = root / "documents"
        self.index = root / "index"
        self.documents.mkdir()
        (self.documents / "people.txt").write_text(
            "Abe Lincoln spoke.\n"
            "Abraham Lincoln replied.\n"
            "Abe was called Lincoln.\n"
            "Lincoln Lincoln Lincoln.\n",
            encoding="utf-8",
        )
        (self.documents / "korean.txt").write_text("대한민국 헌법\n대한민국 국민\n", encoding="utf-8")
        (self.documents / "gutenberg.txt").write_text(
            "header Lincoln\n*** START OF THE PROJECT GUTENBERG EBOOK SAMPLE ***\n"
            "Abe Lincoln body\n*** END OF THE PROJECT GUTENBERG EBOOK SAMPLE ***\nfooter Lincoln\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def evaluator(self) -> QueryEvaluator:
        return QueryEvaluator(load_pickle(self.index / "master.pkl", {}), load_document_indexes(self.index / "files"))

    def test_boolean_queries_occurrences_and_gutenberg_range(self) -> None:
        first = build_index(self.documents, self.index)
        self.assertEqual(first["new"], 3)
        evaluator = self.evaluator()
        self.assertEqual(evaluator.evaluate(parse_query("Lincoln")).occurrence_count, 7)
        self.assertEqual(evaluator.evaluate(parse_query("Abe && Lincoln")).occurrence_count, 2)
        self.assertEqual(evaluator.evaluate(parse_query("(Abe || Abraham) && Lincoln")).occurrence_count, 3)
        self.assertIn(("people.txt", 3), evaluator.evaluate(parse_query("Abe || Abraham && Lincoln")).lines)
        self.assertNotIn(("people.txt", 3), evaluator.evaluate(parse_query("Abe && Lincoln")).lines)
        self.assertEqual(evaluator.evaluate(parse_query("! Lincoln")).lines, {("korean.txt", 1), ("korean.txt", 2)})
        self.assertEqual(evaluator.evaluate(parse_query("대한민국 && 헌법")).lines, {("korean.txt", 1)})

    def test_incremental_indexing_change_and_delete(self) -> None:
        build_index(self.documents, self.index)
        second = build_index(self.documents, self.index)
        self.assertEqual(second["skipped"], 3)
        people = self.documents / "people.txt"
        people.write_text(people.read_text(encoding="utf-8") + "Abraham Lincoln again.\n", encoding="utf-8")
        changed = build_index(self.documents, self.index)
        self.assertEqual(changed["updated"], 1)
        (self.documents / "korean.txt").unlink()
        deleted = build_index(self.documents, self.index)
        self.assertEqual(deleted["deleted"], 1)
        self.assertNotIn("korean.txt", load_document_indexes(self.index / "files"))

    def test_duplicate_lines_sorting_and_invalid_queries(self) -> None:
        build_index(self.documents, self.index)
        evaluator = self.evaluator()
        result = evaluator.evaluate(parse_query("Lincoln || Abraham"))
        output = StringIO()
        with redirect_stdout(output):
            print_results(result, load_document_indexes(self.index / "files"))
        printed = [line for line in output.getvalue().splitlines() if line]
        self.assertEqual(len(printed), len(set(printed)))
        self.assertEqual(
            printed,
            [
                "(3) gutenberg.txt: Abe Lincoln body",
                "(1) people.txt: Abe Lincoln spoke.",
                "(2) people.txt: Abraham Lincoln replied.",
                "(3) people.txt: Abe was called Lincoln.",
                "(4) people.txt: Lincoln Lincoln Lincoln.",
            ],
        )
        for query in ("", "( Lincoln", "Lincoln &&", "|| Lincoln"):
            with self.assertRaises(ValueError):
                parse_query(query)


if __name__ == "__main__":
    unittest.main(verbosity=2)
