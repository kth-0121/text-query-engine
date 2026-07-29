"""Shared text-normalization and naming helpers."""

from __future__ import annotations

import hashlib
import re

from stopwords import STOPWORDS

_PUNCTUATION = re.compile(r"[^0-9a-zA-Z가-힣\s]+")


def normalize_text(text: str) -> str:
    """Case-fold English and replace punctuation with whitespace.

    Korean syllables, English letters, numbers, and existing whitespace are
    retained.  ``casefold`` leaves Korean unchanged.
    """
    return _PUNCTUATION.sub(" ", text.casefold())


def tokenize(text: str) -> list[str]:
    """Split normalized text into whitespace-delimited tokens."""
    return text.split()


def preprocess_with_positions(text: str) -> list[tuple[str, int]]:
    """Return indexed tokens with original (pre-stopword-removal) positions.

    Keeping original positions prevents ``abe was lincoln`` from matching the
    adjacent query ``abe && lincoln`` after the stopword ``was`` is removed.
    """
    return [
        (word, position)
        for position, word in enumerate(tokenize(normalize_text(text)))
        if word not in STOPWORDS
    ]


def safe_filename(document_name: str) -> str:
    """Return a collision-safe pickle filename for a relative document path."""
    stem = document_name.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    digest = hashlib.sha256(document_name.encode("utf-8")).hexdigest()[:16]
    return f"{stem}-{digest}.pkl"
