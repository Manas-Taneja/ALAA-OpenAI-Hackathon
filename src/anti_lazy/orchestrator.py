from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import List

from .answer_agent import AnswerAgent
from .info_seeker import InfoSeeker
from .mistake_memory import MistakeMemory
from .run_logger import RunLogger
from .schemas import DraftAnswer, RunLog, Rule, RunResult, VerificationResult, utc_now
from .verifier import Verifier


@dataclass
class Orchestrator:
    mistake_memory: MistakeMemory
    info_seeker: InfoSeeker
    answer_agent: AnswerAgent
    verifier: Verifier
    run_logger: RunLogger

    def run_task(self, task: str) -> RunResult:
        task_type = self._classify_task(task)
        trace: List[dict] = []
        trace.append({"stage": "classify", "task_type": task_type})
        rules = self.mistake_memory.get_applicable_rules(task)
        trace.append({"stage": "rules", "count": len(rules), "rule_ids": [rule.rule_id for rule in rules]})
        context_pack = self.info_seeker.build_context_pack(task)
        trace.append({"stage": "retrieve", "tools_called": context_pack.tools_called, "snippets_count": len(context_pack.snippets)})
        draft = self.answer_agent.answer(task, rules, context_pack)
        trace.append({"stage": "draft", "used_snippet_ids": draft.used_snippet_ids})
        verification = self.verifier.verify(draft, context_pack.snippets)
        trace.append({"stage": "verify", "ok": verification.ok, "reason": verification.reason})
        attempts = [
            {
                "used_snippet_ids": draft.used_snippet_ids,
                "verification": {
                    "ok": verification.ok,
                    "reason": verification.reason,
                },
                "rewrite_instruction": verification.rewrite_instruction,
            }
        ]

        if not verification.ok and verification.rewrite_instruction:
            draft = self.answer_agent.answer(
                task,
                rules,
                context_pack,
                enforce_snippet_usage=True,
            )
            verification = self.verifier.verify(draft, context_pack.snippets)
            trace.append({"stage": "rewrite", "used_snippet_ids": draft.used_snippet_ids, "ok": verification.ok, "reason": verification.reason})
        trace.append({"stage": "verify", "ok": verification.ok, "reason": verification.reason})
            attempts.append(
                {
                    "used_snippet_ids": draft.used_snippet_ids,
                    "verification": {
                        "ok": verification.ok,
                        "reason": verification.reason,
                    },
                    "rewrite_instruction": verification.rewrite_instruction,
                }
            )

        self._log_run(
            task=task,
            task_type=task_type,
            rules=rules,
            required_tools=context_pack.required_tools,
            tools_called=context_pack.tools_called,
            draft=draft,
            verification=verification,
            attempts=attempts,
            trace=trace,
            snippets_count=len(context_pack.snippets),
        )
        return RunResult(
            draft=draft,
            task_type=task_type,
            tools_called=context_pack.tools_called,
            snippets_count=len(context_pack.snippets),
            trace=trace,
        )

    def _log_run(
        self,
        task: str,
        task_type: str,
        rules: List[Rule],
        required_tools: List[str],
        tools_called: List[str],
        draft: DraftAnswer,
        verification: VerificationResult,
        attempts: List[dict],
        trace: List[dict],
        snippets_count: int,
    ) -> None:
        required_count = len(required_tools)
        tool_coverage = (
            len(tools_called) / required_count if required_count else 0.0
        )
        log = RunLog(
            run_id=str(uuid.uuid4()),
            task=task,
            task_type=task_type,
            timestamp=utc_now(),
            rules_applied=[rule.rule_id for rule in rules],
            required_tools=required_tools,
            tools_called=tools_called,
            tool_coverage=tool_coverage,
            snippets_count=snippets_count,
            used_snippet_ids=draft.used_snippet_ids,
            attempts=attempts,
            trace=trace,
            verification={
                "ok": verification.ok,
                "reason": verification.reason,
            },
        )
        self.run_logger.write(log)

    @staticmethod
    def _classify_task(task: str) -> str:
        lowered = task.lower().strip()
        if any(token in lowered for token in ("summarize", "summary", "tldr", "tl;dr")):
            return "summarize"
        if any(token in lowered for token in ("explain", "how", "why", "what")):
            return "explain"
        if any(token in lowered for token in ("list", "steps", "checklist")):
            return "list"
        if any(token in lowered for token in ("fix", "debug", "error", "issue")):
            return "debug"
        return "general"
