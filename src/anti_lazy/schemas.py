from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Snippet:
    snippet_id: str
    source: str
    content: str


@dataclass(frozen=True)
class ContextPack:
    query: str
    snippets: List[Snippet]
    tools_called: List[str]


@dataclass(frozen=True)
class Rule:
    rule_id: str
    domain: str
    intent: str
    instruction: str
    severity: str
    created_at: str


@dataclass
class DraftAnswer:
    answer: str
    used_snippet_ids: List[str]
    notes: Optional[str] = None


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    reason: str
    rewrite_instruction: Optional[str] = None


@dataclass(frozen=True)
class RunLog:
    run_id: str
    task: str
    timestamp: str
    rules_applied: List[str]
    tools_called: List[str]
    snippets_count: int
    used_snippet_ids: List[str]
    verification: Dict[str, Any]

    def to_json(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp
        return payload


def utc_now() -> str:
    return datetime.utcnow().isoformat() + "Z"
