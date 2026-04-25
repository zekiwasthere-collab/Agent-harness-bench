"""Canonical data models for AgentHarnessBench."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    THOUGHT = "thought"
    TOOL_CALL = "tool_call"
    OBSERVATION = "observation"
    ACTION = "action"


class EdgeRelation(str, Enum):
    LEADS_TO = "leads_to"
    CALLS = "calls"
    RESPONDS_TO = "responds_to"
    REFERENCES = "references"
    RECOVERS_FROM = "recovers_from"


class Confidence(str, Enum):
    EXTRACTED = "EXTRACTED"
    INFERRED = "INFERRED"
    AMBIGUOUS = "AMBIGUOUS"


class TrajectoryNode(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    type: NodeType
    content: str
    timestamp: str | None = None
    confidence: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrajectoryEdge(BaseModel):
    source: str
    target: str
    relation: EdgeRelation
    confidence_score: float = 1.0
    weight: float = 1.0


class TrajectoryGraph(BaseModel):
    nodes: list[TrajectoryNode] = Field(default_factory=list)
    edges: list[TrajectoryEdge] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=lambda: {
        "agent_name": "unknown",
        "model": "unknown",
        "task_id": "unknown",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


class EvaluationResult(BaseModel):
    tool_selection_accuracy: float = 0.0
    parameter_correctness: float = 0.0
    step_order_correctness: float = 0.0
    reasoning_coherence: float = 0.0
    efficiency: float = 0.0
    error_recovery_rate: float = 0.0
    task_completion: bool = False
    answer_correctness: float = 0.0
    final_output_quality: float = 0.0
    overall_score: float = 0.0
    compliance: dict[str, Any] = Field(default_factory=dict)

    @property
    def process_score(self) -> float:
        scores = [
            self.tool_selection_accuracy,
            self.parameter_correctness,
            self.step_order_correctness,
            self.reasoning_coherence,
            self.efficiency,
            self.error_recovery_rate,
        ]
        return sum(scores) / len(scores) if scores else 0.0

    @property
    def outcome_score(self) -> float:
        scores = [self.answer_correctness, self.final_output_quality]
        if self.task_completion:
            scores.append(1.0)
        else:
            scores.append(0.0)
        return sum(scores) / len(scores) if scores else 0.0


class LeaderboardEntry(BaseModel):
    agent_name: str
    model: str
    task_id: str
    overall_score: float
    process_score: float
    outcome_score: float
    compliance: bool = True
    rank: int = 0


class BenchmarkReport(BaseModel):
    agent_name: str = "unknown"
    model: str = "unknown"
    task_id: str = "unknown"
    task_type: str = "unknown"
    difficulty: str = "medium"
    evaluation: EvaluationResult = Field(default_factory=EvaluationResult)
    compliance: dict[str, Any] = Field(default_factory=dict)
    trajectory_stats: dict[str, Any] = Field(default_factory=dict)
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
