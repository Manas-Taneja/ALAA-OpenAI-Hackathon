from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import List

from .schemas import AnswerPayload, ContextPack, DraftAnswer, Rule


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
            payload = AnswerPayload(
                response=(
                    "I could not find relevant context. "
                    "Please provide more details or add documentation to search."
                ),
                used_snippet_ids=[],
                applied_rules=[rule.rule_id for rule in rules],
            )
            return DraftAnswer(
                answer=json.dumps(asdict(payload), ensure_ascii=True, indent=2),
                used_snippet_ids=[],
                payload=payload,
                notes="no_context",
            )

        selected = context.snippets[0]
        used_snippet_ids = [selected.snippet_id] if enforce_snippet_usage else []
        response = (
            f"Based on {selected.source}, here is the grounded response. "
            f"{selected.content}"
        )
        payload = AnswerPayload(
            response=response,
            used_snippet_ids=used_snippet_ids,
            applied_rules=[rule.rule_id for rule in rules],
        )
        return DraftAnswer(
            answer=json.dumps(asdict(payload), ensure_ascii=True, indent=2),
            used_snippet_ids=used_snippet_ids,
            payload=payload,
        )
