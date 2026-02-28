#!/usr/bin/env python3
"""CI entrypoint for automatic self-healing runs.

This script is intended to run in GitHub Actions after a CI failure.
It executes the LangGraph workflow non-interactively, verifies that both
LLM agents (Investigator + Mechanic) executed, and attempts PR creation.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

from graph import sre_graph
from state import create_initial_state

# Load repository/local env values
load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def build_incident_message() -> str:
    """Build a rich incident payload from GitHub Actions context."""
    repo = _env("GITHUB_REPOSITORY", "unknown-repo")
    sha = _env("GITHUB_SHA", "unknown-sha")
    workflow = _env("FAILED_WORKFLOW_NAME", _env("GITHUB_WORKFLOW", "unknown-workflow"))
    run_id = _env("FAILED_WORKFLOW_RUN_ID", _env("GITHUB_RUN_ID", "unknown-run"))
    run_url = _env("FAILED_WORKFLOW_RUN_URL", "")
    branch = _env("FAILED_WORKFLOW_HEAD_BRANCH", _env("GITHUB_REF_NAME", "unknown-branch"))
    actor = _env("GITHUB_ACTOR", "unknown-actor")
    event = _env("GITHUB_EVENT_NAME", "unknown-event")

    return f"""
[ALERT] CI Failure Detected

Repository: {repo}
Workflow: {workflow}
Run ID: {run_id}
Branch: {branch}
Commit SHA: {sha}
Triggered By: {actor}
Event: {event}
Run URL: {run_url or 'not-available'}
Timestamp: {datetime.now(timezone.utc).isoformat()}

A production-quality issue is suspected because CI failed.
Investigate likely root cause, generate a minimal safe fix, validate it,
and create a PR if validation passes.
""".strip()


def run_ci_auto_heal() -> int:
    """Execute self-healing workflow and enforce two-agent collaboration."""
    incident_message = build_incident_message()
    thread_id = f"ci-auto-heal-{_env('FAILED_WORKFLOW_RUN_ID', _env('GITHUB_RUN_ID', 'manual'))}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    initial_state = create_initial_state(incident_message)
    config = {"configurable": {"thread_id": thread_id}}

    print("=" * 72)
    print("AUTO HEAL CI WORKFLOW")
    print("=" * 72)
    print(f"Thread ID: {thread_id}")

    visited_nodes: list[str] = []
    final_state: dict = {}

    try:
        for idx, output in enumerate(sre_graph.stream(initial_state, config), start=1):
            node = list(output.keys())[0]
            state_data = output[node]
            visited_nodes.append(node)
            final_state = state_data

            print(f"[STEP {idx}] node={node} iteration={state_data.get('iteration_count', 0)}")

            if node == "investigator":
                analysis = state_data.get("root_cause_analysis", "")
                print(f"  Investigator → Mechanic handoff prepared ({len(analysis)} chars)")

            if node == "mechanic":
                fix_preview = state_data.get("fix_code", "")[:120].replace("\n", " ")
                print(f"  Mechanic received handoff and proposed fix: {fix_preview}...")

            if node == "validator" and state_data.get("validation_errors"):
                print("  Validator feedback sent back to Investigator for self-correction")

    except Exception as exc:
        print(f"[ERROR] Auto-heal execution failed: {exc}")
        return 1

    investigator_runs = visited_nodes.count("investigator")
    mechanic_runs = visited_nodes.count("mechanic")

    summary = {
        "investigator_runs": investigator_runs,
        "mechanic_runs": mechanic_runs,
        "total_steps": len(visited_nodes),
        "visited_nodes": visited_nodes,
        "fix_validated": bool(final_state.get("fix_validated", False)),
        "pr_status": final_state.get("pr_status", "unknown"),
        "iteration_count": final_state.get("iteration_count", 0),
    }

    print("\nAUTO_HEAL_SUMMARY=")
    print(json.dumps(summary, indent=2))

    if investigator_runs < 1 or mechanic_runs < 1:
        print("[ERROR] Two-agent collaboration check failed (Investigator/Mechanic missing).")
        return 1

    if final_state.get("pr_status") != "created":
        print("[ERROR] Auto-heal finished without creating PR.")
        return 1

    print("[SUCCESS] Auto-heal completed with two-agent collaboration and PR creation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_ci_auto_heal())
