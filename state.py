"""
State management for the Self-Healing SRE Agent.

This module defines the TypedDict structure that will be used as the state
for the LangGraph StateGraph. The state is passed between all agent nodes
and tracks the entire workflow from error detection to PR creation.
"""

from operator import add
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage


class SREAgentState(TypedDict):
    """
    State schema for the Self-Healing SRE Agent workflow.

    The state flows through these phases:
    1. Investigation: Fetch and analyze logs to identify root cause
    2. Fix Generation: Create code to fix the identified issue
    3. Validation: Verify the generated fix is valid Python code
    4. PR Creation: Open a GitHub Pull Request with the fix

    Attributes:
        messages: Conversation history between agents and LLM. Uses Annotated
                 with `add` operator to automatically append messages rather
                 than replace them.

        error_logs: Raw application logs fetched from the monitoring system.

        root_cause_identified: Boolean flag indicating if the Investigator
                              Agent has successfully identified the root cause.
                              Controls routing from Investigator to Mechanic.

        root_cause_analysis: Detailed explanation of what caused the error.
                            Used by Mechanic Agent to generate appropriate fix.

        fix_code: The generated Python code that fixes the identified issue.

        fix_validated: Boolean flag indicating if the Validator Node confirmed
                      the fix is syntactically valid Python code.

        validation_errors: List of syntax or validation errors found in fix_code.
                          Empty if fix is valid. Fed back to Mechanic for retry.

        pr_status: Status of the PR creation process. Values:
                  - "pending": Not yet attempted
                  - "created": Successfully created
                  - "failed": PR creation failed

        pr_url: The URL of the created GitHub Pull Request (if successful).

        iteration_count: Counter to prevent infinite loops in agent retries.
                        Incremented each time Investigator or Mechanic runs.

        error_timestamp: Timestamp when the error was detected (ISO format).
    """

    # Message history - automatically appended due to `add` operator
    messages: Annotated[Sequence[BaseMessage], add]

    # Investigation phase
    error_logs: str
    root_cause_identified: bool
    root_cause_analysis: str

    # Fix generation phase
    fix_code: str
    fix_validated: bool
    validation_errors: list[str]

    # PR creation phase
    pr_status: str  # "pending", "created", "failed"
    pr_url: str

    # Control flow
    iteration_count: int
    error_timestamp: str


def create_initial_state(error_message: str) -> dict:
    """
    Factory function to create an initial state for a new SRE workflow.

    Args:
        error_message: The initial error message or alert that triggered
                      the self-healing workflow.

    Returns:
        A dictionary with default values for all state fields.
    """
    from datetime import datetime, timezone

    from langchain_core.messages import HumanMessage

    return {
        "messages": [HumanMessage(content=error_message)],
        "error_logs": "",
        "root_cause_identified": False,
        "root_cause_analysis": "",
        "fix_code": "",
        "fix_validated": False,
        "validation_errors": [],
        "pr_status": "pending",
        "pr_url": "",
        "iteration_count": 0,
        "error_timestamp": datetime.now(timezone.utc).isoformat(),
    }
