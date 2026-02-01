from __future__ import annotations

import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None
from dataclasses import dataclass
from typing import Optional

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None


@dataclass
class LLMClient:
    model: str

    @classmethod
    def from_env(cls) -> Optional["LLMClient"]:
        if load_dotenv:
            load_dotenv()
        if OpenAI is None:
            return None
        if not os.getenv("OPENAI_API_KEY"):
            return None
        model = os.getenv("OPENAI_MODEL", "gpt-5.1")
        return cls(model=model)

    def generate(self, prompt: str) -> str:
        if OpenAI is None:
            raise RuntimeError("OpenAI SDK is not installed.")
        client = OpenAI()
        response = client.responses.create(
            model=self.model,
            input=prompt,
        )
        return response.output_text
