"""4-stage benchmark pipeline orchestrator."""

from __future__ import annotations

from agent_harness_bench.schema import (
    BenchmarkReport,
    EvaluationResult,
    LeaderboardEntry,
    TrajectoryGraph,
)
from agent_harness_bench.evaluate.generation import GenerationStage
from agent_harness_bench.evaluate.execution import ExecutionStage
from agent_harness_bench.evaluate.evaluation import EvaluationStage
from agent_harness_bench.evaluate.compliance import ComplianceStage


class BenchmarkPipeline:
    """Orchestrates the full 4-stage benchmark pipeline.

    Stages: Generation -> Execution -> Evaluation -> Compliance
    """

    def __init__(self):
        self.generation = GenerationStage()
        self.execution = ExecutionStage()
        self.evaluation = EvaluationStage()
        self.compliance = ComplianceStage()

    def run_simulated(self, task_type: str = "code_debug", difficulty: str = "medium",
                      agent_name: str = "test_agent", model: str = "simulated") -> BenchmarkReport:
        """Run the full pipeline with simulated execution (MVP mode)."""
        # Stage 1: Generate task
        tasks = self.generation.generate(task_type, difficulty, count=1)
        task = tasks[0]

        # Stage 2: Simulate execution
        trajectory = self.execution.execute_simulated(task, {"name": agent_name, "model": model})

        # Stage 3: Evaluate
        eval_result = self.evaluation.evaluate(trajectory, task)

        # Stage 4: Compliance
        compliance_result = self.compliance.check(trajectory)

        # Merge compliance into eval result
        eval_result.compliance = compliance_result

        return BenchmarkReport(
            agent_name=agent_name,
            model=model,
            task_id=task["task_id"],
            task_type=task_type,
            difficulty=difficulty,
            evaluation=eval_result,
            compliance=compliance_result,
            trajectory_stats={
                "node_count": len(trajectory.nodes),
                "edge_count": len(trajectory.edges),
                "thought_count": len([n for n in trajectory.nodes if n.type.value == "thought"]),
                "tool_call_count": len([n for n in trajectory.nodes if n.type.value == "tool_call"]),
                "observation_count": len([n for n in trajectory.nodes if n.type.value == "observation"]),
                "_trajectory": trajectory,
            },
        )

    def run_single(self, trajectory: TrajectoryGraph, task_type: str = "code_debug",
                   difficulty: str = "medium") -> BenchmarkReport:
        """Run evaluation + compliance on an existing trajectory."""
        # Generate a matching task for the rubric
        tasks = self.generation.generate(task_type, difficulty, count=1)
        task = tasks[0]

        # Override task_id from trajectory metadata if available
        task["task_id"] = trajectory.metadata.get("task_id", task["task_id"])

        # Evaluate
        eval_result = self.evaluation.evaluate(trajectory, task)

        # Compliance
        compliance_result = self.compliance.check(trajectory)
        eval_result.compliance = compliance_result

        return BenchmarkReport(
            agent_name=trajectory.metadata.get("agent_name", "unknown"),
            model=trajectory.metadata.get("model", "unknown"),
            task_id=task["task_id"],
            task_type=task_type,
            difficulty=difficulty,
            evaluation=eval_result,
            compliance=compliance_result,
            trajectory_stats={
                "node_count": len(trajectory.nodes),
                "edge_count": len(trajectory.edges),
                "thought_count": len([n for n in trajectory.nodes if n.type.value == "thought"]),
                "tool_call_count": len([n for n in trajectory.nodes if n.type.value == "tool_call"]),
                "observation_count": len([n for n in trajectory.nodes if n.type.value == "observation"]),
                "_trajectory": trajectory,
            },
        )

    def run_batch(self, task_type: str, difficulty: str,
                  agent_configs: list[dict]) -> list[BenchmarkReport]:
        """Run the pipeline for multiple agents and collect results."""
        reports = []
        for config in agent_configs:
            report = self.run_simulated(
                task_type=task_type,
                difficulty=difficulty,
                agent_name=config.get("name", "unknown"),
                model=config.get("model", "unknown"),
            )
            reports.append(report)
        return reports

    @staticmethod
    def generate_leaderboard(reports: list[BenchmarkReport]) -> list[LeaderboardEntry]:
        """Generate a sorted leaderboard from benchmark reports."""
        entries = []
        for report in reports:
            entries.append(LeaderboardEntry(
                agent_name=report.agent_name,
                model=report.model,
                task_id=report.task_id,
                overall_score=report.evaluation.overall_score,
                process_score=report.evaluation.process_score,
                outcome_score=report.evaluation.outcome_score,
                compliance=report.evaluation.compliance.get("overall", True),
            ))

        # Sort by overall_score descending
        entries.sort(key=lambda e: e.overall_score, reverse=True)

        # Assign ranks (handle ties)
        for i, entry in enumerate(entries):
            if i == 0:
                entry.rank = 1
            elif entry.overall_score == entries[i - 1].overall_score:
                entry.rank = entries[i - 1].rank
            else:
                entry.rank = i + 1

        return entries
