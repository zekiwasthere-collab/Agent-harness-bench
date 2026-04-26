"""Export trajectory graph in Graphify-compatible format."""

from __future__ import annotations

import json
from pathlib import Path

from agent_harness_bench.schema import TrajectoryGraph


def export_trajectory_graph(trajectory: TrajectoryGraph, output_path: Path) -> Path:
    """Export a TrajectoryGraph as a Graphify-compatible graph.json file."""
    output_path = Path(output_path)

    graph_data = {
        "nodes": [
            {
                "id": node.id,
                "label": node.content[:80],
                "type": node.type.value,
                "community": None,
                "source_file": None,
                "metadata": {
                    **node.metadata,
                    "confidence": node.confidence,
                    "timestamp": node.timestamp,
                },
            }
            for node in trajectory.nodes
        ],
        "links": [
            {
                "source": edge.source,
                "target": edge.target,
                "relation": edge.relation.value,
                "confidence": str(edge.confidence_score),
                "weight": edge.weight,
            }
            for edge in trajectory.edges
        ],
        "metrics": trajectory.metrics,
        "metadata": trajectory.metadata,
    }

    output_path.write_text(json.dumps(graph_data, indent=2, default=str), encoding="utf-8")
    return output_path
