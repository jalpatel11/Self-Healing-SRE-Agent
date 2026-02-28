"""
Agent nodes for the Self-Healing SRE Agent.

This module contains the core agent logic:
1. Investigator Agent: Analyzes logs and identifies root causes
2. Mechanic Agent: Generates code fixes for identified issues
3. Validator Node: Tests the fix and routes back if tests fail
4. PR Creator Node: Opens GitHub Pull Request with the fix
"""

from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from state import SREAgentState
from tools import fetch_logs, run_tests, open_github_pr


def get_llm(temperature: float = 0):
    """Return the configured LLM client based on LLM_PROVIDER setting."""
    if settings.llm_provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=temperature,
        )
    elif settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            google_api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            temperature=temperature,
        )
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def invoke_with_retry(llm, messages):
    """Invoke the LLM with automatic retry on transient failures."""
    return llm.invoke(messages)


def investigator_agent(state: SREAgentState) -> dict:
    """
    Investigator Agent: Analyzes logs to identify the root cause of errors.
    
    This agent:
    1. Calls the fetch_logs tool to retrieve application logs
    2. Analyzes the logs using LLM reasoning
    3. Identifies the root cause and sets root_cause_identified=True
    4. Prepares a detailed analysis for the Mechanic Agent
    
    The agent can be called multiple times if initial analysis is insufficient.
    
    Args:
        state: Current agent state
    
    Returns:
        Partial state update with analysis results
    """
    print("\n[INVESTIGATOR]  Starting log analysis...")

    # Check iteration count
    iteration = state.get("iteration_count", 0) + 1
    print(f"   Iteration: {iteration}/{settings.max_iterations}")
    
    llm = get_llm()
    llm_with_tools = llm.bind_tools([fetch_logs])
    
    # Build the investigation prompt
    system_prompt = """You are an expert Site Reliability Engineer specializing in debugging production issues.

Your task is to analyze application logs, identify the root cause of errors, and provide a clear explanation.

Steps:
1. Use the fetch_logs tool to retrieve recent error logs
2. Carefully analyze the stack traces, error messages, and context
3. Identify the specific line of code causing the issue
4. Determine the root cause (e.g., missing dictionary key, null pointer, type mismatch)
5. Provide a clear, concise explanation of what went wrong and why

Be thorough but focused. Your analysis will be used by another agent to generate a fix."""

    # Check if we have previous test failures to consider
    validation_errors = state.get("validation_errors", [])
    if validation_errors:
        additional_context = f"""
        
IMPORTANT: A previous fix attempt failed with these test errors:
{chr(10).join(f"- {error}" for error in validation_errors)}

Please reconsider the root cause analysis with this feedback in mind. The previous fix didn't work correctly."""
        system_prompt += additional_context
    
    messages = [
        SystemMessage(content=system_prompt),
        *state["messages"]
    ]
    
    # First LLM call: Agent decides to use fetch_logs tool
    print("   Fetching logs...")
    response = llm_with_tools.invoke(messages)
    
    # Check if the model wants to use tools
    if response.tool_calls:
        # Execute the tool calls
        tool_results = []
        for tool_call in response.tool_calls:
            if tool_call["name"] == "fetch_logs":
                args = tool_call.get("args", {})
                logs = fetch_logs.invoke(args)
                tool_results.append(logs)
        
        logs_content = "\n\n".join(tool_results)
        print(f"   Retrieved {len(logs_content)} characters of logs")
        
        # Second LLM call: Analyze the logs
        print("   Analyzing logs with LLM...")
        analysis_messages = [
            SystemMessage(content=system_prompt),
            *state["messages"],
            response,
            HumanMessage(content=f"Here are the logs:\n\n{logs_content}\n\nNow analyze these logs and identify the root cause.")
        ]
        
        analysis_response = llm.invoke(analysis_messages)
        analysis_text = analysis_response.content
    else:
        # Model responded without using tools (shouldn't happen, but handle it)
        analysis_text = response.content
        logs_content = ""
    
    # Determine if root cause is identified
    # Look for confidence indicators in the response
    root_cause_found = any(
        phrase in analysis_text.lower()
        for phrase in [
            "root cause",
            "the issue is",
            "the error occurs because",
            "keyerror",
            "missing key",
            "the bug is"
        ]
    )
    
    print(f"   Root cause identified: {root_cause_found}")
    
    if root_cause_found:
        print(f"   [SUCCESS] Root cause found: {analysis_text[:100]}...")
    else:
        print("   [WARNING] Root cause unclear, may need another iteration")
    
    return {
        "messages": [AIMessage(content=f"Investigation Result:\n\n{analysis_text}")],
        "error_logs": logs_content if logs_content else state.get("error_logs", ""),
        "root_cause_identified": root_cause_found,
        "root_cause_analysis": analysis_text,
        "iteration_count": iteration
    }


