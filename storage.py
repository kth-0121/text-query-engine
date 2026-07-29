"""Persistent storage helpers for the text query index."""

from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any


def ensure_directory(directory: str | Path) -> None:
    """Create *directory* and its parents when they do not exist."""
    Path(directory).mkdir(parents=True, exist_ok=True)


def save_pickle(path: str | Path, data: Any) -> None:
    """Atomically save a Python value as a pickle file."""
    destination = Path(path)
    ensure_directory(destination.parent)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with temporary.open("wb") as file:
        pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(temporary, destination)


def load_pickle(path: str | Path, default: Any = None) -> Any:
    """Load a pickle value, returning *default* if it is absent or invalid."""
    try:
        with Path(path).open("rb") as file:
            return pickle.load(file)
    except (FileNotFoundError, EOFError, OSError, pickle.UnpicklingError):
        return default


def delete_file(path: str | Path) -> None:
    """Delete an index file if it exists."""
    try:
        Path(path).unlink()
    except FileNotFoundError:
        pass


def load_metadata(path: str | Path) -> dict[str, dict[str, int]]:
    """Load document metadata, accepting only the expected dictionary form."""
    value = load_pickle(path, {})
    return value if isinstance(value, dict) else {}


def save_metadata(path: str | Path, metadata: dict[str, dict[str, int]]) -> None:
    """Save document metadata."""
    save_pickle(path, metadata)
