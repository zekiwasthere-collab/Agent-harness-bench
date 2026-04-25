"""Auto-detect trajectory log format and dispatch to the right parser."""

from __future__ import annotations

import json
from pathlib import Path

from agent_harness_bench.ingest.jsonl import parse_jsonl
from agent_harness_bench.ingest.langsmith import parse_langsmith
from agent_harness_bench.ingest.opentelemetry import parse_opentelemetry
from agent_harness_bench.schema import TrajectoryGraph


def auto_ingest(path: Path, fmt: str = "auto") -> TrajectoryGraph:
    """Ingest a trajectory log, auto-detecting format if needed."""
    path = Path(path)

    if fmt != "auto":
        parsers = {
            "jsonl": parse_jsonl,
            "langsmith": parse_langsmith,
            "opentelemetry": parse_opentelemetry,
        }
        parser = parsers.get(fmt)
        if parser:
            return parser(path)
        raise ValueError(f"Unknown format: {fmt}")

    # Auto-detect
    text = path.read_text(encoding="utf-8").strip()

    # Try JSONL first: first line is valid JSON and not an object/array wrapper
    first_line = text.split("\n", 1)[0].strip()
    if first_line.startswith("{") and first_line.endswith("}"):
        try:
            first_obj = json.loads(first_line)
            if "role" in first_obj:
                return parse_jsonl(path)
        except json.JSONDecodeError:
            pass

    # Try full JSON parse for LangSmith or OTel
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            if "resourceSpans" in data:
                return parse_opentelemetry(path)
            if "runs" in data or all(k in data for k in ("id", "run_type")):
                return parse_langsmith(path)
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                if "spanId" in first or "span_id" in first or "parentSpanId" in first:
                    return parse_opentelemetry(path)
                if "run_type" in first or "parent_run_id" in first:
                    return parse_langsmith(path)
    except json.JSONDecodeError:
        pass

    # Fallback: try JSONL (most lenient)
    return parse_jsonl(path)
