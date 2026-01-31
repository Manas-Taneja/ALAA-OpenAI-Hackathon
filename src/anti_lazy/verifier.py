from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .schemas import DraftAnswer, Snippet, VerificationResult


@dataclass
class Verifier:
    def verify(self, draft: DraftAnswer, snippets: List[Snippet]) -> VerificationResult:
        if not snippets and draft.used_snippet_ids:
            return VerificationResult(
                ok=False,
                reason="Used snippet IDs but no snippets exist.",
                rewrite_instruction="Remove snippet references and ask for more context.",
            )
        if snippets and not draft.used_snippet_ids:
            return VerificationResult(
                ok=False,
                reason="No snippet IDs were cited.",
                rewrite_instruction="Include at least one snippet_id in used_snippet_ids.",
            )
        if not snippets and draft.notes == "no_context":
            return VerificationResult(ok=True, reason="No context available.")
        return VerificationResult(ok=True, reason="Grounding requirements satisfied.")
