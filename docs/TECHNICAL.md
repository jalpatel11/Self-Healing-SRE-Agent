# Technical Deep Dive

## The Self-Correction Loop (The Core Innovation)

This is what turns a simple agent into a production-grade system.

**Implementation**: [graph.py](../graph.py#L60-L75)

```python
def should_continue_after_validation(state: SREAgentState) -> Literal["pr_creator", "investigator", "end"]:
    """
    The self-correction routing logic.
    
    Flow:
    - Tests passed → Success! Create PR
    - Tests failed + attempts < 3 → Loop back with feedback
    - Tests failed + attempts >= 3 → Give up gracefully
    """
    if state["fix_validated"]:
        print("[SUCCESS] Fix validated! Proceeding to PR creation")
        return "pr_creator"
    
    if state["iteration_count"] >= 3:
        print("[ERROR] Maximum attempts reached. Manual intervention required.")
        return "end"
    
    # KEY: Send validation errors back to Investigator
    print(f"[SELF-CORRECTION LOOP] Attempt {state['iteration_count']} failed. Routing back...")
    return "investigator"  # Try again with new information
```

**Why this matters:**

1. **Real-world debugging isn't linear** - Engineers iterate, get feedback, adjust
2. **LLMs make mistakes** - A single pass rarely produces perfect code
3. **Feedback improves accuracy** - Each iteration is informed by previous failures
4. **Cost control** - 3 attempts balances success rate vs. API costs

**What I learned:** The first version looped infinitely when the LLM hallucinated. Adding iteration limits and passing validation errors back as context massively improved success rates.

## State Management Architecture

**Implementation**: [state.py](../state.py)

LangGraph uses a reducer pattern for state updates. The key is the `Annotated` type with `operator.add`:

```python
from typing import TypedDict, Annotated, Sequence
from operator import add
from langchain_core.messages import BaseMessage

class SREAgentState(TypedDict):
    # Messages automatically append (no manual list management!)
    messages: Annotated[Sequence[BaseMessage], add]
    
    # Control flow booleans
    root_cause_identified: bool
    fix_validated: bool
    
    # Iteration tracking (prevents infinite loops)
    iteration_count: int
    
    # Data passed between agents
    error_logs: str
    root_cause_analysis: str
    fix_code: str
    validation_errors: list[str]
    
    # Final results
    pr_status: str
    pr_url: str
    error_timestamp: str
```

**Key insight:** The `Annotated[Sequence[BaseMessage], add]` means messages are automatically appended without manual `+` operators. This is critical for maintaining conversation history across agents.

## Agent Design Patterns

Each agent follows a consistent pattern:

```python
def agent_node(state: SREAgentState) -> dict:
    """
    1. Read current state
    2. Perform specialized task
    3. Return state updates (not full state!)
    """
    # Get what we need from state
    relevant_data = state["some_field"]
    
    # Do work (call LLM, run tools, etc.)
    result = do_specialized_work(relevant_data)
    
    # Return ONLY the fields we're updating
    return {
        "messages": [AIMessage(content=result)],
        "some_field": result,
        "iteration_count": state["iteration_count"] + 1
    }
```

**Why partial updates?** LangGraph merges returned dict with existing state. Returning full state causes bugs and unnecessary complexity.

## The Intentional Bug

**Location**: [app.py](../app.py#L103-L120)

I intentionally created a KeyError that only triggers with a specific header:

```python
@app.get("/api/data")
def get_data(request: Request):
    x_trigger_bug = request.headers.get("X-Trigger-Bug")
    
    # Dictionary missing "api_key"
    user_config = {
        "user_id": 12345,
        "username": "demo_user",
        "preferences": {"theme": "dark"}
        # Intentionally missing: "api_key"
    }
    
    if x_trigger_bug and x_trigger_bug.lower() == "true":
        # This will crash!
        api_key = user_config["api_key"]  # KeyError
    
    return {"status": "ok"}
```

**The expected fix** the agent should generate:

```python
# Option 1: Use .get() with default
api_key = user_config.get("api_key", "default_key")

# Option 2: Check existence first
if "api_key" in user_config:
    api_key = user_config["api_key"]
else:
    api_key = "default_key"
```

**Why this bug?** It's:
- Simple enough for an LLM to understand
- Common in real production code
- Easy to validate programmatically
- Representative of real errors (KeyError is one of the most common Python exceptions)

## Validation Strategy

**Implementation**: [tools.py](../tools.py#L40-L80)

The validator uses AST parsing to check for common fixes:

```python
@tool
def run_tests(fix_code: str) -> str:
    """
    Simulates pytest by checking:
    1. Syntax validity (AST parsing)
    2. Presence of safe dictionary access patterns
    3. Proper error handling
    """
    try:
        tree = ast.parse(fix_code)
    except SyntaxError as e:
        return f"[ERROR] Syntax error: {e}"
    
    # Look for .get() method or 'in' checks
    has_safe_access = any([
        ".get(" in fix_code,
        " in user_config" in fix_code,
        "KeyError" in fix_code  # try/except
    ])
    
    if not has_safe_access:
        return "[ERROR] Fix doesn't use safe dictionary access"
    
    return "[SUCCESS] All tests passed"
```

**Trade-off:** Real validation would run actual tests in containers. This simulated approach:
- **Pros**: Fast, no Docker overhead, safe
- **Cons**: Can't catch runtime errors, limited checks

**For production:** Replace with actual test execution in isolated environments.

## LLM Provider Abstraction

**Implementation**: [agents.py](../agents.py#L10-L20)

Supporting multiple LLMs future-proofs the system:

```python
def get_llm():
    """Factory pattern for LLM selection"""
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    
    if provider == "anthropic":
        return ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0.1  # Low temp for consistent code generation
        )
    else:
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0.1
        )
```

**Why Claude 3.5 Sonnet?** Testing showed it outperforms GPT-4o for:
- Code debugging tasks
- Understanding stack traces
- Generating syntactically correct Python

**Cost comparison:**
- Claude 3.5 Sonnet: ~$3 per million tokens (input)
- GPT-4o: ~$2.5 per million tokens (input)
- Typical run: ~10K tokens = $0.03-0.04

## LangSmith: The Observability Game-Changer

**Setup**: [main.py](../main.py#L15-L25)

```python
# Automatically enabled if env vars are set
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "SRE-Self-Healing-Agent"
```

**What you get for free:**
1. Every LLM prompt and response
2. Tool invocations with inputs/outputs
3. Latency metrics for each step
4. Token usage and estimated costs
5. Error tracking and retry logic
6. Visual workflow graph

**Interview tip:** When presenting this project, show:
- A successful run in LangSmith
- A failed run that self-corrected
- Token usage breakdown
- How you debugged an issue using traces

**This proves you understand production AI systems**, not just toy demos.

---

[← Back to Main README](../README.md) | [Architecture →](ARCHITECTURE.md) | [Production Guide →](PRODUCTION.md)
