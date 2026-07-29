"""Document-level and master inverted-index construction."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from storage import delete_file, load_pickle, save_pickle
from utils import preprocess_with_positions, safe_filename

DocumentIndex = dict[str, Any]
MasterIndex = dict[str, set[tuple[str, int, int]]]
GUTENBERG_START = "*** start of the project gutenberg ebook"
GUTENBERG_END = "*** end of the project gutenberg ebook"


def _searchable_line_numbers(lines: list[str]) -> list[int]:
    """Return body-line numbers for Gutenberg files, otherwise all line numbers."""
    start = next((i for i, line in enumerate(lines) if GUTENBERG_START in line.casefold()), None)
    end = next((i for i, line in enumerate(lines) if GUTENBERG_END in line.casefold()), None)
    if start is not None and end is not None and start < end:
        return list(range(start + 2, end + 1))  # 1-based original line numbers
    return list(range(1, len(lines) + 1))


def index_document(path: str | Path, document_name: str) -> DocumentIndex:
    """Index one UTF-8 document while retaining original line positions."""
    source = Path(path)
    lines = source.read_text(encoding="utf-8").splitlines()
    inverted: defaultdict[str, set[tuple[int, int]]] = defaultdict(set)
    counts: Counter[str] = Counter()
    searchable_lines = _searchable_line_numbers(lines)

    for line_number in searchable_lines:
        for word, position in preprocess_with_positions(lines[line_number - 1]):
            inverted[word].add((line_number, position))
            counts[word] += 1

    stat = source.stat()
    return {
        "version": 2,
        "filename": document_name,
        "lines": lines,
        "line_numbers": searchable_lines,
        "index": dict(inverted),
        "counter": dict(counts),
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
    }


def document_index_path(index_directory: str | Path, document_name: str) -> Path:
    """Return the collision-safe path for a document index."""
    return Path(index_directory) / safe_filename(document_name)


def save_document_index(document: DocumentIndex, index_directory: str | Path) -> None:
    """Store a document index and remove legacy duplicates for that document."""
    directory = Path(index_directory)
    destination = document_index_path(directory, document["filename"])
    for existing in directory.glob("*.pkl") if directory.exists() else ():
        if existing == destination:
            continue
        old_document = load_pickle(existing)
        if isinstance(old_document, dict) and old_document.get("filename") == document["filename"]:
            delete_file(existing)
    save_pickle(destination, document)


def remove_document_index(document_name: str, index_directory: str | Path) -> None:
    """Remove every stored index belonging to *document_name*."""
    directory = Path(index_directory)
    for candidate in directory.glob("*.pkl") if directory.exists() else ():
        document = load_pickle(candidate)
        if isinstance(document, dict) and document.get("filename") == document_name:
            delete_file(candidate)


def load_document_indexes(index_directory: str | Path) -> dict[str, DocumentIndex]:
    """Load valid per-document indexes keyed by logical document name."""
    documents: dict[str, DocumentIndex] = {}
    directory = Path(index_directory)
    if not directory.exists():
        return documents
    for path in directory.glob("*.pkl"):
        document = load_pickle(path)
        if isinstance(document, dict) and document.get("version") == 2 and "filename" in document:
            documents[document["filename"]] = document
    return documents


def rebuild_master_index(index_directory: str | Path) -> MasterIndex:
    """Merge document indexes into ``word -> (file, line, position)`` entries."""
    master: defaultdict[str, set[tuple[str, int, int]]] = defaultdict(set)
    for filename, document in load_document_indexes(index_directory).items():
        for word, positions in document["index"].items():
            master[word].update((filename, line, position) for line, position in positions)
    return dict(master)
