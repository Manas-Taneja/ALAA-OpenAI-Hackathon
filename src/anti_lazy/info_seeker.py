from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .schemas import ContextPack, Snippet
from .tools import LocalDocsTool


@dataclass
class InfoSeeker:
    docs_tool: LocalDocsTool

    def build_context_pack(self, query: str) -> ContextPack:
        snippets = self.docs_tool.search(query)
        tools_called: List[str] = ["local_docs"]
        return ContextPack(query=query, snippets=snippets, tools_called=tools_called)
