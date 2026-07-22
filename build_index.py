"""
build_index.py

Incrementally build document indexes.
"""

import os

from storage import (
    load_metadata,
    save_metadata,
    save_pickle
)

from indexer import (
    index_document,
    save_document_index,
    remove_document_index,
    rebuild_master_index,
    build_metadata
)

from utils import get_file_mtime


DOCUMENT_DIR = "documents"
INDEX_DIR = "index"
FILE_INDEX_DIR = os.path.join(INDEX_DIR, "files")

METADATA_PATH = os.path.join(
    INDEX_DIR,
    "metadata.pkl"
)

MASTER_INDEX_PATH = os.path.join(
    INDEX_DIR,
    "master.pkl"
)

os.makedirs(FILE_INDEX_DIR, exist_ok=True)


def main():

    metadata = load_metadata(METADATA_PATH)

    indexed_documents = []

    current_files = set()

    changed = False

    for filename in os.listdir(DOCUMENT_DIR):

        if not filename.endswith(".txt"):
            continue

        current_files.add(filename)

        filepath = os.path.join(
            DOCUMENT_DIR,
            filename
        )

        current_mtime = get_file_mtime(filepath)

        if (
            filename not in metadata or
            metadata[filename]["mtime"] != current_mtime
        ):

            print(f"Indexing {filename}")

            document = index_document(filepath)

            save_document_index(
                document,
                FILE_INDEX_DIR
            )

            changed = True

        else:

            print(f"Skipping {filename}")

    removed = set(metadata.keys()) - current_files

    for filename in removed:

        print(f"Removing {filename}")

        remove_document_index(
            filename,
            FILE_INDEX_DIR
        )

        changed = True

    if changed:

        print("Building master index...")

        master = rebuild_master_index(
            FILE_INDEX_DIR
        )

        save_pickle(
            MASTER_INDEX_PATH,
            master
        )

        document_list = []

        for file in os.listdir(FILE_INDEX_DIR):

            path = os.path.join(
                FILE_INDEX_DIR,
                file
            )

            from storage import load_pickle

            document_list.append(
                load_pickle(path)
            )

        metadata = build_metadata(
            document_list
        )

        save_metadata(
            METADATA_PATH,
            metadata
        )

        print("Done.")

    else:

        print("Everything is up-to-date.")


if __name__ == "__main__":
    main()