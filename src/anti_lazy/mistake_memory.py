from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List

from .schemas import Rule, utc_now


class MistakeMemory:
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.write_text("", encoding="utf-8")

    def add_rule(
        self,
        domain: str,
        intent: str,
        instruction: str,
        severity: str = "medium",
    ) -> Rule:
        rule = Rule(
            rule_id=f"rule-{self._next_id()}",
            domain=domain,
            intent=intent,
            instruction=instruction,
            severity=severity,
            created_at=utc_now(),
        )
        with self.storage_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(rule)) + "\n")
        return rule

    def get_applicable_rules(self, task: str) -> List[Rule]:
        rules = list(self._load_rules())
        rules = self._suppress_conflicts(rules)
        return [rule for rule in rules if self._matches(rule, task)]

    def _load_rules(self) -> Iterable[Rule]:
        with self.storage_path.open("r", encoding="utf-8-sig") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                yield Rule(**payload)

    def _matches(self, rule: Rule, task: str) -> bool:
        lowered = task.lower()
        return (
            rule.domain == "*"
            or rule.intent == "*"
            or rule.domain.lower() in lowered
            or rule.intent.lower() in lowered
        )

    @staticmethod
    def _suppress_conflicts(rules: Iterable[Rule]) -> List[Rule]:
        latest_by_scope: dict[tuple[str, str], Rule] = {}
        for rule in rules:
            key = (rule.domain, rule.intent)
            existing = latest_by_scope.get(key)
            if existing is None:
                latest_by_scope[key] = rule
                continue
            if MistakeMemory._compare_rules(rule, existing) >= 0:
                latest_by_scope[key] = rule
        return list(latest_by_scope.values())

    @staticmethod
    def _compare_rules(left: Rule, right: Rule) -> int:
        left_rank = MistakeMemory._severity_rank(left.severity)
        right_rank = MistakeMemory._severity_rank(right.severity)
        if left_rank != right_rank:
            return left_rank - right_rank
        return 1

    @staticmethod
    def _severity_rank(severity: str) -> int:
        mapping = {"low": 0, "medium": 1, "high": 2}
        return mapping.get(severity, 0)

    def _next_id(self) -> int:
        count = 0
        with self.storage_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    count += 1
        return count + 1
