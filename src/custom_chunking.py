"""Markdown section chunking; sizes are characters, not tokens."""
import re
from .chunking import RecursiveChunker


class HeadingChunker:
    def __init__(self, chunk_size=350):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.chunk_size = chunk_size

    def chunk(self, text):
        chunks, headings, body = [], [], []

        def flush():
            content = "".join(body).strip()
            prefix = "\n".join(value for _, value in headings)
            if not content and not prefix:
                return
            if not content:
                chunks.extend(RecursiveChunker(chunk_size=self.chunk_size).chunk(prefix))
                return
            prefix = prefix + "\n\n" if prefix else ""
            if len(prefix) >= self.chunk_size:
                chunks.extend(RecursiveChunker(chunk_size=self.chunk_size).chunk(prefix + content))
            else:
                chunks.extend(prefix + part for part in RecursiveChunker(
                    chunk_size=self.chunk_size - len(prefix)).chunk(content))

        for line in text.splitlines(keepends=True):
            match = re.match(r"^(#{1,6})\s+", line)
            if match:
                if body:
                    flush()
                body = []
                level = len(match[1])
                headings = [(n, h) for n, h in headings if n < level]
                headings.append((level, line.strip()))
            else:
                body.append(line)
        flush()
        return chunks
