"""
main.py

Entry point for the Text Query Engine.
"""

import build_index
import search


def print_header():
    """Print the application header."""

    print("=" * 45)
    print("          TEXT QUERY ENGINE")
    print("=" * 45)


def print_menu():
    """Print the main menu."""

    print("\n1. Build / Update Index")
    print("2. Search")
    print("3. Exit")


def handle_build():
    """Run the indexing process."""

    print("\nBuilding index...\n")

    try:
        build_index.main()
    except Exception as e:
        print(f"\nError while building index: {e}")


def handle_search():
    """Run the search engine."""

    print("\nStarting search engine...\n")

    try:
        search.main()
    except FileNotFoundError:
        print("No index found.")
        print("Please build the index first.")
    except Exception as e:
        print(f"\nSearch error: {e}")


def main():
    """Application entry point."""

    while True:

        print_header()
        print_menu()

        choice = input("\nSelect an option: ").strip()

        if choice == "1":
            handle_build()

        elif choice == "2":
            handle_search()

        elif choice == "3":
            print("\nGoodbye!")
            break

        else:
            print("\nInvalid option. Please try again.")

        input("\nPress Enter to return to the menu...")


if __name__ == "__main__":
    main()