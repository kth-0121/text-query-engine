"""
indexer.py

Functions for indexing documents and maintaining
the master inverted index.
"""

import os

from collections import Counter, defaultdict

from utils import preprocess, get_file_mtime, safe_filename
from storage import save_pickle, load_pickle, delete_file


def index_document(filepath):
    """
    Build an inverted index for a single document.
    """

    filename = os.path.basename(filepath)

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    inverted_index = defaultdict(set)
    counter = Counter()

    for line_number, line in enumerate(lines, start=1):

        words = preprocess(line)

        counter.update(words)

        for word in words:
            inverted_index[word].add(line_number)

    return {
        "filename": filename,
        "lines": lines,
        "index": dict(inverted_index),
        "counter": counter,
        "mtime": get_file_mtime(filepath)
    }


def save_document_index(document_data, index_directory):
    """
    Save the index of a single document.
    """

    filename = safe_filename(document_data["filename"])

    path = os.path.join(index_directory, filename)

    save_pickle(path, document_data)


def remove_document_index(filename, index_directory):
    """
    Remove a document index.
    """

    path = os.path.join(
        index_directory,
        safe_filename(filename)
    )

    delete_file(path)


def rebuild_master_index(index_directory):
    """
    Rebuild the master inverted index from
    all document index files.
    """

    master = defaultdict(set)

    for file in os.listdir(index_directory):

        if not file.endswith(".pkl"):
            continue

        path = os.path.join(index_directory, file)

        document = load_pickle(path)

        filename = document["filename"]

        for word, line_numbers in document["index"].items():

            for line_number in line_numbers:

                master[word].add(
                    (filename, line_number)
                )

    return dict(master)


def build_metadata(document_data_list):
    """
    Build metadata from indexed documents.
    """

    metadata = {}

    for document in document_data_list:

        metadata[document["filename"]] = {
            "mtime": document["mtime"]
        }

    return metadata