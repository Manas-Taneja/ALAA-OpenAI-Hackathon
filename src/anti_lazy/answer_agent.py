from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import List

from .llm_client import LLMClient
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

        llm_client = LLMClient.from_env()
        if llm_client:
            payload = self._answer_with_llm(
                llm_client=llm_client,
                task=task,
                rules=rules,
                context=context,
                enforce_snippet_usage=enforce_snippet_usage,
            )
            return DraftAnswer(
                answer=json.dumps(asdict(payload), ensure_ascii=True, indent=2),
                used_snippet_ids=payload.used_snippet_ids,
                payload=payload,
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

    def _answer_with_llm(
        self,
        llm_client: LLMClient,
        task: str,
        rules: List[Rule],
        context: ContextPack,
        enforce_snippet_usage: bool,
    ) -> AnswerPayload:
        snippet_lines = [
            f"- {snippet.snippet_id}: {snippet.content}"
            for snippet in context.snippets
        ]
        rule_lines = [f"- {rule.rule_id}: {rule.instruction}" for rule in rules]
        usage_rule = (
            "Include at least one snippet_id from the list."
            if enforce_snippet_usage
            else "If no snippet supports a claim, leave used_snippet_ids empty."
        )
        prompt = (
            "You are an assistant that must answer using provided snippets.\n"
            "Return ONLY valid JSON with keys: response, used_snippet_ids, applied_rules.\n"
            f"Task: {task}\n\n"
            "Snippets:\n"
            f"{chr(10).join(snippet_lines)}\n\n"
            "Rules:\n"
            f"{chr(10).join(rule_lines) if rule_lines else '- none'}\n\n"
            f"Snippet usage requirement: {usage_rule}\n"
            "Ensure used_snippet_ids is a subset of the snippet IDs above.\n"
        )
        raw = llm_client.generate(prompt)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {
                "response": raw.strip(),
                "used_snippet_ids": [],
                "applied_rules": [rule.rule_id for rule in rules],
            }
        return AnswerPayload(
            response=payload.get("response", "").strip(),
            used_snippet_ids=list(payload.get("used_snippet_ids", [])),
            applied_rules=list(payload.get("applied_rules", [])),
        )
