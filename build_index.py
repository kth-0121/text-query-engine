"""Incrementally synchronize indexes for the project's documents directory."""

from __future__ import annotations

from pathlib import Path

from indexer import document_index_path, index_document, rebuild_master_index, remove_document_index, save_document_index
from storage import ensure_directory, load_metadata, load_pickle, save_metadata, save_pickle

DOCUMENTS_DIR = Path("documents")
INDEX_DIR = Path("index")
FILE_INDEX_DIR = INDEX_DIR / "files"
METADATA_PATH = INDEX_DIR / "metadata.pkl"
MASTER_INDEX_PATH = INDEX_DIR / "master.pkl"
INDEX_VERSION = 2


def discover_documents(documents_dir: str | Path) -> dict[str, Path]:
    """Find all text documents recursively, using paths relative to the root."""
    root = Path(documents_dir)
    ensure_directory(root)
    return {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.casefold() == ".txt"
    }


def _fingerprint(path: Path) -> dict[str, int]:
    stat = path.stat()
    return {"mtime_ns": stat.st_mtime_ns, "size": stat.st_size, "index_version": INDEX_VERSION}


def build_index(documents_dir: str | Path = DOCUMENTS_DIR, index_dir: str | Path = INDEX_DIR) -> dict[str, int]:
    """Index only new/changed files and return a summary of performed actions."""
    index_root = Path(index_dir)
    file_index_dir = index_root / "files"
    metadata_path = index_root / "metadata.pkl"
    master_path = index_root / "master.pkl"
    ensure_directory(file_index_dir)
    documents = discover_documents(documents_dir)
    metadata = load_metadata(metadata_path)
    updated_metadata: dict[str, dict[str, int]] = {}
    summary = {"new": 0, "updated": 0, "skipped": 0, "deleted": 0, "failed": 0}
    changed = not isinstance(load_pickle(master_path), dict)

    for name in sorted(documents, key=str.casefold):
        path = documents[name]
        fingerprint = _fingerprint(path)
        previous = metadata.get(name)
        cached_document = load_pickle(document_index_path(file_index_dir, name))
        index_is_usable = isinstance(cached_document, dict) and cached_document.get("version") == INDEX_VERSION
        if previous == fingerprint and index_is_usable:
            print(f"[SKIP] {name}")
            updated_metadata[name] = fingerprint
            summary["skipped"] += 1
            continue
        try:
            save_document_index(index_document(path, name), file_index_dir)
        except (OSError, UnicodeError) as error:
            print(f"[ERROR] {name}: {error}")
            summary["failed"] += 1
            if previous:
                updated_metadata[name] = previous
            continue
        action = "[NEW]" if previous is None else "[UPDATE]"
        print(f"{action} {name}")
        summary["new" if previous is None else "updated"] += 1
        updated_metadata[name] = fingerprint
        changed = True

    for name in sorted(set(metadata) - set(documents), key=str.casefold):
        remove_document_index(name, file_index_dir)
        print(f"[DELETE] {name}")
        summary["deleted"] += 1
        changed = True

    if changed:
        save_pickle(master_path, rebuild_master_index(file_index_dir))
        print("Index build completed.")
    else:
        print("Index is up-to-date.")
    save_metadata(metadata_path, updated_metadata)
    return summary


def main() -> None:
    """Build or refresh the default ``documents/`` index from the command line."""
    build_index()


if __name__ == "__main__":
    main()