def mechanic_agent(state: SREAgentState) -> dict:
    """
    Mechanic Agent: Generates code fixes for identified issues.
    
    This agent:
    1. Takes the root cause analysis from the Investigator
    2. Generates a code fix that addresses the issue
    3. Provides the complete fixed code (not just a diff)
    4. Explains what was changed and why
    
    If validation fails, this agent is called again with feedback.
    
    Args:
        state: Current agent state
    
    Returns:
        Partial state update with generated fix code
    """
    print("\n[MECHANIC] Generating code fix...")
    
    llm = get_llm()
    
    root_cause = state.get("root_cause_analysis", "")
    validation_errors = state.get("validation_errors", [])
    
    # Build the fix generation prompt
    system_prompt = """You are an expert Python developer specializing in fixing production bugs.

Your task is to generate a corrected version of the buggy code based on the root cause analysis.

Requirements:
1. Provide the COMPLETE fixed code for the app.py file, not just a snippet
2. Fix the specific issue identified in the root cause analysis
3. Use defensive programming practices (e.g., .get() instead of direct dict access)
4. Preserve all other functionality
5. Ensure the code is clean, readable, and follows Python best practices
6. Add comments explaining the fix

The response should be the FULL corrected code that can replace the current app.py file."""

    if validation_errors:
        system_prompt += f"""

WARNING: Your previous fix failed validation with these errors:
{chr(10).join(f"- {error}" for error in validation_errors)}

Please generate a NEW fix that addresses these validation failures."""
    
    # Read the original buggy code
    try:
        with open("app.py", "r") as f:
            original_code = f.read()
    except Exception:
        original_code = "[Could not read original app.py file]"
    
    prompt = f"""Root Cause Analysis:
{root_cause}

Original Buggy Code:
```python
{original_code}
```

Please provide the COMPLETE fixed version of app.py that solves this issue.
Respond with ONLY the Python code, no explanations before or after."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ]
    
    print("   Generating fix with LLM...")
    response = llm.invoke(messages)
    fix_code = response.content
    
    # Extract code if wrapped in markdown code blocks
    if "```python" in fix_code:
        fix_code = fix_code.split("```python")[1].split("```")[0].strip()
    elif "```" in fix_code:
        fix_code = fix_code.split("```")[1].split("```")[0].strip()
    
    print(f"   [SUCCESS] Generated fix ({len(fix_code)} characters)")
    print(f"   Preview: {fix_code[:150]}...")
    
    return {
        "messages": [AIMessage(content="I've generated a fix for the issue. The code addresses the root cause by implementing proper error handling.")],
        "fix_code": fix_code,
        "fix_validated": False,  # Will be set by validator
        "validation_errors": []  # Clear previous errors
    }


def validator_node(state: SREAgentState) -> dict:
    """
    Validator Node: Tests the generated fix and determines next steps.
    
    This node acts like a CI/CD pipeline:
    1. Runs static analysis on the fix code
    2. Simulates pytest execution
    3. Validates that the fix addresses the root cause
    4. Routes back to Investigator if tests fail
    5. Proceeds to PR creation if tests pass
    
    This creates the self-correction loop that makes the agent resilient.
    
    Args:
        state: Current agent state
    
    Returns:
        Partial state update with validation results
    """
    print("\n[VALIDATOR] Testing the generated fix...")
    
    fix_code = state.get("fix_code", "")
    
    if not fix_code:
        print("   [ERROR] No fix code to validate!")
        return {
            "fix_validated": False,
            "validation_errors": ["No fix code provided"],
            "messages": [AIMessage(content="Validation failed: No fix code to test")]
        }
    
    # Read original code for comparison
    try:
        with open("app.py", "r") as f:
            original_code = f.read()
    except Exception:
        original_code = ""
    
    # Run the tests
    print("   Running tests (simulated pytest)...")
    test_result = run_tests.invoke({
        "fix_code": fix_code,
        "original_code": original_code
    })
    
    passed = test_result["passed"]
    message = test_result["message"]
    errors = test_result["errors"]
    
    if passed:
        print("   [SUCCESS] All tests passed!")
        print(f"   {message}")
        return {
            "fix_validated": True,
            "validation_errors": [],
            "messages": [AIMessage(content=f"[VALIDATION SUCCESS] {message}")]
        }
    else:
        print(f"   [ERROR] Tests failed: {message}")
        for error in errors:
            print(f"      - {error}")
        
        return {
            "fix_validated": False,
            "validation_errors": errors,
            "messages": [AIMessage(content="[VALIDATION FAILED]\n" + "\n".join(errors))]
        }


def pr_creator_node(state: SREAgentState) -> dict:
    """
    PR Creator Node: Opens a GitHub Pull Request with the validated fix.
    
    This is the final node in the success path:
    1. Prepares PR title and description
    2. Calls the open_github_pr tool
    3. Updates state with PR status and URL
    
    Args:
        state: Current agent state
    
    Returns:
        Partial state update with PR creation results
    """
    print("\n[PR CREATOR] Opening GitHub Pull Request...")
    
    fix_code = state.get("fix_code", "")
    root_cause = state.get("root_cause_analysis", "Unknown root cause detected")

    # Dynamic title — capped at 72 chars for clean git log display
    title = f"[Automated Fix] {root_cause[:72]}"

    validation_errors = state.get("validation_errors", [])
    test_summary = (
        "All automated tests passed (syntax + function-signature validation)."
        if not validation_errors
        else f"Passed after {state.get('iteration_count', 1)} iteration(s)."
    )

    body = f"""## Automated Fix by Self-Healing SRE Agent

