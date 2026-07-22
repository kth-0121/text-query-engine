"""
storage.py

Utility functions for saving and loading index data.
"""

import os
import pickle


def ensure_directory(directory):
    """Create the directory if it does not exist."""
    os.makedirs(directory, exist_ok=True)


def save_pickle(path, data):
    """Save a Python object as a pickle file."""

    ensure_directory(os.path.dirname(path))

    with open(path, "wb") as f:
        pickle.dump(data, f)


def load_pickle(path, default=None):
    """
    Load a pickle file.

    Return the default value if the file does not exist.
    """

    if not os.path.exists(path):
        return default

    with open(path, "rb") as f:
        return pickle.load(f)


def delete_file(path):
    """
    Delete a file if it exists.
    """

    if os.path.exists(path):
        os.remove(path)


def file_exists(path):
    """Return True if the file exists."""

    return os.path.exists(path)


def save_metadata(path, metadata):
    """Save metadata."""

    save_pickle(path, metadata)


def load_metadata(path):
    """
    Load metadata.
    Return an empty dictionary if metadata does not exist.
    """

    return load_pickle(path, default={})