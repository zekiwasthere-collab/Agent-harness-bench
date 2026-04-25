"""Rich console summary output for benchmark results."""

from __future__ import annotations

import os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from agent_harness_bench.schema import BenchmarkReport


def print_summary(report: BenchmarkReport) -> None:
    """Print a formatted summary of benchmark results to the console."""
    console = Console(force_terminal=True, legacy_windows=False)

    # Overall score card
    score = report.evaluation.overall_score
    if score >= 0.7:
        score_style = "bold green"
        emoji = "+"
    elif score >= 0.4:
        score_style = "bold yellow"
        emoji = "~"
    else:
        score_style = "bold red"
        emoji = "-"

    console.print(Panel(
        Text.from_markup(
            f"[{score_style}]{emoji} {score * 100:.1f}%[/{score_style}]  "
            f"Process: {report.evaluation.process_score * 100:.1f}%  "
            f"Outcome: {report.evaluation.outcome_score * 100:.1f}%"
        ),
        title=f"[bold]{report.agent_name}[/] / {report.model}",
        subtitle=f"{report.task_type} ({report.difficulty}) - {report.task_id}",
    ))

    # Process metrics table
    proc_table = Table(title="Process Metrics", show_header=True, header_style="bold cyan")
    proc_table.add_column("Metric", style="white")
    proc_table.add_column("Score", justify="right")
    proc_table.add_column("Bar", min_width=20)

    for label, value in [
        ("Tool Selection", report.evaluation.tool_selection_accuracy),
        ("Parameter Correctness", report.evaluation.parameter_correctness),
        ("Step Order", report.evaluation.step_order_correctness),
        ("Reasoning Coherence", report.evaluation.reasoning_coherence),
        ("Efficiency", report.evaluation.efficiency),
        ("Error Recovery", report.evaluation.error_recovery_rate),
    ]:
        bar_filled = int(value * 20)
        bar = "#" * bar_filled + "-" * (20 - bar_filled)
        style = "green" if value >= 0.7 else ("yellow" if value >= 0.4 else "red")
        proc_table.add_row(label, f"[{style}]{value * 100:.1f}%[/{style}]", f"[{style}]{bar}[/{style}]")

    console.print(proc_table)

    # Outcome metrics table
    out_table = Table(title="Outcome Metrics", show_header=True, header_style="bold yellow")
    out_table.add_column("Metric", style="white")
    out_table.add_column("Score", justify="right")

    completion_str = "[green]YES[/]" if report.evaluation.task_completion else "[red]NO[/]"
    out_table.add_row("Task Completion", completion_str)
    out_table.add_row("Answer Correctness", f"{report.evaluation.answer_correctness * 100:.1f}%")
    out_table.add_row("Output Quality", f"{report.evaluation.final_output_quality * 100:.1f}%")

    console.print(out_table)

    # Compliance
    if report.compliance:
        comp_table = Table(title="Compliance Checks", show_header=True, header_style="bold magenta")
        comp_table.add_column("Check", style="white")
        comp_table.add_column("Status", justify="center")

        for name, result in report.compliance.items():
            if name == "overall":
                continue
            if isinstance(result, dict):
                status = "[green]PASS[/]" if result.get("pass", True) else "[red]FAIL[/]"
                comp_table.add_row(name.replace("_", " ").title(), status)

        overall = report.compliance.get("overall", True)
        comp_table.add_row("[bold]Overall[/]", "[bold green]PASS[/]" if overall else "[bold red]FAIL[/]")
        console.print(comp_table)

    # Trajectory stats
    if report.trajectory_stats:
        stats = {k: v for k, v in report.trajectory_stats.items() if not k.startswith("_")}
        console.print(f"\n[dim]Trajectory: {stats.get('node_count', 0)} nodes, "
                      f"{stats.get('edge_count', 0)} edges, "
                      f"{stats.get('tool_call_count', 0)} tool calls[/]")
