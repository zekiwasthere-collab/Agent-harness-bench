# Graph Report - C:\Users\nahom\OneDrive\Pictures\Documents\res\project 1  (2026-04-25)

## Corpus Check
- 19 files · ~8,051 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 169 nodes · 557 edges · 10 communities detected
- Extraction: 36% EXTRACTED · 64% INFERRED · 0% AMBIGUOUS · INFERRED: 359 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]

## God Nodes (most connected - your core abstractions)
1. `TrajectoryGraph` - 79 edges
2. `NodeType` - 61 edges
3. `EdgeRelation` - 44 edges
4. `EvaluationResult` - 31 edges
5. `TrajectoryNode` - 26 edges
6. `TrajectoryEdge` - 26 edges
7. `BenchmarkReport` - 22 edges
8. `LeaderboardEntry` - 20 edges
9. `ComplianceStage` - 19 edges
10. `RubricScorer` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Synthetic task generation stage.  Generates benchmark tasks with expected tool s` --uses--> `NodeType`  [INFERRED]
  C:\Users\nahom\OneDrive\Pictures\Documents\res\project 1\src\agent_harness_bench\evaluate\generation.py → C:\Users\nahom\OneDrive\Pictures\Documents\res\project 1\src\agent_harness_bench\schema.py
- `Generates synthetic benchmark tasks.` --uses--> `NodeType`  [INFERRED]
  C:\Users\nahom\OneDrive\Pictures\Documents\res\project 1\src\agent_harness_bench\evaluate\generation.py → C:\Users\nahom\OneDrive\Pictures\Documents\res\project 1\src\agent_harness_bench\schema.py
- `Generate synthetic tasks for benchmarking.` --uses--> `NodeType`  [INFERRED]
  C:\Users\nahom\OneDrive\Pictures\Documents\res\project 1\src\agent_harness_bench\evaluate\generation.py → C:\Users\nahom\OneDrive\Pictures\Documents\res\project 1\src\agent_harness_bench\schema.py
- `Build a single task from a template.` --uses--> `NodeType`  [INFERRED]
  C:\Users\nahom\OneDrive\Pictures\Documents\res\project 1\src\agent_harness_bench\evaluate\generation.py → C:\Users\nahom\OneDrive\Pictures\Documents\res\project 1\src\agent_harness_bench\schema.py
- `Fill in the prompt template with random values.` --uses--> `NodeType`  [INFERRED]
  C:\Users\nahom\OneDrive\Pictures\Documents\res\project 1\src\agent_harness_bench\evaluate\generation.py → C:\Users\nahom\OneDrive\Pictures\Documents\res\project 1\src\agent_harness_bench\schema.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.14
Nodes (36): auto_ingest(), Execution stage - run or simulate agent execution on benchmark tasks., Execute agent on benchmark tasks (real or simulated)., Execute a real agent on the given task.          For MVP, delegates to simulatio, Generate a simulated trajectory for a given task.          Creates a realistic t, parse_jsonl(), Parse JSONL trajectory logs into canonical TrajectoryGraph format.  Each line is, Parse a JSONL file into a TrajectoryGraph. (+28 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (34): Auto-detect trajectory log format and dispatch to the right parser., Ingest a trajectory log, auto-detecting format if needed., BaseModel, cli(), ingest(), leaderboard(), CLI interface for AgentHarnessBench., Generate leaderboard JSON from evaluation results in a directory. (+26 more)

### Community 2 - "Community 2"
Cohesion: 0.13
Nodes (24): _lcs_length(), LLMJudge, random_factor(), Core evaluation stage with rubrics and LLM-as-judge scoring., Score parameter correctness of tool calls (heuristic)., Score whether steps were executed in a logical order., Score reasoning coherence based on thought-tool-observation structure., Score efficiency: actual steps vs expected steps. (+16 more)

### Community 3 - "Community 3"
Cohesion: 0.35
Nodes (7): EvaluationStage, ExecutionStage, BenchmarkPipeline, 4-stage benchmark pipeline orchestrator., Run the pipeline for multiple agents and collect results., Generate a sorted leaderboard from benchmark reports., Orchestrates the full 4-stage benchmark pipeline.      Stages: Generation -> Exe

### Community 4 - "Community 4"
Cohesion: 0.24
Nodes (6): GenerationStage, Synthetic task generation stage.  Generates benchmark tasks with expected tool s, Build a single task from a template., Fill in the prompt template with random values., Generates synthetic benchmark tasks., Generate synthetic tasks for benchmarking.

### Community 5 - "Community 5"
Cohesion: 0.33
Nodes (7): evaluate(), Run the 4-stage evaluation pipeline on a trajectory graph., Run evaluation + compliance on an existing trajectory., BenchmarkReport, print_summary(), Rich console summary output for benchmark results., Print a formatted summary of benchmark results to the console.

### Community 6 - "Community 6"
Cohesion: 0.52
Nodes (1): ComplianceStage

### Community 7 - "Community 7"
Cohesion: 0.4
Nodes (3): Enum, Confidence, Canonical data models for AgentHarnessBench.

### Community 8 - "Community 8"
Cohesion: 0.4
Nodes (1): Report package - HTML reports, leaderboard JSON, and console output.

### Community 9 - "Community 9"
Cohesion: 0.67
Nodes (1): Run the full pipeline with simulated execution (MVP mode).

## Knowledge Gaps
- **1 isolated node(s):** `Canonical data models for AgentHarnessBench.`
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TrajectoryGraph` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 5`, `Community 6`, `Community 7`, `Community 9`?**
  _High betweenness centrality (0.426) - this node is a cross-community bridge._
- **Why does `NodeType` connect `Community 2` to `Community 0`, `Community 1`, `Community 3`, `Community 4`, `Community 6`, `Community 7`?**
  _High betweenness centrality (0.208) - this node is a cross-community bridge._
- **Why does `RubricScorer` connect `Community 2` to `Community 0`, `Community 1`, `Community 8`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Are the 77 inferred relationships involving `TrajectoryGraph` (e.g. with `CLI interface for AgentHarnessBench.` and `AgentHarnessBench - Evaluate LLM agent trajectories.`) actually correct?**
  _`TrajectoryGraph` has 77 INFERRED edges - model-reasoned connections that need verification._
- **Are the 58 inferred relationships involving `NodeType` (e.g. with `ComplianceStage` and `Compliance stage - safety, cost, drift, and resource checks.`) actually correct?**
  _`NodeType` has 58 INFERRED edges - model-reasoned connections that need verification._
- **Are the 41 inferred relationships involving `EdgeRelation` (e.g. with `RubricScorer` and `LLMJudge`) actually correct?**
  _`EdgeRelation` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `EvaluationResult` (e.g. with `BenchmarkPipeline` and `4-stage benchmark pipeline orchestrator.`) actually correct?**
  _`EvaluationResult` has 29 INFERRED edges - model-reasoned connections that need verification._