"""Tokenizer and recursive-descent parser for Boolean text queries."""

from __future__ import annotations

import re
from typing import TypeAlias

QueryNode: TypeAlias = tuple[str, object] | tuple[str, object, object]
TOKEN_PATTERN = re.compile(r"[^\W_]+|&&|\|\||!|\(|\)", re.UNICODE)


def tokenize_query(query: str) -> list[str]:
    """Split a query into normalized words and Boolean operators."""
    return TOKEN_PATTERN.findall(query.casefold())


class Parser:
    """Parse with precedence: parentheses, NOT, adjacency AND, OR."""

    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.position = 0

    def current(self) -> str | None:
        return self.tokens[self.position] if self.position < len(self.tokens) else None

    def consume(self) -> str:
        token = self.current()
        if token is None:
            raise ValueError("Unexpected end of query.")
        self.position += 1
        return token

    def parse(self) -> QueryNode:
        if not self.tokens:
            raise ValueError("Query cannot be empty.")
        expression = self.parse_or()
        if self.current() is not None:
            raise ValueError(f"Unexpected token: {self.current()}")
        return expression

    def parse_or(self) -> QueryNode:
        left = self.parse_and()
        while self.current() == "||":
            self.consume()
            left = ("OR", left, self.parse_and())
        return left

    def parse_and(self) -> QueryNode:
        left = self.parse_unary()
        while self.current() == "&&":
            self.consume()
            left = ("AND", left, self.parse_unary())
        return left

    def parse_unary(self) -> QueryNode:
        if self.current() == "!":
            self.consume()
            return ("NOT", self.parse_unary())
        return self.parse_primary()

    def parse_primary(self) -> QueryNode:
        token = self.current()
        if token is None:
            raise ValueError("Unexpected end of query.")
        if token == "(":
            self.consume()
            expression = self.parse_or()
            if self.current() != ")":
                raise ValueError("Missing closing parenthesis.")
            self.consume()
            return expression
        if token in {"&&", "||", "!", ")"}:
            raise ValueError(f"Expected a word or '(', got: {token}")
        return ("WORD", self.consume())


def parse_query(query: str) -> QueryNode:
    """Parse *query* into an AST."""
    return Parser(tokenize_query(query)).parse()
