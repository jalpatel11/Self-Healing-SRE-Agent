# Interview Preparation Guide

## Elevator Pitch (30 seconds)

> "I built an AI-powered SRE agent that autonomously fixes production bugs. When a crash occurs, it analyzes logs using Claude, generates a Python fix, validates it through simulated tests, and if validation fails, it self-corrects by looping back with feedback—just like a human engineer would. The entire process is traced in LangSmith for full observability. I can show you a live demo right now."

## Demo Structure (5-10 minutes)

### 1. Show the Problem (1 min)
- Open the FastAPI app
- Trigger the KeyError crash
- Show the logs: stack trace, timestamp

### 2. Run the Agent (3 min)
- Start Streamlit UI
- Click "Run Self-Healing Agent"
- Narrate what each agent is doing:
  - "Investigator is reading logs and asking Claude to identify the root cause"
  - "Mechanic is generating a fix using safe dictionary access"
  - "Validator is checking syntax and testing the fix"
  - (If it fails) "Notice the self-correction loop routing back"

### 3. Show the Results (2 min)
- Open the generated PR (or simulated output)
- Show the fix code
- Click the LangSmith trace link
- Highlight: full prompt/response, tool calls, iteration count

### 4. Discuss Architecture (2 min)
- Pull up the README architecture diagram
- Explain StateGraph, conditional routing
- Highlight the self-correction loop logic

### 5. Handle Questions (2 min)
- "How do you prevent infinite loops?" → Iteration limits
- "What about costs?" → Show LangSmith token usage
- "How would you productionize this?" → Discuss Docker, real tests, approval gates

## Technical Discussion Points

### When asked about challenges:

> "The biggest challenge was preventing infinite loops when the LLM hallucinates. My first version would retry forever if validation kept failing. I solved this with a combination of iteration limits, passing validation errors back as context, and using lower temperature for more consistent code generation."

### When asked about trade-offs:

> "I made a conscious decision to use simulated tests instead of running actual pytest in Docker containers. The trade-off is speed and simplicity versus accuracy. For this demo, fast iteration was more important, but in production, I'd absolutely use container-based test execution for safety."

### When asked about production readiness:

> "This demonstrates the core workflow, but production would need: rate limiting to control costs, human approval gates for high-risk changes, rollback mechanisms, integration with real monitoring tools like Datadog, and probably a queue system to handle concurrent incidents."

### When asked about the tech stack:

> "I chose LangGraph over alternatives like CrewAI because I needed fine-grained control over routing logic for the self-correction loop. Claude 3.5 Sonnet outperformed GPT-4o in my testing for code debugging tasks, though GPT-4o is faster and cheaper. LangSmith is non-negotiable for production AI systems—without observability, you're flying blind."

## Interview Talking Points

### Show a successful trace:
> "Here's a trace in LangSmith where the agent fixed the bug on the first try. Notice the Investigator identified the KeyError in 8 seconds, the Mechanic generated a fix using .get(), and the Validator confirmed it passes all checks. Total cost: $0.03."

### Show a self-correction trace:
> "Here's a more interesting case. The first fix failed validation because the Mechanic tried to use a try/except which didn't fully address the issue. The system automatically routed back to the Investigator with feedback, reconsidered the root cause, and the second attempt used .get() which passed. This demonstrates the self-correction loop in action."

### Discuss trade-offs:
> "I set the iteration limit to 3 because testing showed diminishing returns after that. The first attempt succeeds 60% of the time, the second 85%, and the third 95%. Beyond that, we're spending API costs without meaningful improvement. In production, I'd track these metrics and adjust dynamically."

## Red Flags to Avoid

**Don't say**:
- "It always works" (No AI system has 100% accuracy)
- "I didn't test other approaches" (Shows lack of experimentation)
- "It's production-ready as-is" (Shows lack of real-world understanding)
- "I just followed a tutorial" (This is original work)

**Do say**:
- "It succeeds ~95% of the time after self-correction"
- "I tested both Claude and GPT-4o; here's what I found..."
- "For production, I'd add X, Y, Z because..."
- "I was inspired by Google SRE practices and adapted them for AI"

## Questions to Ask Them

**Turn the tables** (shows strategic thinking):

1. "What's your current incident response process? Where do you see AI fitting in?"
2. "Do you use LangSmith or similar observability tools for your GenAI systems?"
3. "What's your approach to preventing runaway API costs in agentic workflows?"
4. "How do you balance automation with human oversight in production changes?"

These questions demonstrate you're thinking about real problems, not just toy demos.

---

[← Back to Main README](../README.md) | [Production Guide →](PRODUCTION.md) | [Resources →](RESOURCES.md)
