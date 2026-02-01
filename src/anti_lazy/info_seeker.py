from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .schemas import ContextPack, Snippet
from .tools import CodeSearchTool, LocalDocsTool


@dataclass
class InfoSeeker:
    docs_tool: LocalDocsTool
    code_tool: Optional[CodeSearchTool] = None

    def build_context_pack(self, query: str) -> ContextPack:
        snippets = self.docs_tool.search(query)
        required_tools: List[str] = ["local_docs"]
        tools_called: List[str] = ["local_docs"]
        if self.code_tool is not None:
            code_snippets = self.code_tool.search(query)
            snippets.extend(code_snippets)
            required_tools.append("code_search")
            tools_called.append("code_search")
        return ContextPack(
            query=query,
            snippets=snippets,
            required_tools=required_tools,
            tools_called=tools_called,
        )