This PR was automatically generated after detecting and analyzing a production error.

### Root Cause Analysis
{root_cause}

### Changes Made
The agent generated a fix addressing the root cause above using defensive
Python patterns (e.g. `.get()` instead of direct dict access, proper
exception handling).

### Validation
{test_summary}

### ⚠️ Human Review Required
This PR was created automatically. Please review carefully before merging.

---
*Generated by Self-Healing SRE Agent*
*Timestamp: {datetime.now(timezone.utc).isoformat()}*
*Iterations: {state.get("iteration_count", 1)}*
"""
    
    # Call the tool to create PR
    pr_result = open_github_pr.invoke({
        "title": title,
        "body": body,
        "fix_code": fix_code,
        "file_path": "app.py"
    })
    
    # Check if PR was created successfully
    if "[SUCCESS]" in pr_result or "PR URL:" in pr_result or "Simulated PR" in pr_result:
        print("   [SUCCESS] Pull Request created successfully!")
        return {
            "pr_status": "created",
            "pr_url": pr_result,
            "messages": [AIMessage(content=f"Pull Request created:\n\n{pr_result}")]
        }
    else:
        print("   [ERROR] Pull Request creation failed")
        return {
            "pr_status": "failed",
            "pr_url": pr_result,
            "messages": [AIMessage(content=f"PR creation failed:\n\n{pr_result}")]
        }
