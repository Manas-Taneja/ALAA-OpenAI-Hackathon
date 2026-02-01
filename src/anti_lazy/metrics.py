from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass(frozen=True)
class MetricsSummary:
    runs_count: int
    average_tool_coverage: float
    average_snippets: float
    total_used_snippets: int
    rules_applied_count: int


@dataclass(frozen=True)
class MistakeStats:
    total_rules: int
    by_severity: dict[str, int]
    by_domain: dict[str, int]


def load_runs(path: Path) -> List[dict]:
    if not path.exists():
        return []
    runs = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            runs.extend(_parse_json_objects(line))
    return runs


def load_mistakes(path: Path) -> List[dict]:
    if not path.exists():
        return []
    mistakes = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            mistakes.extend(_parse_json_objects(line))
    return mistakes


def _parse_json_objects(line: str) -> List[dict]:
    trimmed = line.strip()
    if not trimmed:
        return []
    decoder = json.JSONDecoder()
    index = 0
    objects: List[dict] = []
    while index < len(trimmed):
        try:
            payload, offset = decoder.raw_decode(trimmed[index:])
        except json.JSONDecodeError:
            break
        if isinstance(payload, dict):
            objects.append(payload)
        index += offset
        while index < len(trimmed) and trimmed[index].isspace():
            index += 1
    return objects


def summarize_runs(runs: Iterable[dict]) -> MetricsSummary:
    runs_list = list(runs)
    if not runs_list:
        return MetricsSummary(0, 0.0, 0.0, 0, 0)
    total_tool_coverage = sum(run.get("tool_coverage", 0.0) for run in runs_list)
    total_snippets = sum(run.get("snippets_count", 0) for run in runs_list)
    total_used_snippets = sum(
        len(run.get("used_snippet_ids", [])) for run in runs_list
    )
    rules_applied = sum(len(run.get("rules_applied", [])) for run in runs_list)
    count = len(runs_list)
    return MetricsSummary(
        runs_count=count,
        average_tool_coverage=total_tool_coverage / count,
        average_snippets=total_snippets / count,
        total_used_snippets=total_used_snippets,
        rules_applied_count=rules_applied,
    )


def summarize_mistakes(mistakes: Iterable[dict]) -> MistakeStats:
    mistakes_list = list(mistakes)
    by_severity: dict[str, int] = {}
    by_domain: dict[str, int] = {}
    for mistake in mistakes_list:
        severity = mistake.get("severity", "unknown")
        by_severity[severity] = by_severity.get(severity, 0) + 1
        domain = mistake.get("domain", "unknown")
        by_domain[domain] = by_domain.get(domain, 0) + 1
    return MistakeStats(
        total_rules=len(mistakes_list),
        by_severity=by_severity,
        by_domain=by_domain,
    )


def format_metrics_table(summary: MetricsSummary) -> str:
    lines = [
        "Metric                          | Value",
        "--------------------------------|-----------------",
        f"Runs count                      | {summary.runs_count}",
        f"Average tool coverage           | {summary.average_tool_coverage:.2f}",
        f"Average snippets per run        | {summary.average_snippets:.2f}",
        f"Total used snippet IDs          | {summary.total_used_snippets}",
        f"Rules applied (total)           | {summary.rules_applied_count}",
    ]
    return "\n".join(lines)


def format_mistake_table(stats: MistakeStats) -> str:
    lines = [
        "Mistake stats                   | Value",
        "--------------------------------|-----------------",
        f"Total rules                     | {stats.total_rules}",
    ]
    for severity, count in sorted(stats.by_severity.items()):
        lines.append(f"Severity: {severity:<20} | {count}")
    for domain, count in sorted(stats.by_domain.items()):
        lines.append(f"Domain: {domain:<22} | {count}")
    return "\n".join(lines)
