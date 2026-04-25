# CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: AgentHarnessBench

A benchmark harness suite for evaluating LLM agent trajectories. Inspired by Karpathy's agentic coding insights and TRAJECT-Bench's trajectory-level metrics.

## Install & Run

```bash
pip install -e .                    # install in editable mode
pip install -e ".[dev]"             # install with dev dependencies
agent-harness-bench --help          # CLI help
agent-harness-bench run             # full simulated pipeline (generate -> execute -> evaluate -> report)
agent-harness-bench ingest log.jsonl -o trajectory.graph.json   # ingest a trajectory log
agent-harness-bench evaluate trajectory.graph.json              # evaluate a trajectory
agent-harness-bench report evaluation_result.json               # generate HTML report
```

## Tests

```bash
pytest                              # run all tests
pytest tests/test_schema.py         # single test file
pytest -x                           # stop on first failure
```

## Architecture

```
src/agent_harness_bench/
  schema.py          # Pydantic models: TrajectoryGraph, EvaluationResult, BenchmarkReport, LeaderboardEntry
  cli.py             # Click CLI: ingest, evaluate, report, run, leaderboard
  pipeline.py        # BenchmarkPipeline orchestrator (4-stage)
  ingest/
    jsonl.py         # Parse JSONL logs (role/content/tool_calls per line)
    langsmith.py     # Parse LangSmith runs.json exports
    opentelemetry.py # Parse OTel trace JSON exports
    auto.py          # Auto-detect format and dispatch
  evaluate/
    generation.py    # Synthetic task generation (4 templates × 3 difficulties)
    execution.py     # Agent execution (real + simulated mode)
    evaluation.py    # RubricScorer (process+outcome weights), LLMJudge (heuristic MVP)
    compliance.py    # Safety/cost/drift/timeout/resource checks
  report/
    html_report.py   # Self-contained dark-theme HTML (Jinja2, no external deps)
    leaderboard.py   # HuggingFace-compatible leaderboard JSON
    trajectory_graph.py  # Graphify-compatible graph.json export
    summary.py       # Rich console output (tables, panels, bars)
```

## Key Design Decisions

- **Canonical format**: All ingested logs become `TrajectoryGraph` (nodes=thought/tool_call/observation, edges=leads_to/calls/responds_to). This is the single source of truth for evaluation and reporting.
- **Graphify-compatible output**: `trajectory.graph.json` uses Graphify's node/link schema so you can `/graphify` the output for interactive visualization and community detection.
- **4-stage pipeline**: Generation → Execution → Evaluation → Compliance. Each stage is independent and testable.
- **Process > Outcome**: Process metrics weighted 60%, outcome 40%. TRAJECT-Bench showed process metrics reveal failure modes that final-answer accuracy hides.
- **MVP simulation**: ExecutionStage has `execute_simulated()` for testing without a live agent. The interface is structured for real agent integration later.

## Adding a New Ingest Format

1. Create `src/agent_harness_bench/ingest/<format>.py` with a `parse_<format>(path: Path) -> TrajectoryGraph`
2. Add it to `ingest/__init__.py` and `ingest/auto.py` detection logic
3. Add the format choice to `cli.py` ingest command

## Adding a New Task Template

1. Add to `TASK_TEMPLATES` dict in `evaluate/generation.py`
2. Add simulated thoughts/tools/observations to `evaluate/execution.py`
