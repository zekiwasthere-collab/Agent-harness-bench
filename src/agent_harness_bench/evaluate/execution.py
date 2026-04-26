"""Execution stage - run or simulate agent execution on benchmark tasks."""

from __future__ import annotations

import random
from datetime import datetime, timezone
from uuid import uuid4

from agent_harness_bench.schema import (
    EdgeRelation,
    NodeType,
    TrajectoryEdge,
    TrajectoryGraph,
    TrajectoryNode,
)


# Simulated tool names that an agent might call
_SIM_TOOLS = {
    "code_debug": ["read_file", "search_code", "run_tests", "edit_file", "grep", "cat"],
    "multi_step_api": ["api_call", "parse_response", "transform_data", "validate", "retry"],
    "research_synthesis": ["search", "read", "summarize", "write", "cite"],
    "tool_selection": ["plan", "select_tool", "execute", "verify", "report"],
}

_SIM_THOUGHTS = {
    "code_debug": [
        "I need to find the bug. Let me start by reading the source file.",
        "I can see the function. Let me search for potential issues.",
        "Found a suspicious pattern. Let me run the tests to confirm.",
        "The test confirms the bug. Let me apply the fix.",
        "Fix applied. Let me verify the tests pass now.",
        "All tests passing. The bug was in the loop boundary.",
    ],
    "multi_step_api": [
        "I need to call the first API to get the initial data.",
        "Got the response. Let me parse the relevant fields.",
        "Now I need to transform this data for the second API call.",
        "Transformed data ready. Making the second API call.",
        "Second call succeeded. Let me validate the combined result.",
        "Result is valid. Compiling the final output.",
    ],
    "research_synthesis": [
        "Let me search for information on this topic.",
        "Found a relevant source. Let me read it in detail.",
        "Good information. Let me search for another perspective.",
        "Now I have enough data to synthesize the findings.",
        "Writing up the synthesis covering all key points.",
        "Report complete. Let me verify all sources are cited.",
    ],
    "tool_selection": [
        "Let me plan the approach first by analyzing available tools.",
        "Based on the requirements, I'll select the optimal tool set.",
        "Executing step 1 with the selected tool.",
        "First step done. Moving to the next tool.",
        "Verifying the results of each step.",
        "All steps completed successfully. Generating final report.",
    ],
}

_SIM_OBSERVATIONS = {
    "read_file": "File contents loaded: 42 lines, function defined at line 15",
    "search_code": "Found 3 matches for the pattern",
    "run_tests": "2/3 tests passed, 1 failed: test_edge_case",
    "edit_file": "File updated successfully",
    "api_call": "Response 200: {\"data\": [...], \"count\": 15}",
    "parse_response": "Extracted 5 records from response",
    "search": "Found 8 relevant results",
    "summarize": "Summary generated: 3 key points identified",
    "validate": "Validation passed: all constraints satisfied",
    "verify": "Verification complete: output matches expected format",
}


class ExecutionStage:
    """Execute agent on benchmark tasks (real or simulated)."""

    def execute(self, task: dict, agent_config: dict, timeout: int = 300) -> TrajectoryGraph:
        """Execute a real agent on the given task.

        For MVP, delegates to simulation. In production, this would
        spawn an actual agent process with the given config.
        """
        return self.execute_simulated(task, agent_config)

    def execute_simulated(self, task: dict, agent_config: dict | None = None) -> TrajectoryGraph:
        """Generate a simulated trajectory for a given task.

        Creates a realistic thought -> tool_call -> observation chain
        with some randomness to simulate different agent quality levels.
        """
        agent_name = (agent_config or {}).get("name", "simulated")
        model = (agent_config or {}).get("model", "simulated")
        task_type = task.get("task_type", "code_debug")
        expected_steps = task.get("expected_steps", 4)

        # Random quality factor affects how good the simulated agent is
        quality = random.uniform(0.5, 1.0)

        nodes: list[TrajectoryNode] = []
        edges: list[TrajectoryEdge] = []
        tools = _SIM_TOOLS.get(task_type, _SIM_TOOLS["code_debug"])
        thoughts = _SIM_THOUGHTS.get(task_type, _SIM_THOUGHTS["code_debug"])

        prev_thought_id: str | None = None

        num_steps = max(2, min(expected_steps + random.randint(-1, 2), len(thoughts)))

        for i in range(num_steps):
            ts = datetime.now(timezone.utc).isoformat()

            # Thought node
            thought_id = uuid4().hex[:12]
            thought_content = thoughts[i] if i < len(thoughts) else f"Processing step {i+1}..."

            # Introduce occasional errors in lower quality simulations
            if quality < 0.7 and random.random() < 0.3:
                thought_content += " [uncertain about next step]"

            thought_node = TrajectoryNode(
                id=thought_id,
                type=NodeType.THOUGHT,
                content=thought_content,
                timestamp=ts,
                confidence=min(1.0, quality + random.uniform(-0.2, 0.1)),
                metadata={"step": i + 1},
            )
            nodes.append(thought_node)

            if prev_thought_id:
                edges.append(TrajectoryEdge(
                    source=prev_thought_id, target=thought_id,
                    relation=EdgeRelation.LEADS_TO,
                ))

            # Tool call node
            tool_name = tools[i % len(tools)]
            tool_id = uuid4().hex[:12]
            tool_node = TrajectoryNode(
                id=tool_id,
                type=NodeType.TOOL_CALL,
                content=f"{tool_name}()",
                timestamp=ts,
                confidence=min(1.0, quality + random.uniform(-0.1, 0.1)),
                metadata={"tool_name": tool_name, "step": i + 1},
            )
            nodes.append(tool_node)
            edges.append(TrajectoryEdge(
                source=thought_id, target=tool_id,
                relation=EdgeRelation.CALLS,
            ))

            # Observation node
            obs_id = uuid4().hex[:12]
            obs_content = _SIM_OBSERVATIONS.get(tool_name, f"{tool_name} completed")

            # Lower quality agents sometimes get errors
            if quality < 0.6 and random.random() < 0.25:
                obs_content = f"Error: {tool_name} failed - timeout exceeded"

            obs_node = TrajectoryNode(
                id=obs_id,
                type=NodeType.OBSERVATION,
                content=obs_content,
                timestamp=ts,
                confidence=min(1.0, quality + random.uniform(-0.15, 0.15)),
                metadata={"step": i + 1},
            )
            nodes.append(obs_node)
            edges.append(TrajectoryEdge(
                source=tool_id, target=obs_id,
                relation=EdgeRelation.RESPONDS_TO,
            ))

            prev_thought_id = thought_id

        # Add error recovery edges for low-quality runs
        error_nodes = [n for n in nodes if "Error" in n.content or "uncertain" in n.content]
        recovery_nodes = [n for n in nodes if n.type == NodeType.THOUGHT and "uncertain" not in n.content]
        if error_nodes and recovery_nodes and len(error_nodes) < len(recovery_nodes):
            edges.append(TrajectoryEdge(
                source=error_nodes[0].id,
                target=recovery_nodes[min(len(recovery_nodes) - 1, len(error_nodes))].id,
                relation=EdgeRelation.RECOVERS_FROM,
                confidence_score=0.6,
            ))

        return TrajectoryGraph(
            nodes=nodes,
            edges=edges,
            metrics={"quality_factor": quality, "simulated": True},
            metadata={
                "agent_name": agent_name,
                "model": model,
                "task_id": task.get("task_id", "unknown"),
                "task_type": task_type,
                "expected_steps": expected_steps,
                "actual_steps": num_steps,
            },
        )
