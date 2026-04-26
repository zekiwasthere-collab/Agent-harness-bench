"""Parse LangSmith export format into canonical TrajectoryGraph format.

LangSmith runs.json contains a list of run objects with:
id, name, run_type (llm/tool/chain), inputs, outputs, parent_run_id,
start_time, end_time.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from agent_harness_bench.schema import (
    EdgeRelation,
    NodeType,
    TrajectoryEdge,
    TrajectoryGraph,
    TrajectoryNode,
)


def parse_langsmith(path: Path) -> TrajectoryGraph:
    """Parse a LangSmith runs export into a TrajectoryGraph."""
    data = json.loads(path.read_text(encoding="utf-8"))

    runs = data if isinstance(data, list) else data.get("runs", data.get("data", []))

    nodes: list[TrajectoryNode] = []
    edges: list[TrajectoryEdge] = []
    id_map: dict[str, str] = {}

    for run in runs:
        run_id = run.get("id", uuid4().hex[:12])
        run_type = run.get("run_type", "chain")
        name = run.get("name", "unknown")
        parent_id = run.get("parent_run_id")
        inputs = run.get("inputs", {})
        outputs = run.get("outputs", {})
        start_time = run.get("start_time")
        end_time = run.get("end_time")

        if run_type == "llm":
            node_type = NodeType.THOUGHT
            content = _extract_llm_content(inputs, outputs)
        elif run_type == "tool":
            node_type = NodeType.TOOL_CALL
            content = _extract_tool_content(inputs, outputs, name)
        else:
            node_type = NodeType.ACTION
            content = f"[{name}] {_serialize(inputs)[:1000]}"

        node_id = uuid4().hex[:12]
        id_map[run_id] = node_id

        node = TrajectoryNode(
            id=node_id,
            type=node_type,
            content=content,
            timestamp=start_time,
            metadata={
                "run_id": run_id,
                "run_type": run_type,
                "name": name,
                "duration_ms": _duration_ms(start_time, end_time),
            },
        )
        nodes.append(node)

        if parent_id and parent_id in id_map:
            relation = EdgeRelation.LEADS_TO
            if run_type == "tool":
                relation = EdgeRelation.CALLS
            edges.append(TrajectoryEdge(
                source=id_map[parent_id], target=node_id,
                relation=relation,
            ))

    return TrajectoryGraph(
        nodes=nodes,
        edges=edges,
        metadata={"source": str(path), "format": "langsmith"},
    )


def _extract_llm_content(inputs: dict, outputs: dict) -> str:
    """Extract readable content from an LLM run."""
    if outputs and isinstance(outputs, dict):
        generations = outputs.get("generations", [])
        if generations and isinstance(generations, list):
            for gen in generations:
                if isinstance(gen, list):
                    for g in gen:
                        text = g.get("text", "")
                        if text:
                            return text[:2000]
                text = gen.get("text", "") if isinstance(gen, dict) else ""
                if text:
                    return text[:2000]
    if inputs and isinstance(inputs, dict):
        messages = inputs.get("messages", [])
        if messages and isinstance(messages, list):
            last = messages[-1] if messages else {}
            if isinstance(last, dict):
                return last.get("content", str(last))[:2000]
            return str(last)[:2000]
    return str(outputs)[:500] if outputs else ""


def _extract_tool_content(inputs: dict, outputs: dict, name: str) -> str:
    """Extract tool call content."""
    input_str = _serialize(inputs)[:500]
    output_str = _serialize(outputs)[:500]
    return f"{name}({input_str}) -> {output_str}"


def _serialize(obj: dict) -> str:
    """Safely serialize a dict to string."""
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return str(obj)


def _duration_ms(start: str | None, end: str | None) -> float | None:
    """Calculate duration in milliseconds between ISO timestamps."""
    if not start or not end:
        return None
    from datetime import datetime
    try:
        s = datetime.fromisoformat(start.replace("Z", "+00:00"))
        e = datetime.fromisoformat(end.replace("Z", "+00:00"))
        return (e - s).total_seconds() * 1000
    except (ValueError, AttributeError):
        return None
