from __future__ import annotations

import re
from dataclasses import dataclass
from math import sqrt
from pathlib import Path
from typing import Iterable, List

from .schemas import Snippet


@dataclass
class LocalDocsTool:
    docs_path: Path
    use_embeddings: bool = True

    def search(self, query: str, top_k: int = 3) -> List[Snippet]:
        snippets: List[Snippet] = []
        if not self.docs_path.exists():
            return snippets

        doc_files = sorted(self.docs_path.glob("*.txt"))
        for doc in doc_files:
            content = doc.read_text(encoding="utf-8").strip()
            if not content:
                continue
            score = self._score(query, content)
            if self.use_embeddings:
                score = max(score, self._embedding_score(query, content))
            if score <= 0:
                continue
            snippet_id = f"{doc.stem}-{len(snippets) + 1}"
            snippets.append(
                Snippet(
                    snippet_id=snippet_id,
                    source=doc.name,
                    content=self._truncate(content),
                )
            )
            if len(snippets) >= top_k:
                break
        return snippets

    @staticmethod
    def _score(query: str, content: str) -> int:
        score = 0
        lowered = content.lower()
        for token in query.lower().split():
            if token in lowered:
                score += 1
        return score

    @staticmethod
    def _embedding_score(query: str, content: str) -> float:
        query_vec = _term_frequency(query)
        content_vec = _term_frequency(content)
        if not query_vec or not content_vec:
            return 0.0
        dot = sum(query_vec[token] * content_vec.get(token, 0.0) for token in query_vec)
        return dot / (_vector_norm(query_vec) * _vector_norm(content_vec))

    @staticmethod
    def _truncate(content: str, limit: int = 400) -> str:
        if len(content) <= limit:
            return content
        return content[: limit - 3].rstrip() + "..."


@dataclass
class CodeSearchTool:
    repo_root: Path
    allowed_extensions: Iterable[str] = (".py", ".md", ".txt")
    ignore_dirs: Iterable[str] = (".git", "data", ".venv", "__pycache__")

    def search(self, query: str, top_k: int = 3) -> List[Snippet]:
        snippets: List[Snippet] = []
        query_tokens = _tokenize(query)
        if not query_tokens:
            return snippets

        for path in self._iter_files():
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            score = _keyword_score(query_tokens, content)
            if score <= 0:
                continue
            snippet_id = f"code-{len(snippets) + 1}"
            snippets.append(
                Snippet(
                    snippet_id=snippet_id,
                    source=str(path.relative_to(self.repo_root)),
                    content=LocalDocsTool._truncate(content.strip()),
                )
            )
            if len(snippets) >= top_k:
                break
        return snippets

    def _iter_files(self) -> Iterable[Path]:
        for path in self.repo_root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in self.ignore_dirs for part in path.parts):
                continue
            if path.suffix.lower() not in self.allowed_extensions:
                continue
            yield path


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _term_frequency(text: str) -> dict[str, float]:
    tokens = _tokenize(text)
    if not tokens:
        return {}
    total = float(len(tokens))
    freq: dict[str, float] = {}
    for token in tokens:
        freq[token] = freq.get(token, 0.0) + 1.0
    return {token: count / total for token, count in freq.items()}


def _vector_norm(vector: dict[str, float]) -> float:
    return sqrt(sum(value * value for value in vector.values()))


def _keyword_score(tokens: Iterable[str], content: str) -> int:
    lowered = content.lower()
    return sum(1 for token in tokens if token in lowered)
