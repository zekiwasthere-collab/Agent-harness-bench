"""Core evaluation stage with rubrics and LLM-as-judge scoring."""

from __future__ import annotations

import math
from agent_harness_bench.schema import (
    EdgeRelation,
    EvaluationResult,
    NodeType,
    TrajectoryGraph,
)


# Process rubric weights
PROCESS_WEIGHTS = {
    "tool_selection_accuracy": 0.20,
    "parameter_correctness": 0.15,
    "step_order_correctness": 0.20,
    "reasoning_coherence": 0.25,
    "efficiency": 0.10,
    "error_recovery_rate": 0.10,
}

OUTCOME_WEIGHT = 0.4
PROCESS_WEIGHT = 0.6


class RubricScorer:
    """Apply weighted rubrics to score a trajectory."""

    def score(self, trajectory: TrajectoryGraph, task: dict) -> EvaluationResult:
        """Compute all metric scores for a trajectory against a task."""
        tool_acc = self._tool_selection_accuracy(trajectory, task)
        param_corr = self._parameter_correctness(trajectory)
        step_order = self._step_order_correctness(trajectory, task)
        coherence = self._reasoning_coherence(trajectory)
        efficiency = self._efficiency(trajectory, task)
        error_recovery = self._error_recovery_rate(trajectory)
        completion = self._task_completion(trajectory, task)
        answer_corr = self._answer_correctness(trajectory, task)
        output_quality = self._final_output_quality(trajectory)

        # Weighted overall score
        process_scores = {
            "tool_selection_accuracy": tool_acc,
            "parameter_correctness": param_corr,
            "step_order_correctness": step_order,
            "reasoning_coherence": coherence,
            "efficiency": efficiency,
            "error_recovery_rate": error_recovery,
        }
        process_avg = sum(
            process_scores[k] * PROCESS_WEIGHTS[k] for k in process_scores
        ) / sum(PROCESS_WEIGHTS.values())

        outcome_avg = (answer_corr + output_quality + (1.0 if completion else 0.0)) / 3.0
        overall = PROCESS_WEIGHT * process_avg + OUTCOME_WEIGHT * outcome_avg

        return EvaluationResult(
            tool_selection_accuracy=round(tool_acc, 3),
            parameter_correctness=round(param_corr, 3),
            step_order_correctness=round(step_order, 3),
            reasoning_coherence=round(coherence, 3),
            efficiency=round(efficiency, 3),
            error_recovery_rate=round(error_recovery, 3),
            task_completion=completion,
            answer_correctness=round(answer_corr, 3),
            final_output_quality=round(output_quality, 3),
            overall_score=round(overall, 3),
        )

    def _tool_selection_accuracy(self, trajectory: TrajectoryGraph, task: dict) -> float:
        """Score how well the agent selected appropriate tools."""
        expected_tools = set(task.get("expected_tools", []))
        if not expected_tools:
            return 0.5

        used_tools = set()
        for node in trajectory.nodes:
            if node.type == NodeType.TOOL_CALL:
                tool_name = node.metadata.get("tool_name", "")
                if tool_name:
                    used_tools.add(tool_name)
                else:
                    used_tools.add(node.content.split("(")[0])

        if not used_tools:
            return 0.0

        overlap = expected_tools & used_tools
        precision = len(overlap) / len(used_tools) if used_tools else 0
        recall = len(overlap) / len(expected_tools) if expected_tools else 0

        if precision + recall == 0:
            return 0.0
        f1 = 2 * precision * recall / (precision + recall)
        return f1

    def _parameter_correctness(self, trajectory: TrajectoryGraph) -> float:
        """Score parameter correctness of tool calls (heuristic)."""
        tool_nodes = [n for n in trajectory.nodes if n.type == NodeType.TOOL_CALL]
        if not tool_nodes:
            return 0.5

        # Check that observations following tool calls aren't errors
        error_count = 0
        for node in tool_nodes:
            obs_edges = [e for e in trajectory.edges
                         if e.source == node.id and e.relation == EdgeRelation.RESPONDS_TO]
            for edge in obs_edges:
                obs_nodes = [n for n in trajectory.nodes if n.id == edge.target]
                for obs in obs_nodes:
                    if "Error" in obs.content or "failed" in obs.content:
                        error_count += 1

        error_rate = error_count / len(tool_nodes)
        return max(0.0, 1.0 - error_rate * 2)

    def _step_order_correctness(self, trajectory: TrajectoryGraph, task: dict) -> float:
        """Score whether steps were executed in a logical order."""
        expected_tools = task.get("expected_tools", [])
        if len(expected_tools) < 2:
            return 0.8

        used_sequence = []
        for node in trajectory.nodes:
            if node.type == NodeType.TOOL_CALL:
                tool_name = node.metadata.get("tool_name", node.content.split("(")[0])
                used_sequence.append(tool_name)

        if len(used_sequence) < 2:
            return 0.5

        # Compute longest common subsequence ratio
        lcs_len = self._lcs_length(expected_tools, used_sequence)
        max_len = max(len(expected_tools), len(used_sequence))
        return lcs_len / max_len if max_len > 0 else 0.0

    def _reasoning_coherence(self, trajectory: TrajectoryGraph) -> float:
        """Score reasoning coherence based on thought-tool-observation structure."""
        thought_nodes = [n for n in trajectory.nodes if n.type == NodeType.THOUGHT]
        tool_nodes = [n for n in trajectory.nodes if n.type == NodeType.TOOL_CALL]
        obs_nodes = [n for n in trajectory.nodes if n.type == NodeType.OBSERVATION]

        if not thought_nodes:
            return 0.0

        # Each thought should be followed by a tool call
        thoughts_with_tools = 0
        for thought in thought_nodes:
            has_tool = any(e.source == thought.id and e.relation == EdgeRelation.CALLS
                          for e in trajectory.edges)
            if has_tool:
                thoughts_with_tools += 1

        tool_coverage = thoughts_with_tools / len(thought_nodes) if thought_nodes else 0

        # Average confidence of thought nodes
        avg_confidence = sum(n.confidence for n in thought_nodes) / len(thought_nodes)

        # Check for uncertainty markers
        uncertain = sum(1 for n in thought_nodes if "uncertain" in n.content.lower())
        uncertainty_penalty = uncertain / len(thought_nodes) if thought_nodes else 0

        score = 0.4 * tool_coverage + 0.4 * avg_confidence + 0.2 * (1 - uncertainty_penalty)
        return max(0.0, min(1.0, score))

    def _efficiency(self, trajectory: TrajectoryGraph, task: dict) -> float:
        """Score efficiency: actual steps vs expected steps."""
        expected = task.get("expected_steps", 4)
        tool_nodes = [n for n in trajectory.nodes if n.type == NodeType.TOOL_CALL]
        actual = len(tool_nodes)

        if actual == 0:
            return 0.0
        if actual <= expected:
            return 1.0
        # Penalty grows with extra steps
        ratio = expected / actual
        return max(0.0, min(1.0, ratio))

    def _error_recovery_rate(self, trajectory: TrajectoryGraph) -> float:
        """Score how well the agent recovers from errors."""
        error_edges = [e for e in trajectory.edges if e.relation == EdgeRelation.RECOVERS_FROM]
        error_nodes = [n for n in trajectory.nodes
                       if n.type == NodeType.OBSERVATION and ("Error" in n.content or "failed" in n.content)]

        if not error_nodes:
            return 1.0  # No errors = perfect recovery

        recoveries = len(error_edges)
        return min(1.0, recoveries / len(error_nodes))

    def _task_completion(self, trajectory: TrajectoryGraph, task: dict) -> bool:
        """Determine if the task was completed (heuristic)."""
        quality = trajectory.metrics.get("quality_factor", 0.5)
        has_errors = any("Error" in n.content for n in trajectory.nodes)
        # Complete if quality is decent and no unrecovered errors at the end
        final_nodes = trajectory.nodes[-3:] if len(trajectory.nodes) >= 3 else trajectory.nodes
        final_errors = any("Error" in n.content for n in final_nodes)
        return quality >= 0.5 and not final_errors

    def _answer_correctness(self, trajectory: TrajectoryGraph, task: dict) -> float:
        """Score answer correctness (heuristic based on trajectory quality)."""
        quality = trajectory.metrics.get("quality_factor", 0.5)
        return min(1.0, quality * random_factor(0.8, 1.0))

    def _final_output_quality(self, trajectory: TrajectoryGraph) -> float:
        """Score the quality of the final output (heuristic)."""
        quality = trajectory.metrics.get("quality_factor", 0.5)
        obs_nodes = [n for n in trajectory.nodes if n.type == NodeType.OBSERVATION]
        if not obs_nodes:
            return 0.3
        last_obs = obs_nodes[-1]
        has_error = "Error" in last_obs.content or "failed" in last_obs.content
        if has_error:
            return max(0.1, quality * 0.5)
        return min(1.0, quality * random_factor(0.85, 1.0))

    @staticmethod
    def _lcs_length(seq1: list, seq2: list) -> int:
        """Compute length of longest common subsequence."""
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i - 1] == seq2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        return dp[m][n]


