from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .schemas import ContextPack, DraftAnswer, Rule


@dataclass
class AnswerAgent:
    def answer(
        self,
        task: str,
        rules: List[Rule],
        context: ContextPack,
        enforce_snippet_usage: bool = False,
    ) -> DraftAnswer:
        if not context.snippets:
            return DraftAnswer(
                answer=(
                    "I could not find relevant context. "
                    "Please provide more details or add documentation to search."
                ),
                used_snippet_ids=[],
                notes="no_context",
            )

        selected = context.snippets[0]
        used_snippet_ids = [selected.snippet_id] if enforce_snippet_usage else []
        rule_instructions = " ".join(rule.instruction for rule in rules)
        answer = (
            f"Based on {selected.source}, here is the grounded response. "
            f"{selected.content}"
        )
        if rule_instructions:
            answer = f"{answer}\n\nApplied rules: {rule_instructions}"
        return DraftAnswer(answer=answer, used_snippet_ids=used_snippet_ids)
