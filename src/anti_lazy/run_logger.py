from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .schemas import RunLog


class RunLogger:
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.write_text("", encoding="utf-8")

    def write(self, log: RunLog) -> None:
        with self.storage_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(log)) + "\n")
