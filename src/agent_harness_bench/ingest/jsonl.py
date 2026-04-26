"""Parse JSONL trajectory logs into canonical TrajectoryGraph format.

Each line is a JSON object with: role (assistant/tool/system), content,
optional tool_calls, and timestamp.
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


def parse_jsonl(path: Path) -> TrajectoryGraph:
    """Parse a JSONL file into a TrajectoryGraph."""
    nodes: list[TrajectoryNode] = []
    edges: list[TrajectoryEdge] = []
    last_thought_id: str | None = None
    last_tool_call_id: str | None = None

    for line_num, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        role = entry.get("role", "")
        content = entry.get("content", "")
        timestamp = entry.get("timestamp")
        tool_calls = entry.get("tool_calls", [])

        if role == "assistant":
            node_id = uuid4().hex[:12]
            thought_node = TrajectoryNode(
                id=node_id,
                type=NodeType.THOUGHT,
                content=content,
                timestamp=timestamp,
                metadata={"line": line_num},
            )
            nodes.append(thought_node)
            last_thought_id = node_id
            last_tool_call_id = None

            for tc in tool_calls:
                tc_id = uuid4().hex[:12]
                tc_name = tc.get("name", tc.get("function", {}).get("name", "unknown"))
                tc_args = tc.get("arguments", tc.get("function", {}).get("arguments", ""))
                tc_node = TrajectoryNode(
                    id=tc_id,
                    type=NodeType.TOOL_CALL,
                    content=f"{tc_name}({tc_args})",
                    timestamp=timestamp,
                    metadata={"tool_name": tc_name, "line": line_num},
                )
                nodes.append(tc_node)
                edges.append(TrajectoryEdge(
                    source=node_id, target=tc_id,
                    relation=EdgeRelation.CALLS,
                ))
                last_tool_call_id = tc_id

        elif role == "tool" and last_tool_call_id:
            obs_id = uuid4().hex[:12]
            obs_node = TrajectoryNode(
                id=obs_id,
                type=NodeType.OBSERVATION,
                content=content[:2000],
                timestamp=timestamp,
                metadata={"line": line_num},
            )
            nodes.append(obs_node)
            edges.append(TrajectoryEdge(
                source=last_tool_call_id, target=obs_id,
                relation=EdgeRelation.RESPONDS_TO,
            ))

        elif role == "system":
            sys_id = uuid4().hex[:12]
            sys_node = TrajectoryNode(
                id=sys_id,
                type=NodeType.ACTION,
                content=content[:2000],
                timestamp=timestamp,
                metadata={"line": line_num, "system": True},
            )
            nodes.append(sys_node)

    return TrajectoryGraph(
        nodes=nodes,
        edges=edges,
        metadata={"source": str(path), "format": "jsonl"},
    )
