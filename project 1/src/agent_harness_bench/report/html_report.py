"""Generate interactive HTML report with dark dashboard theme."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Template

from agent_harness_bench.schema import BenchmarkReport, NodeType, TrajectoryGraph

HTML_TEMPLATE = Template("""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AgentHarnessBench Report</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #0d1117; color: #c9d1d9; padding: 24px; }
.container { max-width: 960px; margin: 0 auto; }
h1 { color: #58a6ff; font-size: 1.8em; margin-bottom: 8px; }
h2 { color: #8b949e; font-size: 1.2em; font-weight: normal; margin-bottom: 24px; }
h3 { color: #c9d1d9; margin: 20px 0 12px; font-size: 1.1em; }
.card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 16px; }
.score-big { font-size: 3em; font-weight: 700; }
.score-pass { color: #3fb950; }
.score-fail { color: #f85149; }
.score-mid { color: #d29922; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.metric { background: #0d1117; border: 1px solid #21262d; border-radius: 6px; padding: 14px; }
.metric-label { color: #8b949e; font-size: 0.85em; margin-bottom: 4px; }
.metric-value { font-size: 1.4em; font-weight: 600; }
.bar-track { background: #21262d; border-radius: 4px; height: 8px; margin-top: 6px; }
.bar-fill { height: 8px; border-radius: 4px; transition: width 0.3s; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; font-weight: 600; }
.badge-pass { background: #1b3a1b; color: #3fb950; }
.badge-fail { background: #3d1414; color: #f85149; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid #21262d; }
th { color: #8b949e; font-size: 0.85em; font-weight: 600; }
.timeline { display: flex; flex-wrap: wrap; gap: 4px; align-items: center; padding: 12px 0; }
.tl-node { padding: 6px 10px; border-radius: 6px; font-size: 0.8em; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tl-thought { background: #1f3a5f; color: #58a6ff; border: 1px solid #2a5a8f; }
.tl-tool { background: #3b2e1f; color: #d29922; border: 1px solid #5a4422; }
.tl-obs { background: #1b3a1b; color: #3fb950; border: 1px solid #2a5a2a; }
.tl-arrow { color: #484f58; font-size: 1.2em; }
.footer { margin-top: 32px; text-align: center; color: #484f58; font-size: 0.8em; }
</style>
</head>
<body>
<div class="container">
  <h1>AgentHarnessBench Report</h1>
  <h2>{{ report.agent_name }} / {{ report.model }} &mdash; {{ report.task_type }} ({{ report.difficulty }})</h2>

  <div class="card">
    <div class="grid">
      <div>
        <div class="metric-label">Overall Score</div>
        <div class="score-big {{ score_class }}">{{ "%.1f"|format(report.evaluation.overall_score * 100) }}</div>
      </div>
      <div>
        <div class="metric-label">Process Score</div>
        <div class="metric-value" style="color:#58a6ff">{{ "%.1f"|format(report.evaluation.process_score * 100) }}</div>
      </div>
      <div>
        <div class="metric-label">Outcome Score</div>
        <div class="metric-value" style="color:#d29922">{{ "%.1f"|format(report.evaluation.outcome_score * 100) }}</div>
      </div>
      <div>
        <div class="metric-label">Compliance</div>
        <div><span class="badge {{ 'badge-pass' if compliance_overall else 'badge-fail' }}">{{ 'PASS' if compliance_overall else 'FAIL' }}</span></div>
      </div>
    </div>
  </div>

  <h3>Process Metrics</h3>
  <div class="grid">
    {% for m in process_metrics %}
    <div class="metric">
      <div class="metric-label">{{ m.label }}</div>
      <div class="metric-value">{{ "%.1f"|format(m.value * 100) }}</div>
      <div class="bar-track"><div class="bar-fill" style="width:{{ m.value * 100 }}%;background:{{ m.color }}"></div></div>
    </div>
    {% endfor %}
  </div>

  <h3>Outcome Metrics</h3>
  <div class="grid">
    {% for m in outcome_metrics %}
    <div class="metric">
      <div class="metric-label">{{ m.label }}</div>
      <div class="metric-value">{{ "%.1f"|format(m.value * 100) }}</div>
      <div class="bar-track"><div class="bar-fill" style="width:{{ m.value * 100 }}%;background:{{ m.color }}"></div></div>
    </div>
    {% endfor %}
  </div>

  <h3>Compliance Checks</h3>
  <div class="card">
    <table>
      <tr><th>Check</th><th>Status</th><th>Details</th></tr>
      {% for name, result, details in compliance_items %}
      <tr>
        <td>{{ name }}</td>
        <td><span class="badge {{ 'badge-pass' if result.pass else 'badge-fail' }}">{{ 'PASS' if result.pass else 'FAIL' }}</span></td>
        <td style="color:#8b949e;font-size:0.85em">{{ result.details }}</td>
      </tr>
      {% endfor %}
    </table>
  </div>

  {% if trajectory %}
  <h3>Trajectory Timeline</h3>
  <div class="card">
    <div class="timeline">
      {% for node in timeline_nodes %}
        {% if node.type == 'thought' %}
          <div class="tl-node tl-thought" title="{{ node.content }}">{{ node.content[:40] }}</div>
        {% elif node.type == 'tool_call' %}
          <span class="tl-arrow">&rarr;</span>
          <div class="tl-node tl-tool" title="{{ node.content }}">{{ node.content[:30] }}</div>
        {% elif node.type == 'observation' %}
          <span class="tl-arrow">&rarr;</span>
          <div class="tl-node tl-obs" title="{{ node.content }}">{{ node.content[:30] }}</div>
        {% endif %}
      {% endfor %}
    </div>
  </div>
  {% endif %}

  <div class="footer">
    AgentHarnessBench v0.1.0 &mdash; Generated {{ report.generated_at[:19] }}
  </div>
</div>
</body>
</html>
""")


def generate_html_report(report: BenchmarkReport, trajectory: TrajectoryGraph | None,
                         output_path: Path) -> Path:
    """Generate an interactive HTML report."""
    output_path = Path(output_path)

    # Classify overall score
    score = report.evaluation.overall_score
    if score >= 0.7:
        score_class = "score-pass"
    elif score >= 0.4:
        score_class = "score-mid"
    else:
        score_class = "score-fail"

    # Process metrics for template
    process_metrics = [
        {"label": "Tool Selection", "value": report.evaluation.tool_selection_accuracy, "color": "#58a6ff"},
        {"label": "Parameter Correctness", "value": report.evaluation.parameter_correctness, "color": "#58a6ff"},
        {"label": "Step Order", "value": report.evaluation.step_order_correctness, "color": "#58a6ff"},
        {"label": "Reasoning Coherence", "value": report.evaluation.reasoning_coherence, "color": "#58a6ff"},
        {"label": "Efficiency", "value": report.evaluation.efficiency, "color": "#58a6ff"},
        {"label": "Error Recovery", "value": report.evaluation.error_recovery_rate, "color": "#58a6ff"},
    ]

    outcome_metrics = [
        {"label": "Task Completion", "value": 1.0 if report.evaluation.task_completion else 0.0, "color": "#d29922"},
        {"label": "Answer Correctness", "value": report.evaluation.answer_correctness, "color": "#d29922"},
        {"label": "Output Quality", "value": report.evaluation.final_output_quality, "color": "#d29922"},
    ]

    # Compliance items
    compliance_items = []
    compliance_overall = report.compliance.get("overall", True)
    for name, result in report.compliance.items():
        if name == "overall":
            continue
        if isinstance(result, dict):
            details = "; ".join(f"{k}={v}" for k, v in result.items() if k != "pass")
            compliance_items.append((name.replace("_", " ").title(), result, details))

    # Timeline nodes (limit to 20 for readability)
    timeline_nodes = []
    if trajectory:
        for node in trajectory.nodes[:20]:
            timeline_nodes.append({"type": node.type.value, "content": node.content})

    html = HTML_TEMPLATE.render(
        report=report,
        score_class=score_class,
        process_metrics=process_metrics,
        outcome_metrics=outcome_metrics,
        compliance_items=compliance_items,
        compliance_overall=compliance_overall,
        trajectory=trajectory,
        timeline_nodes=timeline_nodes,
    )

    output_path.write_text(html, encoding="utf-8")
    return output_path
