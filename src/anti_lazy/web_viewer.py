from __future__ import annotations

import json
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Iterable

from .metrics import (
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
            if self.path.startswith("/api/runs"):
                self._send_json(load_runs(data_dir / "runs.jsonl"))
                return
            if self.path.startswith("/api/mistakes"):
                self._send_json(load_mistakes(data_dir / "mistakes.jsonl"))
                return
            if self.path.startswith("/api/summary"):
                runs = load_runs(data_dir / "runs.jsonl")
                mistakes = load_mistakes(data_dir / "mistakes.jsonl")
                summary = summarize_runs(runs)
                mistake_stats = summarize_mistakes(mistakes)
                payload = {
                    "summary": asdict(summary),
                    "mistakes": asdict(mistake_stats),
                }
                self._send_json(payload)
                return
            if self.path not in ("/", "/runs", "/mistakes"):
                self.send_error(404, "Not Found")
                return
            content = render_dashboard()
            encoded = content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_json(self, payload) -> None:
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    return DashboardHandler


def render_dashboard() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Anti-Lazy Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    :root {
      --bg: #f4f3ef;
      --ink: #151515;
      --muted: #6b6b6b;
      --card: #ffffff;
      --accent: #ff5c36;
      --accent-2: #1e3a8a;
      --border: #e5e1d8;
      --shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
      --radius: 16px;
      --mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      --sans: "Space Grotesk", "Segoe UI", system-ui, -apple-system, sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: var(--sans);
      background: radial-gradient(1200px 800px at 10% -10%, #ffe7df 0%, transparent 60%),
                  radial-gradient(1200px 800px at 90% -20%, #dbeafe 0%, transparent 55%),
                  var(--bg);
      color: var(--ink);
    }
    header {
      padding: 28px 6vw 12px 6vw;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
    }
    header h1 {
      font-size: clamp(24px, 3vw, 36px);
      margin: 0;
      letter-spacing: -0.02em;
    }
    header p {
      margin: 6px 0 0 0;
      color: var(--muted);
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: #111827;
      color: #fff;
      padding: 8px 14px;
      border-radius: 999px;
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    main {
      padding: 0 6vw 8vw 6vw;
      display: grid;
      gap: 20px;
    }
    .grid {
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }
    .card {
      background: var(--card);
      border-radius: var(--radius);
      padding: 18px;
      box-shadow: var(--shadow);
      border: 1px solid var(--border);
    }
    .card h2 {
      margin: 0 0 10px 0;
      font-size: 16px;
      letter-spacing: 0.02em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .stat {
      font-size: 26px;
      font-weight: 600;
    }
    .stat small {
      display: block;
      font-size: 12px;
      color: var(--muted);
      margin-top: 6px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }
    .filters {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
    select {
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid var(--border);
      font-family: var(--sans);
      background: #fff;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }
    th, td {
      text-align: left;
      padding: 10px;
      border-bottom: 1px solid var(--border);
    }
    tr:hover { background: #f8f5ef; cursor: pointer; }
    .pill {
      display: inline-flex;
      padding: 4px 10px;
      border-radius: 999px;
      background: #f1f5f9;
      font-size: 12px;
      color: #0f172a;
    }
    .accent { color: var(--accent); font-weight: 600; }
    .drawer {
      position: fixed;
      top: 0;
      right: 0;
      width: min(420px, 92vw);
      height: 100vh;
      background: #0f172a;
      color: #e2e8f0;
      padding: 20px;
      transform: translateX(100%);
      transition: transform 0.25s ease;
      box-shadow: -20px 0 40px rgba(15, 23, 42, 0.4);
      overflow-y: auto;
      z-index: 10;
    }
    .drawer.open { transform: translateX(0); }
    .drawer pre {
      white-space: pre-wrap;
      word-break: break-word;
      font-family: var(--mono);
      background: #111827;
      padding: 12px;
      border-radius: 12px;
      font-size: 12px;
    }
    .drawer h3 { margin-top: 0; }
    .chart {
      display: grid;
      gap: 8px;
    }
    .bar {
      height: 10px;
      background: linear-gradient(90deg, #ff5c36, #f59e0b);
      border-radius: 999px;
    }
    .muted { color: var(--muted); }
    @media (max-width: 780px) {
      header { flex-direction: column; align-items: flex-start; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <div class="badge">Anti-Lazy / Anti-Amnesia</div>
      <h1>Run Intelligence Dashboard</h1>
      <p>Grounding, rules, and verification in one live trace.</p>
    </div>
    <div class="card" style="min-width: 200px;">
      <div class="stat" id="runsCount">0</div>
      <small class="muted">Total runs</small>
    </div>
  </header>
  <main>
    <section class="grid" id="metricsGrid"></section>
    <section class="card">
      <h2>Filters</h2>
      <div class="filters">
        <select id="filterTaskType"></select>
        <select id="filterRule"></select>
      </div>
    </section>
    <section class="card">
      <h2>Recent Runs</h2>
      <div class="muted">Click a row to open the trace.</div>
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Task</th>
            <th>Type</th>
            <th>Snippets</th>
            <th>Coverage</th>
            <th>Rules</th>
          </tr>
        </thead>
        <tbody id="runsTable"></tbody>
      </table>
    </section>
    <section class="card">
      <h2>Mistake Rules</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Domain</th>
            <th>Intent</th>
            <th>Severity</th>
          </tr>
        </thead>
        <tbody id="mistakesTable"></tbody>
      </table>
    </section>
  </main>
  <aside class="drawer" id="drawer">
    <h3>Run Trace</h3>
    <div id="drawerMeta" class="muted"></div>
    <pre id="drawerTrace">Select a run to view details.</pre>
  </aside>
  <script>
    const state = { runs: [], mistakes: [], summary: null };

    const $ = (id) => document.getElementById(id);

    const formatNumber = (value, digits = 2) =>
      Number(value).toFixed(digits).replace(/\.00$/, "");

    const renderMetrics = () => {
      if (!state.summary) return;
      const s = state.summary.summary;
      $("runsCount").textContent = s.runs_count;
      const cards = [
        { label: "Avg tool coverage", value: formatNumber(s.average_tool_coverage) },
        { label: "Avg snippets", value: formatNumber(s.average_snippets) },
        { label: "Used snippet IDs", value: s.total_used_snippets },
        { label: "Rules applied", value: s.rules_applied_count },
      ];
      $("metricsGrid").innerHTML = cards.map(card => `
        <div class="card">
          <h2>${card.label}</h2>
          <div class="stat">${card.value}<small>Rolling total</small></div>
        </div>
      `).join("");
    };

    const renderFilters = () => {
      const taskTypes = ["all", ...new Set(state.runs.map(r => r.task_type || "general"))];
      const rules = ["all", ...new Set(state.runs.flatMap(r => r.rules_applied || []))];
      $("filterTaskType").innerHTML = taskTypes.map(t => `<option value="${t}">${t}</option>`).join("");
      $("filterRule").innerHTML = rules.map(r => `<option value="${r}">${r}</option>`).join("");
    };

    const getFilteredRuns = () => {
      const type = $("filterTaskType").value;
      const rule = $("filterRule").value;
      return state.runs.filter(run => {
        if (type !== "all" && run.task_type !== type) return false;
        if (rule !== "all" && !(run.rules_applied || []).includes(rule)) return false;
        return true;
      });
    };

    const renderRuns = () => {
      const rows = getFilteredRuns().slice(-30).reverse().map(run => {
        const rules = (run.rules_applied || []).join(", ") || "-";
        return `
          <tr data-run='${JSON.stringify(run).replace(/'/g, "&#39;")}' >
            <td>${run.timestamp || ""}</td>
            <td>${run.task || ""}</td>
            <td><span class="pill">${run.task_type || "general"}</span></td>
            <td>${run.snippets_count ?? 0}</td>
            <td>${formatNumber(run.tool_coverage ?? 0)}</td>
            <td>${rules}</td>
          </tr>
        `;
      }).join("");
      $("runsTable").innerHTML = rows || `<tr><td colspan="6">No runs yet.</td></tr>`;
      Array.from(document.querySelectorAll("#runsTable tr")).forEach(row => {
        row.addEventListener("click", () => {
          const payload = JSON.parse(row.dataset.run);
          $("drawerMeta").innerHTML = `<div class="accent">${payload.task_type}</div><div>${payload.task}</div>`;
          $("drawerTrace").textContent = JSON.stringify({
            trace: payload.trace || [],
            attempts: payload.attempts || [],
            verification: payload.verification || {}
          }, null, 2);
          $("drawer").classList.add("open");
        });
      });
    };

    const renderMistakes = () => {
      const rows = state.mistakes.slice(-30).reverse().map(m => `
        <tr>
          <td>${m.rule_id || ""}</td>
          <td>${m.domain || ""}</td>
          <td>${m.intent || ""}</td>
          <td>${m.severity || ""}</td>
        </tr>
      `).join("");
      $("mistakesTable").innerHTML = rows || `<tr><td colspan="4">No rules yet.</td></tr>`;
    };

    const loadData = async () => {
      const [runs, mistakes, summary] = await Promise.all([
        fetch("/api/runs").then(r => r.json()),
        fetch("/api/mistakes").then(r => r.json()),
        fetch("/api/summary").then(r => r.json())
      ]);
      state.runs = runs || [];
      state.mistakes = mistakes || [];
      state.summary = summary || null;
      renderMetrics();
      renderFilters();
      renderRuns();
      renderMistakes();
    };

    $("filterTaskType").addEventListener("change", renderRuns);
    $("filterRule").addEventListener("change", renderRuns);
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") $("drawer").classList.remove("open");
    });

    loadData();
  </script>
</body>
</html>
"""
