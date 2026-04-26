"""Parse OpenTelemetry trace exports into canonical TrajectoryGraph format.

OTel JSON export contains resourceSpans with scopeSpans containing spans.
Each span has: trace_id, span_id, parent_span_id, name, attributes, events.
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


# Heuristic mapping of span names/attributes to node types
_AGENT_SPAN_PREFIXES = ("agent", "llm", "chat", "completion", "think", "reason")
_TOOL_SPAN_PREFIXES = ("tool", "function", "execute", "run_", "call_", "api_", "http", "bash", "read", "write", "search")


def parse_opentelemetry(path: Path) -> TrajectoryGraph:
    """Parse an OpenTelemetry JSON export into a TrajectoryGraph."""
    data = json.loads(path.read_text(encoding="utf-8"))

    nodes: list[TrajectoryNode] = []
    edges: list[TrajectoryEdge] = []
    id_map: dict[str, str] = {}

    resource_spans = data.get("resourceSpans", [])
    if not resource_spans and isinstance(data, list):
        resource_spans = data

    for rs in resource_spans:
        scope_spans = rs.get("scopeSpans", [])
        for ss in scope_spans:
            for span in ss.get("spans", []):
                span_id = span.get("spanId", span.get("span_id", uuid4().hex[:16]))
                parent_id = span.get("parentSpanId", span.get("parent_span_id"))
                name = span.get("name", "unknown")
                attributes = span.get("attributes", {})
                events = span.get("events", [])

                node_type = _infer_node_type(name, attributes)
                content = _extract_content(name, attributes, events)

                node_id = uuid4().hex[:12]
                id_map[span_id] = node_id

                node = TrajectoryNode(
                    id=node_id,
                    type=node_type,
                    content=content,
                    timestamp=_nano_to_iso(span.get("startTimeUnixNano", span.get("start_time"))),
                    metadata={
                        "span_id": span_id,
                        "trace_id": span.get("traceId", span.get("trace_id", "")),
                        "service": _get_attr(attributes, "service.name"),
                        "duration_ms": _span_duration_ms(span),
                    },
                )
                nodes.append(node)

                if parent_id and parent_id in id_map:
                    relation = EdgeRelation.LEADS_TO
                    if node_type == NodeType.TOOL_CALL:
                        relation = EdgeRelation.CALLS
                    elif node_type == NodeType.OBSERVATION:
                        relation = EdgeRelation.RESPONDS_TO
                    edges.append(TrajectoryEdge(
                        source=id_map[parent_id], target=node_id,
                        relation=relation,
                    ))

    return TrajectoryGraph(
        nodes=nodes,
        edges=edges,
        metadata={"source": str(path), "format": "opentelemetry"},
    )


def _infer_node_type(name: str, attributes: dict) -> NodeType:
    """Infer the trajectory node type from span name and attributes."""
    name_lower = name.lower()
    attr_type = _get_attr(attributes, "type") or _get_attr(attributes, "agent.node.type")

    if attr_type:
        attr_lower = attr_type.lower()
        if attr_lower in ("thought", "thinking", "reasoning"):
            return NodeType.THOUGHT
        if attr_lower in ("tool_call", "tool", "function", "action"):
            return NodeType.TOOL_CALL
        if attr_lower in ("observation", "result", "response", "output"):
            return NodeType.OBSERVATION

    for prefix in _AGENT_SPAN_PREFIXES:
        if name_lower.startswith(prefix):
            return NodeType.THOUGHT

    for prefix in _TOOL_SPAN_PREFIXES:
        if name_lower.startswith(prefix):
            return NodeType.TOOL_CALL

    return NodeType.ACTION


def _extract_content(name: str, attributes: dict, events: list) -> str:
    """Extract readable content from a span."""
    parts = [f"[{name}]"]
    for key in ("input", "content", "prompt", "message", "arguments", "query"):
        val = _get_attr(attributes, key)
        if val:
            parts.append(str(val)[:1500])
            break
    for evt in events[:3]:
        evt_name = evt.get("name", "")
        evt_attrs = evt.get("attributes", {})
        evt_content = _get_attr(evt_attrs, "content") or _get_attr(evt_attrs, "output") or ""
        if evt_content:
            parts.append(f"Event[{evt_name}]: {str(evt_content)[:500]}")
    return " | ".join(parts)[:2000]


def _get_attr(attributes: dict, key: str) -> str | None:
    """Get an attribute value from OTel attributes (handles {key: {value: v}} format)."""
    if key in attributes:
        val = attributes[key]
        if isinstance(val, dict):
            return val.get("stringValue", val.get("intValue", val.get("doubleValue", str(val))))
        return str(val)
    return None


def _nano_to_iso(nano: str | int | None) -> str | None:
    """Convert Unix nanosecond timestamp to ISO format."""
    if nano is None:
        return None
    try:
        from datetime import datetime, timezone
        seconds = int(nano) / 1_000_000_000
        return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
    except (ValueError, TypeError, OSError):
        return None


def _span_duration_ms(span: dict) -> float | None:
    """Calculate span duration in milliseconds."""
    start = span.get("startTimeUnixNano", span.get("start_time"))
    end = span.get("endTimeUnixNano", span.get("end_time"))
    if start and end:
        try:
            return (int(end) - int(start)) / 1_000_000
        except (ValueError, TypeError):
            return None
    return None
