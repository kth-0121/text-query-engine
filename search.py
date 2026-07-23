"""
search.py

Boolean query search engine.
"""

import os
import re

from storage import load_pickle


INDEX_DIR = "index"

MASTER_PATH = os.path.join(INDEX_DIR,"master.pkl")

FILE_INDEX_DIR = os.path.join(INDEX_DIR,"files")


master = load_pickle(MASTER_PATH)

all_entries = set()

for locations in master.values():
    all_entries |= locations


def tokenize_query(query):

    return re.findall(
        r'\w+|&&|\|\||!|\(|\)',
        query.lower()
    )


def evaluate(tokens):

    stack = []

    def apply_not(expression):

        while "!" in expression:

            pos = expression.index("!")

            expression[pos:pos + 2] = [
                all_entries - expression[pos + 1]
            ]

        return expression

    def compute(expression):

        expression = apply_not(expression)

        while "&&" in expression:

            pos = expression.index("&&")

            result = (
                expression[pos - 1]
                &
                expression[pos + 1]
            )

            expression[pos - 1:pos + 2] = [result]

        while "||" in expression:

            pos = expression.index("||")

            result = (
                expression[pos - 1]
                |
                expression[pos + 1]
            )

            expression[pos - 1:pos + 2] = [result]

        return expression[0]

    for token in tokens:

        if token == ")":

            temp = []

            while stack[-1] != "(":
                temp.append(stack.pop())

            stack.pop()

            temp.reverse()

            stack.append(
                compute(temp)
            )

        elif token == "(":
            stack.append(token)

        elif token in ["&&", "||", "!"]:
            stack.append(token)

        else:
            stack.append(
                master.get(token, set())
            )

    return compute(stack)


def print_results(results):

    grouped = {}

    for filename, line_number in results:

        grouped.setdefault(
            filename,
            []
        ).append(line_number)

    for filename in sorted(grouped):

        path = os.path.join(
            FILE_INDEX_DIR,
            filename.replace(".txt", ".pkl")
        )

        document = load_pickle(path)

        print()
        print(filename)

        for line_number in sorted(grouped[filename]):

            line = document["lines"][
                line_number - 1
            ].rstrip()

            print(
                f"  ({line_number}) {line}"
            )


def main():

    while True:

        query = input("\nSearch (. to quit): ").strip()

        if query == ".":
            break

        tokens = tokenize_query(query)

        results = evaluate(tokens)

        if not results:

            print("No results found.")
            continue

        print(
            f"\nFound {len(results)} matching line(s)."
        )

        print_results(results)


if __name__ == "__main__":
    main()