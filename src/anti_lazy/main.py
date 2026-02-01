from __future__ import annotations

import argparse
from pathlib import Path

from .answer_agent import AnswerAgent
from .info_seeker import InfoSeeker
from .metrics import (
    format_metrics_table,
    format_mistake_table,
    load_mistakes,
    load_runs,
    summarize_mistakes,
    summarize_runs,
)
from .mistake_memory import MistakeMemory
from .orchestrator import Orchestrator
from .run_logger import RunLogger
from .tools import CodeSearchTool, LocalDocsTool
from .verifier import Verifier
from .web_viewer import run_server

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


def build_orchestrator() -> Orchestrator:
    docs_tool = LocalDocsTool(DATA_DIR / "docs")
    code_tool = CodeSearchTool(ROOT)
    info_seeker = InfoSeeker(docs_tool=docs_tool, code_tool=code_tool)
    mistake_memory = MistakeMemory(DATA_DIR / "mistakes.jsonl")
    run_logger = RunLogger(DATA_DIR / "runs.jsonl")
    return Orchestrator(
        mistake_memory=mistake_memory,
        info_seeker=info_seeker,
        answer_agent=AnswerAgent(),
        verifier=Verifier(),
        run_logger=run_logger,
    )


def cmd_run(args: argparse.Namespace) -> None:
    orchestrator = build_orchestrator()
    result = orchestrator.run_task(args.task)
    print("=== RUN SUMMARY ===")
    print(f"Task type: {result.task_type}")
    print(f"Tools called: {', '.join(result.tools_called)}")
    print(f"Snippets found: {result.snippets_count}")
    print("\n=== TRACE ===")
    for event in result.trace:
        print(event)
    print("\n=== FINAL ANSWER ===")
    print(result.draft.answer)
    if result.draft.used_snippet_ids:
        print(f"\nUsed snippet IDs: {', '.join(result.draft.used_snippet_ids)}")


def cmd_feedback(args: argparse.Namespace) -> None:
    memory = MistakeMemory(DATA_DIR / "mistakes.jsonl")
    rule = memory.add_rule(
        domain=args.domain,
        intent=args.intent,
        instruction=args.instruction,
        severity=args.severity,
    )
    print(f"Recorded rule {rule.rule_id} for {rule.domain}/{rule.intent}.")


def cmd_metrics(_: argparse.Namespace) -> None:
    runs = load_runs(DATA_DIR / "runs.jsonl")
    mistakes = load_mistakes(DATA_DIR / "mistakes.jsonl")
    summary = summarize_runs(runs)
    mistake_stats = summarize_mistakes(mistakes)
    print("=== METRICS ===")
    print(format_metrics_table(summary))
    print("\n=== MISTAKE STATS ===")
    print(format_mistake_table(mistake_stats))


def cmd_web(args: argparse.Namespace) -> None:
    run_server(args.host, args.port, DATA_DIR)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Anti-Lazy / Anti-Amnesia Orchestrator CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a task through the pipeline")
    run_parser.add_argument("task", help="Task or question to answer")
    run_parser.set_defaults(func=cmd_run)

    feedback_parser = subparsers.add_parser(
        "feedback", help="Add a mistake-memory rule"
    )
    feedback_parser.add_argument("domain", help="Domain for the rule (or *)")
    feedback_parser.add_argument("intent", help="Intent for the rule (or *)")
    feedback_parser.add_argument("instruction", help="Instruction to enforce")
    feedback_parser.add_argument(
        "--severity",
        default="medium",
        choices=["low", "medium", "high"],
        help="Rule severity",
    )
    feedback_parser.set_defaults(func=cmd_feedback)

    metrics_parser = subparsers.add_parser(
        "metrics", help="Show aggregated run metrics"
    )
    metrics_parser.set_defaults(func=cmd_metrics)

    web_parser = subparsers.add_parser("web", help="Start the web dashboard")
    web_parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind the web server"
    )
    web_parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind the web server"
    )
    web_parser.set_defaults(func=cmd_web)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
