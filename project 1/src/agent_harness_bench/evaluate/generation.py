"""Synthetic task generation stage.

Generates benchmark tasks with expected tool sequences, step counts,
and success criteria for evaluation.
"""

from __future__ import annotations

import random
import string
from uuid import uuid4

from agent_harness_bench.schema import NodeType


TASK_TEMPLATES = {
    "code_debug": {
        "description": "Find and fix a bug in the given code",
        "expected_tools": ["read_file", "search_code", "run_tests", "edit_file"],
        "success_criteria": [
            "Bug identified in source code",
            "Correct fix applied",
            "Tests pass after fix",
        ],
        "prompt_template": (
            "A Python function has a bug. The function {func_name} should {expected_behavior} "
            "but currently {actual_behavior}. Find the bug and fix it."
        ),
        "func_names": ["calculate_average", "parse_config", "validate_input", "sort_records", "merge_dicts"],
        "bug_types": ["off_by_one", "wrong_operator", "missing_return", "type_mismatch", "index_error"],
    },
    "multi_step_api": {
        "description": "Chain multiple API calls to accomplish a goal",
        "expected_tools": ["api_call", "parse_response", "transform_data", "api_call", "validate"],
        "success_criteria": [
            "First API call returns valid data",
            "Data transformed correctly for second call",
            "Second API call succeeds",
            "Final result matches expected format",
        ],
        "prompt_template": (
            "Use the {service_a} API to get {resource_a}, then use the result to call "
            "the {service_b} API to {action_b}. Return the combined result."
        ),
        "services": ["github", "slack", "database", "cache", "queue"],
        "resources": ["user profiles", "repository list", "channel messages", "query results"],
    },
    "research_synthesis": {
        "description": "Gather information from multiple sources and synthesize",
        "expected_tools": ["search", "read", "search", "read", "summarize", "write"],
        "success_criteria": [
            "Relevant sources found",
            "Key information extracted",
            "Synthesis covers all required topics",
            "Output is well-structured",
        ],
        "prompt_template": (
            "Research {topic} by searching for information about {subtopics}. "
            "Synthesize the findings into a structured report."
        ),
        "topics": ["microservices architecture", "prompt engineering techniques", "Python async patterns", "database indexing strategies"],
    },
    "tool_selection": {
        "description": "Select the right tools for a multi-step task",
        "expected_tools": ["plan", "select_tool", "execute", "verify"],
        "success_criteria": [
            "Correct tools selected for each step",
            "Tools used in optimal order",
            "No unnecessary tool calls",
            "Task completed efficiently",
        ],
        "prompt_template": (
            "You need to {goal}. You have access to these tools: {available_tools}. "
            "Choose the best combination and sequence to accomplish this."
        ),
        "goals": ["deploy a web service", "set up CI/CD pipeline", "migrate a database", "configure monitoring"],
    },
}

DIFFICULTY_CONFIG = {
    "easy": {"min_steps": 2, "max_steps": 3, "complexity": 0.3},
    "medium": {"min_steps": 4, "max_steps": 6, "complexity": 0.6},
    "hard": {"min_steps": 7, "max_steps": 10, "complexity": 0.9},
}


class GenerationStage:
    """Generates synthetic benchmark tasks."""

    def generate(self, task_type: str, difficulty: str = "medium", count: int = 1) -> list[dict]:
        """Generate synthetic tasks for benchmarking."""
        if task_type not in TASK_TEMPLATES:
            raise ValueError(f"Unknown task type: {task_type}. Choose from: {list(TASK_TEMPLATES)}")
        if difficulty not in DIFFICULTY_CONFIG:
            raise ValueError(f"Unknown difficulty: {difficulty}. Choose from: {list(DIFFICULTY_CONFIG)}")

        template = TASK_TEMPLATES[task_type]
        config = DIFFICULTY_CONFIG[difficulty]

        tasks = []
        for _ in range(count):
            task = self._build_task(template, task_type, config, difficulty)
            tasks.append(task)
        return tasks

    def _build_task(self, template: dict, task_type: str, config: dict, difficulty: str) -> dict:
        """Build a single task from a template."""
        expected_steps = random.randint(config["min_steps"], config["max_steps"])
        prompt = self._fill_prompt(template, task_type, expected_steps)

        return {
            "task_id": uuid4().hex[:8],
            "task_type": task_type,
            "description": template["description"],
            "prompt": prompt,
            "expected_tools": template["expected_tools"][:expected_steps],
            "expected_steps": expected_steps,
            "success_criteria": template["success_criteria"],
            "difficulty_level": difficulty,
            "complexity": config["complexity"],
        }

    def _fill_prompt(self, template: dict, task_type: str, steps: int) -> str:
        """Fill in the prompt template with random values."""
        prompt = template["prompt_template"]

        if task_type == "code_debug":
            prompt = prompt.format(
                func_name=random.choice(template["func_names"]),
                expected_behavior="return the correct result for all inputs",
                actual_behavior=random.choice([
                    "returns None for empty inputs",
                    "raises an IndexError on the last element",
                    "uses + instead of * for multiplication",
                    "fails to handle edge cases",
                ]),
            )
        elif task_type == "multi_step_api":
            services = random.sample(template["services"], 2)
            prompt = prompt.format(
                service_a=services[0],
                resource_a=random.choice(template["resources"]),
                service_b=services[1],
                action_b=random.choice(["create a record", "update the index", "send a notification", "trigger a build"]),
            )
        elif task_type == "research_synthesis":
            subtopics = random.sample(template["topics"], min(2, len(template["topics"])))
            prompt = prompt.format(
                topic=subtopics[0],
                subtopics=", ".join(subtopics),
            )
        elif task_type == "tool_selection":
            prompt = prompt.format(
                goal=random.choice(template["goals"]),
                available_tools=", ".join(template["expected_tools"]),
            )

        return prompt
