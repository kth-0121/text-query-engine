"""Application entry point for the Text Query Engine."""

from build_index import build_index
from search import main as search_main


def main() -> None:
    """Update indexes for documents/ and launch the search interface."""
    print("=" * 50)
    print("Text Query Engine")
    print("=" * 50)
    print("\nChecking document index...")
    build_index()
    print("\nStarting search engine...")
    search_main()


if __name__ == "__main__":
    main()
