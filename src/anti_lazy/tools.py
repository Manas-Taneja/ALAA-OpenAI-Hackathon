from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from .schemas import Snippet


@dataclass
class LocalDocsTool:
    docs_path: Path

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
    def _truncate(content: str, limit: int = 400) -> str:
        if len(content) <= limit:
            return content
        return content[: limit - 3].rstrip() + "..."
