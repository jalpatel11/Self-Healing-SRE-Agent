"""
LangGraph StateGraph definition for the Self-Healing SRE Agent.

This module defines the agentic workflow with conditional routing and
a self-correction loop that allows the agent to iteratively improve its
fixes based on validation feedback.

Graph Flow:
    START → Investigator → Mechanic → Validator
                ↑                         ↓
                └─────────────────────────┘
                    (if tests fail)       → PR Creator → END
                                              (if tests pass)
"""

from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state import SREAgentState
from agents import (
    investigator_agent,
    mechanic_agent,
    validator_node,
    pr_creator_node
)


def should_continue_investigation(state: SREAgentState) -> Literal["mechanic", "investigator", "end"]:
    """
    Routing logic after the Investigator Agent.
    
    Decision tree:
    1. If iteration count > 3: Give up (return "end")
    2. If root cause identified: Move to Mechanic (return "mechanic")
    3. Otherwise: Continue investigating (return "investigator")
    
    Args:
        state: Current workflow state
    
    Returns:
        Next node to execute: "mechanic", "investigator", or "end"
    """
    iteration = state.get("iteration_count", 0)
    root_cause_found = state.get("root_cause_identified", False)
    
    # Safety limit: Max 3 attempts
    if iteration > 3:
        print(f"\n[WARNING] Maximum iterations (3) reached. Ending workflow.")
        return "end"
    
    # Success: Root cause identified, proceed to fix generation
    if root_cause_found:
        print(f"\n[SUCCESS] Root cause identified. Moving to Mechanic Agent...")
        return "mechanic"
    
    # Continue investigation
    print(f"\n[RETRY] Root cause not yet clear. Continuing investigation (attempt {iteration}/3)...)")
    return "investigator"


def should_continue_after_validation(state: SREAgentState) -> Literal["pr_creator", "investigator", "end"]:
    """
    Routing logic after the Validator Node - THE SELF-CORRECTION LOOP.
    
    This is the critical routing function that implements the self-healing behavior:
    
    Decision tree:
    1. If tests passed: Success! Move to PR creation (return "pr_creator")
    2. If iteration count > 3: Too many retries, give up (return "end")
    3. If tests failed: Loop back to Investigator with error feedback (return "investigator")
    
    The self-correction loop allows the agent to:
    - Receive validation feedback
    - Reconsider its root cause analysis
    - Generate an improved fix
    - Try again (up to 3 times total)
    
    This mimics how human engineers debug issues iteratively.
    
    Args:
        state: Current workflow state
    
    Returns:
        Next node to execute: "pr_creator", "investigator", or "end"
    """
    fix_validated = state.get("fix_validated", False)
    iteration = state.get("iteration_count", 0)
    validation_errors = state.get("validation_errors", [])
    
    # Success case: Tests passed!
    if fix_validated:
        print(f"\n[SUCCESS] Fix validated successfully! Moving to PR creation...")
        return "pr_creator"
    
    # Safety limit: Max 3 total attempts (Investigator + Mechanic + Validator cycles)
    if iteration >= 3:
        print(f"\n[ERROR] Maximum attempts (3) reached. Validation still failing.")
        print(f"   Last errors: {validation_errors}")
        print(f"   Ending workflow without creating PR.")
        return "end"
    
    # Self-correction: Tests failed, loop back to Investigator
    print(f"\n[SELF-CORRECTION LOOP] Tests failed. Routing back to Investigator...")
    print(f"   Attempt: {iteration}/3")
    print(f"   Validation errors will be fed back for reconsideration.")
    return "investigator"


def create_sre_graph() -> StateGraph:
    """
    Build the complete LangGraph StateGraph with all nodes and edges.
    
    Nodes:
    - investigator: Analyzes logs and identifies root causes
    - mechanic: Generates code fixes
    - validator: Tests fixes and provides feedback
    - pr_creator: Opens GitHub Pull Requests
    
    Edges:
    - START → investigator
    - investigator → (conditional) → mechanic | investigator | END
    - mechanic → validator
    - validator → (conditional) → pr_creator | investigator | END
    - pr_creator → END
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the graph
    workflow = StateGraph(SREAgentState)
    
    # Add all nodes
    workflow.add_node("investigator", investigator_agent)
    workflow.add_node("mechanic", mechanic_agent)
    workflow.add_node("validator", validator_node)
    workflow.add_node("pr_creator", pr_creator_node)
    
    # Set entry point
    workflow.set_entry_point("investigator")
    
    # Add conditional edges
    
    # After Investigator: Decide whether to continue investigating or move to Mechanic
    workflow.add_conditional_edges(
        "investigator",
        should_continue_investigation,
        {
            "mechanic": "mechanic",      # Root cause found → generate fix
            "investigator": "investigator",  # Need more analysis → loop back
            "end": END                    # Max iterations → give up
        }
    )
    
    # After Mechanic: Always go to Validator
    workflow.add_edge("mechanic", "validator")
    
    # After Validator: THE SELF-CORRECTION LOOP
    # This is where the magic happens - tests fail → back to Investigator
    workflow.add_conditional_edges(
        "validator",
        should_continue_after_validation,
        {
            "pr_creator": "pr_creator",      # Tests passed → create PR
            "investigator": "investigator",  # Tests failed → retry with feedback
            "end": END                       # Max attempts → give up
        }
    )
    
    # After PR Creator: Workflow complete
    workflow.add_edge("pr_creator", END)
    
    # Compile the graph with memory (for state persistence)
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


def visualize_graph(output_file: str = "sre_agent_graph.png"):
    """
    Generate a visual representation of the graph.
    
    Requires: graphviz and pygraphviz
    Install: brew install graphviz && pip install pygraphviz
    
    Args:
        output_file: Path to save the graph visualization
    """
    try:
        from IPython.display import Image
        app = create_sre_graph()
        
        # Get the graph visualization
        graph_image = app.get_graph().draw_mermaid_png()
        
        with open(output_file, "wb") as f:
            f.write(graph_image)
        
        print(f"[SUCCESS] Graph visualization saved to {output_file}")
        return Image(graph_image)
    except ImportError:
        print("[WARNING] Graph visualization requires IPython. Skipping.")
    except Exception as e:
        print(f"[WARNING] Could not generate graph visualization: {e}")


# Create and export the compiled graph
sre_graph = create_sre_graph()


if __name__ == "__main__":
    """
    Test the graph structure (doesn't execute, just validates).
    """
    print("Self-Healing SRE Agent Graph")
    print("=" * 60)
    print("\nGraph Structure:")
    print("  START → Investigator")
    print("    ├─ (root cause found) → Mechanic")
    print("    ├─ (need more data)   → Investigator (loop)")
    print("    └─ (max iterations)   → END")
    print("\n  Mechanic → Validator")
    print("\n  Validator")
    print("    ├─ (tests passed)     → PR Creator → END [SUCCESS]")
    print("    ├─ (tests failed)     → Investigator (SELF-CORRECTION LOOP)")
    print("    └─ (max attempts)     → END [FAILED]")
    print("\n" + "=" * 60)
    print("[SUCCESS] Graph definition complete!")
    print("\n[INFO] The self-correction loop allows the agent to:")
    print("   1. Receive test failure feedback from Validator")
    print("   2. Route back to Investigator with error context")
    print("   3. Reconsider the root cause analysis")
    print("   4. Generate an improved fix")
    print("   5. Try again (up to 3 total attempts)")
    print("\nThis makes the agent resilient and able to self-heal!")
