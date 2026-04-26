"""Generate HuggingFace-compatible leaderboard JSON."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from agent_harness_bench.schema import LeaderboardEntry


def generate_leaderboard_json(entries: list[LeaderboardEntry], output_path: Path) -> Path:
    """Generate a leaderboard JSON file."""
    output_path = Path(output_path)

    # Sort by overall_score descending and assign ranks
    sorted_entries = sorted(entries, key=lambda e: e.overall_score, reverse=True)

    current_rank = 1
    for i, entry in enumerate(sorted_entries):
        if i > 0 and entry.overall_score < sorted_entries[i - 1].overall_score:
            current_rank = i + 1
        entry.rank = current_rank

    leaderboard = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "benchmark_version": "0.1.0",
            "task_count": len(sorted_entries),
        },
        "entries": [
            {
                "rank": e.rank,
                "agent_name": e.agent_name,
                "model": e.model,
                "task_id": e.task_id,
                "overall_score": round(e.overall_score, 3),
                "process_score": round(e.process_score, 3),
                "outcome_score": round(e.outcome_score, 3),
                "compliance": e.compliance,
            }
            for e in sorted_entries
        ],
    }

    output_path.write_text(json.dumps(leaderboard, indent=2), encoding="utf-8")
    return output_path
