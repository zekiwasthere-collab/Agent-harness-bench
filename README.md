# AgentHarnessBench

**A benchmark harness suite for evaluating LLM agent trajectories.**

AgentHarnessBench ingests agent execution logs, scores them on a weighted rubric of process and outcome metrics, runs compliance checks, and generates interactive reports — all from a single CLI command.

---

## Why this exists

Most LLM benchmarks measure *what* an agent answered. AgentHarnessBench measures *how* it got there.

A model that stumbles into the right answer through 30 redundant tool calls looks identical to one that nails it in 3 focused steps on a final-answer benchmark. AgentHarnessBench captures that difference by evaluating the full trajectory graph — every thought, tool call, and observation — with a process-weighted rubric (60% process / 40% outcome).

Inspired by Karpathy's agentic coding insights and TRAJECT-Bench's trajectory-level metrics.

---

## Features

- **Multi-format ingestion** — Parse agent logs from JSONL, LangSmith, and OpenTelemetry with auto-detection
- **4-stage pipeline** — Generation → Execution → Evaluation → Compliance
- **Process-weighted scoring** — 6 process metrics (tool selection, parameter correctness, step order, reasoning coherence, efficiency, error recovery) + 3 outcome metrics
- **Compliance checks** — Timeout, safety, cost, concept drift, resource usage
- **Interactive HTML reports** — Dark dashboard theme with score cards, metric bars, compliance tables, and trajectory timelines
- **Graphify-compatible output** — Export trajectory graphs as `graph.json` for visualization and community detection
- **Leaderboard generation** — HuggingFace-compatible JSON with ranked entries
- **Rich console output** — Tables, progress bars, and color-coded metrics in the terminal

---

## Install

```bash
pip install -e .
# or with dev dependencies
pip install -e ".[dev]"
```

Requires Python 3.10+.

---

## Quick Start

### Run a simulated benchmark

```bash
agent-harness-bench run -t code_debug -d medium -o output/
```

### Ingest an agent log

```bash
agent-harness-bench ingest agent_log.jsonl -o trajectory.graph.json
agent-harness-bench ingest langsmith_run.json --format langsmith -o trajectory.graph.json
```

### Evaluate a trajectory

```bash
agent-harness-bench evaluate trajectory.graph.json -o evaluation_result.json
```

### Generate an HTML report

```bash
agent-harness-bench report evaluation_result.json -o report.html
```

### Generate a leaderboard

```bash
agent-harness-bench leaderboard results_dir/ -o leaderboard.json
```

---

## Architecture

```
src/agent_harness_bench/
  schema.py           Pydantic models (TrajectoryGraph, EvaluationResult, BenchmarkReport)
  cli.py              Click CLI with 5 commands
  pipeline.py         BenchmarkPipeline orchestrator (4-stage)

  ingest/
    jsonl.py          Parse JSONL logs (role/content/tool_calls per line)
    langsmith.py      Parse LangSmith runs.json exports
    opentelemetry.py  Parse OTel trace JSON exports
    auto.py           Auto-detect format and dispatch

  evaluate/
    generation.py     Synthetic task generation (4 types × 3 difficulties)
    execution.py      Agent execution (real + simulated mode)
    evaluation.py     RubricScorer + LLMJudge (heuristic MVP, LLM-ready)
    compliance.py     Safety/cost/drift/timeout/resource checks

  report/
    html_report.py    Self-contained dark-theme HTML (Jinja2)
    leaderboard.py    HuggingFace-compatible leaderboard JSON
    trajectory_graph.py  Graphify-compatible graph.json export
    summary.py        Rich console output
```

---

## Scoring Rubric

### Process Metrics (60% weight)

| Metric | Weight | What it measures |
|---|---|---|
| Tool Selection Accuracy | 0.20 | Did the agent pick the right tools for each step? |
| Parameter Correctness | 0.15 | Were tool parameters well-formed and appropriate? |
| Step Order Correctness | 0.20 | Did the agent follow a logical step sequence? |
| Reasoning Coherence | 0.25 | Are thought nodes consistent and non-contradictory? |
| Efficiency | 0.10 | Are there redundant or unnecessary steps? |
| Error Recovery Rate | 0.10 | Does the agent recover from tool failures? |

### Outcome Metrics (40% weight)

| Metric | What it measures |
|---|---|
| Task Completion | Did the agent finish the task? |
| Answer Correctness | Is the final answer correct? |
| Output Quality | Is the output well-structured and complete? |

---

## Trajectory Graph Format

All logs are normalized into a `TrajectoryGraph` — the canonical format for evaluation and reporting:

```json
{
  "nodes": [
    {"id": "a1b2", "type": "thought", "content": "I need to find the bug...", "confidence": 1.0},
    {"id": "c3d4", "type": "tool_call", "content": "grep -n 'def process'", "confidence": 1.0},
    {"id": "e5f6", "type": "observation", "content": "Found 3 matches in main.py", "confidence": 1.0}
  ],
  "edges": [
    {"source": "a1b2", "target": "c3d4", "relation": "leads_to"},
    {"source": "c3d4", "target": "e5f6", "relation": "responds_to"}
  ],
  "metadata": {"agent_name": "my-agent", "model": "gpt-4o"}
}
```

This format is also compatible with [Graphify](https://github.com/safishamsi/graphify) for interactive visualization and community detection.

---

## CLI Reference

```
agent-harness-bench ingest   <path>   [-o output] [--format auto|jsonl|langsmith|opentelemetry]
agent-harness-bench evaluate <path>   [-o output] [-t task_type] [-d difficulty]
agent-harness-bench report   <path>   [-o output]
agent-harness-bench run               [-t task_type] [-d difficulty] [-o output] [--agent-name NAME] [--model MODEL]
agent-harness-bench leaderboard <dir> [-o output]
```

---

## Task Types

| Type | Description |
|---|---|
| `code_debug` | Find and fix a bug in code |
| `code_generation` | Generate code from a specification |
| `data_analysis` | Analyze a dataset and answer questions |
| `web_research` | Search and synthesize information from the web |

Each type has 3 difficulty levels: `easy`, `medium`, `hard`.

---

## Extending

### Add a new ingest format
1. Create `ingest/<format>.py` with a `parse_<format>(path) -> TrajectoryGraph`
2. Register it in `ingest/auto.py` detection logic
3. Add the format choice to `cli.py`

### Add a new task template
1. Add to `TASK_TEMPLATES` in `evaluate/generation.py`
2. Add simulated trajectory in `evaluate/execution.py`

### Add a real LLM judge
The `LLMJudge` class in `evaluate/evaluation.py` currently uses heuristic scoring. Replace `judge()` with an actual LLM API call — the interface is already structured for it.

---

## License

MIT