def random_factor(lo: float, hi: float) -> float:
    """Simple deterministic-ish factor based on hash to avoid importing random."""
    import random
    return random.uniform(lo, hi)


class LLMJudge:
    """LLM-as-judge scoring interface.

    For MVP, uses heuristic scoring based on trajectory structure.
    In production, this would call an LLM API with rubric prompts.
    """

    def judge_trajectory(self, trajectory: TrajectoryGraph, rubric: str = "default") -> float:
        """Score a trajectory using LLM judgment (heuristic for MVP)."""
        num_nodes = len(trajectory.nodes)
        num_edges = len(trajectory.edges)
        avg_confidence = sum(n.confidence for n in trajectory.nodes) / num_nodes if num_nodes else 0

        # Structural quality: good graphs have ~2x edges to nodes (thought->tool->obs)
        edge_ratio = num_edges / num_nodes if num_nodes else 0
        structural_score = min(1.0, edge_ratio / 2.0)

        # Confidence score
        conf_score = avg_confidence

        # Completeness: all tool calls have responses
        tool_nodes = [n for n in trajectory.nodes if n.type == NodeType.TOOL_CALL]
        tools_with_obs = 0
        for tn in tool_nodes:
            has_obs = any(e.source == tn.id for e in trajectory.edges)
            if has_obs:
                tools_with_obs += 1
        completeness = tools_with_obs / len(tool_nodes) if tool_nodes else 1.0

        score = 0.3 * structural_score + 0.4 * conf_score + 0.3 * completeness
        return round(min(1.0, max(0.0, score)), 3)


class EvaluationStage:
    """Orchestrates the evaluation of a trajectory against a task."""

    def __init__(self):
        self.scorer = RubricScorer()
        self.judge = LLMJudge()

    def evaluate(self, trajectory: TrajectoryGraph, task: dict) -> EvaluationResult:
        """Evaluate a trajectory and return scored results."""
        result = self.scorer.score(trajectory, task)

        # Blend in LLM judge score (30% judge, 70% rubric for MVP)
        judge_score = self.judge.judge_trajectory(trajectory)
        blended = 0.7 * result.overall_score + 0.3 * judge_score
        result.overall_score = round(blended, 3)

        return result
