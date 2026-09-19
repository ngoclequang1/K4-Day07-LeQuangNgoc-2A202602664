from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []

        # Split after punctuation so that sentence-ending marks are retained.
        sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text.strip())]
        return [
            " ".join(sentences[start : start + self.max_sentences_per_chunk])
            for start in range(0, len(sentences), self.max_sentences_per_chunk)
        ]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators or remaining_separators[0] == "":
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        smaller_separators = remaining_separators[1:]
        if separator not in current_text:
            return self._split(current_text, smaller_separators)

        pieces = current_text.split(separator)
        # Keep every separator, including trailing whitespace and paragraph breaks.
        parts = [piece + separator for piece in pieces[:-1]]
        if pieces[-1]:
            parts.append(pieces[-1])

        chunks: list[str] = []
        pending = ""
        for part in parts:
            for fragment in self._split(part, smaller_separators):
                if pending and len(pending) + len(fragment) > self.chunk_size:
                    chunks.append(pending)
                    pending = ""
                pending += fragment
        if pending:
            chunks.append(pending)
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if len(vec_a) != len(vec_b):
        raise ValueError("Vectors must have the same number of dimensions")
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    similarity = _dot(vec_a, vec_b) / (norm_a * norm_b)
    # Floating-point rounding can otherwise put identical vectors just above 1.
    return max(-1.0, min(1.0, similarity))


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        strategies = {
            # Ten percent overlap, capped at 50, also supports tiny chunk sizes.
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=min(50, chunk_size // 10)),
            "by_sentences": SentenceChunker(),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }
        comparison = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            comparison[name] = {
                "count": count,
                "avg_length": sum(len(chunk) for chunk in chunks) / count if count else 0.0,
                "chunks": chunks,
            }
        return comparison
