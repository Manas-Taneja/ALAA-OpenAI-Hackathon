from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Iterable

from .metrics import (
    format_metrics_table,
    format_mistake_table,
    load_mistakes,
    load_runs,
    summarize_mistakes,
    summarize_runs,
)


def run_server(host: str, port: int, data_dir: Path) -> None:
    server = HTTPServer((host, port), _make_handler(data_dir))
    print(f"Serving dashboard at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def _make_handler(data_dir: Path):
    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path not in ("/", "/runs", "/mistakes"):
                self.send_error(404, "Not Found")
                return
            runs = load_runs(data_dir / "runs.jsonl")
            mistakes = load_mistakes(data_dir / "mistakes.jsonl")
            summary = summarize_runs(runs)
            mistake_stats = summarize_mistakes(mistakes)
            content = render_dashboard(runs, mistakes, summary, mistake_stats)
            encoded = content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    return DashboardHandler


def render_dashboard(
    runs: Iterable[dict],
    mistakes: Iterable[dict],
    summary,
    mistake_stats,
) -> str:
    runs_list = list(runs)
    mistakes_list = list(mistakes)
    metrics_table = format_metrics_table(summary)
    mistakes_table = format_mistake_table(mistake_stats)
    run_rows = "\n".join(_render_run_row(run) for run in runs_list[-20:][::-1])
    mistake_rows = "\n".join(
        _render_mistake_row(mistake) for mistake in mistakes_list[-20:][::-1]
    )
    chart = render_mistake_chart(mistake_stats.by_severity)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Anti-Lazy Dashboard</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 24px;
      background: #f6f7fb;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .card {{
      background: white;
      padding: 16px;
      border-radius: 8px;
      margin-top: 16px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }}
    pre {{
      background: #0f172a;
      color: #e2e8f0;
      padding: 12px;
      border-radius: 6px;
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
    }}
    th, td {{
      text-align: left;
      padding: 8px;
      border-bottom: 1px solid #e2e8f0;
      font-size: 14px;
    }}
    .badge {{
      background: #e2e8f0;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Anti-Lazy / Anti-Amnesia Dashboard</h1>
    <span class="badge">Runs: {summary.runs_count}</span>
  </header>
  <section class="card">
    <h2>Metrics Table</h2>
    <pre>{metrics_table}</pre>
  </section>
  <section class="card">
    <h2>Mistake Statistics</h2>
    <pre>{mistakes_table}</pre>
    {chart}
  </section>
  <section class="card">
    <h2>Recent Runs</h2>
    <table>
      <thead>
        <tr>
          <th>Timestamp</th>
          <th>Task</th>
          <th>Snippets</th>
          <th>Tool coverage</th>
          <th>Rules applied</th>
        </tr>
      </thead>
      <tbody>
        {run_rows if run_rows else "<tr><td colspan='5'>No runs yet.</td></tr>"}
      </tbody>
    </table>
  </section>
  <section class="card">
    <h2>Recent Mistake Rules</h2>
    <table>
      <thead>
        <tr>
          <th>Rule ID</th>
          <th>Domain</th>
          <th>Intent</th>
          <th>Severity</th>
        </tr>
      </thead>
      <tbody>
        {mistake_rows if mistake_rows else "<tr><td colspan='4'>No rules yet.</td></tr>"}
      </tbody>
    </table>
  </section>
</body>
</html>
"""


def _render_run_row(run: dict) -> str:
    timestamp = run.get("timestamp", "")
    task = _escape(run.get("task", ""))
    snippets = run.get("snippets_count", 0)
    coverage = run.get("tool_coverage", 0.0)
    rules = ", ".join(run.get("rules_applied", [])) or "-"
    return (
        "<tr>"
        f"<td>{timestamp}</td>"
        f"<td>{task}</td>"
        f"<td>{snippets}</td>"
        f"<td>{coverage:.2f}</td>"
        f"<td>{rules}</td>"
        "</tr>"
    )


def _render_mistake_row(mistake: dict) -> str:
    return (
        "<tr>"
        f"<td>{_escape(mistake.get('rule_id', ''))}</td>"
        f"<td>{_escape(mistake.get('domain', ''))}</td>"
        f"<td>{_escape(mistake.get('intent', ''))}</td>"
        f"<td>{_escape(mistake.get('severity', ''))}</td>"
        "</tr>"
    )


def render_mistake_chart(by_severity: dict[str, int]) -> str:
    if not by_severity:
        return "<p>No mistake data to visualize.</p>"
    max_value = max(by_severity.values())
    bars = []
    for idx, (severity, count) in enumerate(sorted(by_severity.items())):
        width = 480 * (count / max_value)
        y = 20 + idx * 30
        bars.append(
            f"<rect x='120' y='{y}' width='{width:.0f}' height='18' fill='#38bdf8' />"
            f"<text x='10' y='{y + 14}' font-size='12'>{severity}</text>"
            f"<text x='{130 + width:.0f}' y='{y + 14}' font-size='12'>{count}</text>"
        )
    svg_height = 40 + len(by_severity) * 30
    return (
        f"<svg width='640' height='{svg_height}' role='img' aria-label='Mistake severity chart'>"
        + "".join(bars)
        + "</svg>"
    )


def _escape(value: str) -> str:
    return json.dumps(value)[1:-1]
