#!/usr/bin/env python3
"""
Main entry point for the Self-Healing SRE Agent.

This script can be run standalone or imported by the Streamlit UI.
It orchestrates the entire self-healing workflow from error detection
to PR creation.
"""

import sys
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv

from config import settings
from state import create_initial_state
from graph import sre_graph


# Load environment variables
load_dotenv()


def check_environment() -> tuple:
    """
    Validate all required environment variables using Pydantic config.

    Returns:
        tuple: (is_valid, error_messages)
    """
    try:
        # settings is already initialized at import time — report its state
        print(f"   LLM Provider: {settings.llm_provider}")
        print(f"   GitHub Repo: {settings.github_repo or '(not set — simulation mode)'}")
        print(f"   Log File: {settings.log_file}")
        if settings.langchain_tracing_v2:
            print(f"[INFO] LangSmith tracing enabled (project: {settings.langchain_project})")
        else:
            print("[WARNING] LangSmith not configured. Tracing will be disabled.")
        return True, []
    except Exception as e:
        return False, [str(e)]


def trigger_crash() -> bool:
    """
    Trigger the crash in the FastAPI app by sending a request with the bug header.
    
    Returns:
        bool: True if crash was triggered successfully, False otherwise
    """
    try:
        import httpx
        
        print("\n[TRIGGER] Triggering application crash...")
        response = httpx.get(
            f"http://localhost:{settings.app_port}/api/data",
            headers={"X-Trigger-Bug": "true"},
            timeout=5.0
        )
        
        if response.status_code == 500:
            print("[SUCCESS] Crash triggered successfully (500 error)")
            return True
        else:
            print(f"[WARNING] Expected 500 error, got {response.status_code}")
            return False
    
    except httpx.ConnectError:
        print("[ERROR] Could not connect to FastAPI app. Is it running on port 8000?")
        print("   Start it with: python app.py")
        return False
    except Exception as e:
        print(f"[ERROR] Error triggering crash: {e}")
        return False


def run_self_healing_workflow(
    initial_error: Optional[str] = None,
    config: Optional[dict] = None
) -> dict:
    """
    Execute the complete self-healing workflow.
    
    Args:
        initial_error: Optional custom error message to start with
        config: Optional configuration dict with thread_id, etc.
    
    Returns:
        dict: Final state of the workflow
    """
    if not initial_error:
        initial_error = """
[ALERT] Application Error Detected

Endpoint: /api/data
Status: 500 Internal Server Error
Error Type: KeyError
Timestamp: {timestamp}

The monitoring system has detected a crash in the production API.
Please investigate and fix the issue.
""".format(timestamp=datetime.now(timezone.utc).isoformat())
    
    # Create initial state
    print("\n" + "=" * 60)
    print("SELF-HEALING SRE AGENT - Starting Workflow")
    print("=" * 60)
    
    initial_state = create_initial_state(initial_error)
    
    # Set up configuration for state persistence
    if not config:
        config = {
            "configurable": {
                "thread_id": f"sre-workflow-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            }
        }
    
    # Execute the graph
    print("\n[WORKFLOW] Executing LangGraph workflow...")
    print(f"   Thread ID: {config['configurable']['thread_id']}")
    
    try:
        # Stream the workflow execution
        final_state = None
        for step, output in enumerate(sre_graph.stream(initial_state, config), 1):
            print(f"\n{'─' * 60}")
            print(f"Step {step}: {list(output.keys())[0]}")
            final_state = output
        
        print("\n" + "=" * 60)
        print("[SUCCESS] WORKFLOW COMPLETED")
        print("=" * 60)
        
        # Extract final state from the last output
        if final_state:
            node_name = list(final_state.keys())[0]
            state_data = final_state[node_name]
            
            # Print summary
            print("\n[SUMMARY]")
            print(f"   Root Cause Identified: {state_data.get('root_cause_identified', False)}")
            print(f"   Fix Validated: {state_data.get('fix_validated', False)}")
            print(f"   PR Status: {state_data.get('pr_status', 'N/A')}")
            print(f"   Total Iterations: {state_data.get('iteration_count', 0)}")
            
            if state_data.get('pr_url'):
                print("\n[PULL REQUEST]")
                print(state_data['pr_url'])
            
            return state_data
        
        return {}
    
    except Exception as e:
        print(f"\n[ERROR] Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def main():
    """
    Main function - can be called from command line.
    """
    print("Self-Healing SRE Agent")
    print("=" * 60)
    
    # Check environment
    is_valid, errors = check_environment()
    if not is_valid:
        print("\n[ERROR] Environment validation failed:")
        for error in errors:
            print(f"   {error}")
        print("\n[INFO] Copy .env.example to .env and configure your API keys")
        sys.exit(1)
    
    print("[SUCCESS] Environment configured correctly\n")
    
    # Ask if user wants to trigger the crash
    print("Options:")
    print("  1. Trigger crash and run self-healing workflow")
    print("  2. Just run self-healing workflow (assuming crash already happened)")
    print("  3. Exit")
    
    try:
        choice = input("\nSelect option (1-3): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n\nExiting...")
        sys.exit(0)
    
    if choice == "1":
        if trigger_crash():
            print("\n[SUCCESS] Crash logged to app_logs.txt")
            print("[WORKFLOW] Starting self-healing workflow...\n")
            run_self_healing_workflow()
        else:
            print("\n[ERROR] Could not trigger crash. Make sure app.py is running.")
            sys.exit(1)
    
    elif choice == "2":
        print("\n[WORKFLOW] Starting self-healing workflow...\n")
        run_self_healing_workflow()
    
    elif choice == "3":
        print("\nExiting...")
        sys.exit(0)
    
    else:
        print("\n[ERROR] Invalid option")
        sys.exit(1)


if __name__ == "__main__":
    main()
