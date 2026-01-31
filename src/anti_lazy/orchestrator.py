from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import List

from .answer_agent import AnswerAgent
from .info_seeker import InfoSeeker
from .mistake_memory import MistakeMemory
from .run_logger import RunLogger
from .schemas import DraftAnswer, RunLog, Rule, VerificationResult, utc_now
from .verifier import Verifier


@dataclass
class Orchestrator:
    mistake_memory: MistakeMemory
    info_seeker: InfoSeeker
    answer_agent: AnswerAgent
    verifier: Verifier
    run_logger: RunLogger

    def run_task(self, task: str) -> DraftAnswer:
        rules = self.mistake_memory.get_applicable_rules(task)
        context_pack = self.info_seeker.build_context_pack(task)
        draft = self.answer_agent.answer(task, rules, context_pack)
        verification = self.verifier.verify(draft, context_pack.snippets)

        if not verification.ok and verification.rewrite_instruction:
            draft = self.answer_agent.answer(
                task,
                rules,
                context_pack,
                enforce_snippet_usage=True,
            )
            verification = self.verifier.verify(draft, context_pack.snippets)

        self._log_run(
            task=task,
            rules=rules,
            tools_called=context_pack.tools_called,
            draft=draft,
            verification=verification,
            snippets_count=len(context_pack.snippets),
        )
        return draft

    def _log_run(
        self,
        task: str,
        rules: List[Rule],
        tools_called: List[str],
        draft: DraftAnswer,
        verification: VerificationResult,
        snippets_count: int,
    ) -> None:
        log = RunLog(
            run_id=str(uuid.uuid4()),
            task=task,
            timestamp=utc_now(),
            rules_applied=[rule.rule_id for rule in rules],
            tools_called=tools_called,
            snippets_count=snippets_count,
            used_snippet_ids=draft.used_snippet_ids,
            verification={
                "ok": verification.ok,
                "reason": verification.reason,
            },
        )
        self.run_logger.write(log)
