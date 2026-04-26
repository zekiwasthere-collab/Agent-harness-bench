"""CLI interface for AgentHarnessBench."""

from pathlib import Path

import click
from rich.console import Console

from agent_harness_bench.ingest.auto import auto_ingest
from agent_harness_bench.pipeline import BenchmarkPipeline
from agent_harness_bench.report.html_report import generate_html_report
from agent_harness_bench.report.leaderboard import generate_leaderboard_json
from agent_harness_bench.report.summary import print_summary
from agent_harness_bench.report.trajectory_graph import export_trajectory_graph

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="agent-harness-bench")
def cli():
    """AgentHarnessBench - Evaluate LLM agent trajectories."""


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), default="trajectory.graph.json",
              help="Output path for canonical graph JSON")
@click.option("--format", "-f", "fmt", type=click.Choice(["auto", "jsonl", "langsmith", "opentelemetry"]),
              default="auto", help="Input format (auto-detect by default)")
def ingest(input_file: Path, output: Path, fmt: str):
    """Ingest a trajectory log file into canonical graph format."""
    console.print(f"[bold blue]Ingesting[/] {input_file} (format: {fmt})")
    trajectory = auto_ingest(input_file, fmt)
    export_trajectory_graph(trajectory, output)
    console.print(f"[bold green]Done.[/] {len(trajectory.nodes)} nodes, {len(trajectory.edges)} edges -> {output}")


@cli.command()
@click.argument("trajectory_file", type=click.Path(exists=True, path_type=Path))
@click.option("--task-type", "-t", default="code_debug",
              type=click.Choice(["code_debug", "multi_step_api", "research_synthesis", "tool_selection"]),
              help="Task type for evaluation rubric")
@click.option("--difficulty", "-d", default="medium",
              type=click.Choice(["easy", "medium", "hard"]),
              help="Expected task difficulty")
def evaluate(trajectory_file: Path, task_type: str, difficulty: str):
    """Run the 4-stage evaluation pipeline on a trajectory graph."""
    import json
    console.print(f"[bold blue]Evaluating[/] {trajectory_file}")
    data = json.loads(trajectory_file.read_text())
    from agent_harness_bench.schema import TrajectoryGraph
    trajectory = TrajectoryGraph(**data)
    pipeline = BenchmarkPipeline()
    report = pipeline.run_single(trajectory, task_type=task_type, difficulty=difficulty)
    print_summary(report)
    output_path = trajectory_file.parent / "evaluation_result.json"
    output_path.write_text(report.model_dump_json(indent=2))
    console.print(f"[bold green]Result saved to[/] {output_path}")


@cli.command()
@click.argument("result_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), default="report.html",
              help="Output HTML report path")
def report(result_file: Path, output: Path):
    """Generate HTML report from evaluation results."""
    import json
    from agent_harness_bench.schema import BenchmarkReport, TrajectoryGraph
    console.print(f"[bold blue]Generating report[/] from {result_file}")
    report_data = BenchmarkReport.model_validate_json(result_file.read_text())
    trajectory_path = result_file.parent / "trajectory.graph.json"
    trajectory = None
    if trajectory_path.exists():
        trajectory = TrajectoryGraph(**json.loads(trajectory_path.read_text()))
    generate_html_report(report_data, trajectory, output)
    console.print(f"[bold green]Report saved to[/] {output}")


@cli.command()
@click.option("--task-type", "-t", default="code_debug",
              type=click.Choice(["code_debug", "multi_step_api", "research_synthesis", "tool_selection"]))
@click.option("--difficulty", "-d", default="medium",
              type=click.Choice(["easy", "medium", "hard"]))
@click.option("--agent-name", default="test_agent", help="Agent name for simulation")
@click.option("--model", default="simulated", help="Model name for simulation")
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default=".",
              help="Output directory")
def run(task_type: str, difficulty: str, agent_name: str, model: str, output_dir: Path):
    """Full pipeline: generate task -> simulate execution -> evaluate -> report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[bold blue]Running full pipeline[/] task={task_type} difficulty={difficulty}")

    pipeline = BenchmarkPipeline()
    report = pipeline.run_simulated(task_type=task_type, difficulty=difficulty,
                                    agent_name=agent_name, model=model)

    traj_path = output_dir / "trajectory.graph.json"
    result_path = output_dir / "evaluation_result.json"
    report_path = output_dir / "report.html"

    trajectory = report.trajectory_stats.pop("_trajectory", None) or TrajectoryGraph()
    export_trajectory_graph(trajectory, traj_path)
    result_path.write_text(report.model_dump_json(indent=2))
    generate_html_report(report, trajectory, report_path)

    print_summary(report)
    console.print(f"\n[bold green]Outputs:[/]")
    console.print(f"  Trajectory: {traj_path}")
    console.print(f"  Results:    {result_path}")
    console.print(f"  Report:     {report_path}")


@cli.command()
@click.argument("results_dir", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), default="leaderboard.json",
              help="Output leaderboard JSON path")
def leaderboard(results_dir: Path, output: Path):
    """Generate leaderboard JSON from evaluation results in a directory."""
    import json
    from agent_harness_bench.schema import BenchmarkReport, LeaderboardEntry

    entries: list[LeaderboardEntry] = []
    for f in sorted(results_dir.glob("*.json")):
        try:
            report = BenchmarkReport.model_validate_json(f.read_text())
            entries.append(LeaderboardEntry(
                agent_name=report.agent_name,
                model=report.model,
                task_id=report.task_id,
                overall_score=report.evaluation.overall_score,
                process_score=report.evaluation.process_score,
                outcome_score=report.evaluation.outcome_score,
                compliance=report.evaluation.compliance.get("overall", True),
            ))
        except Exception:
            continue

    generate_leaderboard_json(entries, output)
    console.print(f"[bold green]Leaderboard[/] with {len(entries)} entries -> {output}")


if __name__ == "__main__":
    cli()
