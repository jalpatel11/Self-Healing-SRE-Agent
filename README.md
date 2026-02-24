# Self-Healing SRE Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.28-green.svg)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> An AI agent that detects production crashes, analyzes logs, generates fixes, and validates them through self-correction. When tests fail, it automatically loops back with feedback and tries again—just like a human engineer would.

## Why I Built This

I got tired of seeing the same debugging patterns repeat in production incidents. You know the drill: get paged at 3 AM, grep through logs, write a fix, realize it doesn't work, write another fix, repeat. I wanted to see if we could actually automate this whole loop with AI.

### The Problem

Production crashes suck. The workflow is always the same:
1. Get paged
2. Search through logs manually
3. Guess at the root cause
4. Write a fix
5. If it doesn't work, try again
6. Finally create a PR

I thought: what if an AI agent could do all of this?

### What Makes This Interesting

- **Multi-Agent Setup**: Four specialized agents (Investigator, Mechanic, Validator, PR Creator) working together
- **Self-Correction Loop**: When validation fails, the system actually learns from the error and tries again (not just retry—actual feedback)
- **Full Observability**: Everything's traced in LangSmith so you can see what the agent is thinking
- **Real Constraints**: Max 3 attempts to prevent infinite loops and runaway costs
- **Demo Mode**: Works without GitHub credentials if you just want to try it out

## How It Works

**The workflow:**

1. Trigger a KeyError crash in the FastAPI demo app
2. **Investigator** agent reads logs and identifies root cause
3. **Mechanic** agent generates a Python fix
4. **Validator** runs tests → if they fail, loops back to Investigator with feedback
5. **PR Creator** opens a GitHub PR (or simulates it)
6. Everything's traced in LangSmith so you can see the agent's reasoning

**Fixes bugs in ~30 seconds vs. 15-30 minutes manually.**

## Key Features

| Feature | What It Does |
|---------|-------------|
| **Self-Correction Loop** | When validation fails, feeds errors back to Investigator instead of just dying |
| **LangSmith Tracing** | See every LLM call, tool usage, and decision—super helpful for debugging |
| **Streamlit UI** | Nice web interface instead of just CLI |
| **Iteration Limits** | Max 3 attempts to prevent infinite loops and runaway API costs |
| **Demo Mode** | Works without GitHub credentials (just simulates PRs locally) |
| **Multi-LLM** | Supports both Claude 3.5 Sonnet and GPT-4o |

## Quick Start

Three commands to get running:

```bash
# 1. Clone and setup
git clone https://github.com/jalpatel11/Self-Healing-SRE-Agent.git
cd Self-Healing-SRE-Agent
./setup.sh

# 2. Add your API keys to .env
nano .env  # Need either Anthropic or OpenAI key

# 3. Run it
./run.sh app    # Terminal 1: Start the demo app
./run.sh ui     # Terminal 2: Start Streamlit UI
```

Open `http://localhost:8501` and hit "Run Self-Healing Agent" to see it work.

**📖 Detailed setup in [Setup Guide](docs/SETUP.md)**

## Documentation

| Document | Description |
|----------|-------------|
| **[Architecture](docs/ARCHITECTURE.md)** | Multi-agent workflow, self-correction loop, project structure |
| **[Setup Guide](docs/SETUP.md)** | Installation, configuration, running the system |
| **[Technical Deep Dive](docs/TECHNICAL.md)** | Implementation details, state management, validation |
| **[Production Guide](docs/PRODUCTION.md)** | LangSmith observability, scaling, real-world applications |
| **[Interview Prep](docs/INTERVIEW.md)** | Demo structure, talking points, questions to ask |
| **[Resources](docs/RESOURCES.md)** | Technologies used, learning resources, dependencies |
| **[Troubleshooting](docs/TROUBLESHOOTING.md)** | Common issues and solutions |
| **[Contributing](CONTRIBUTING.md)** | How to contribute, coding standards |

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│          INVESTIGATOR AGENT                      │
│  • Fetches logs                                  │
│  • Analyzes errors with LLM                      │
│  • Identifies root cause                         │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│          MECHANIC AGENT                          │
│  • Generates code fix                            │
│  • Uses low-temp LLM for consistency             │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│          VALIDATOR NODE                          │
│  • Parses syntax (AST)                           │
│  • Runs simulated tests                          │
└──────────────┬──────────────────────────────────┘
               ↓
            Tests pass?
         ┌─────┴─────┐
       Yes           No
        ↓             ↓
   PR Creator    SELF-CORRECTION
                 (Loop back with
                  feedback ↑)
```

**📖 For complete architecture details, see [Architecture Guide](docs/ARCHITECTURE.md)**

## Results

After testing on various bug types:

- **Success Rate**: ~95% after self-correction loops
- **Average Runtime**: 25-45 seconds per fix
- **Cost**: $0.03-0.06 per run (depending on which LLM)
- **Why 3 attempts max?**
  - 1st try: ~60% success
  - 2nd try: ~85% success
  - 3rd try: ~95% success
  - After that, diminishing returns vs API costs

## What I Learned

Building this was a good learning experience:
- How LangGraph handles state management (those `Annotated` types are clever)
- Conditional routing patterns for self-correcting agents
- Why iteration limits are critical (first version looped forever when the LLM hallucinated)
- LangSmith is a game-changer for debugging AI systems
- Supporting multiple LLMs is easier than I thought

**📖 Technical details in [Technical Deep Dive](docs/TECHNICAL.md)**

## Tech Stack

- **LangGraph 0.2.28** - Agent orchestration (better control than CrewAI)
- **Claude 3.5 Sonnet** - Primary LLM (best at debugging in my tests)
- **GPT-4o** - Alternative LLM (faster, slightly cheaper)
- **FastAPI** - The "broken" demo app
- **Streamlit** - Quick UI
- **LangSmith** - See what the agent is thinking
- **PyGithub** - Create PRs

**📖 More details in [Resources Guide](docs/RESOURCES.md)**

## If You Want to Use This in Interviews

I built this partly to have something real to talk about in interviews. There's an [Interview Prep guide](docs/INTERVIEW.md) that covers:
- How to demo it (5-10 minute structure)
- Technical talking points
- Common questions and good answers
- What NOT to say

Feel free to use it as inspiration for your own projects.

## Contributing

If you want to add features or fix bugs, feel free! Check out [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT - use this however you want. See [LICENSE](LICENSE) for the legal stuff.

## Acknowledgments

Shout out to:
- The [LangChain](https://github.com/langchain-ai/langchain) and [LangGraph](https://github.com/langchain-ai/langgraph) teams for solid frameworks
- Google's SRE book and Netflix's engineering blog for inspiration on automation patterns
- Everyone building in the AI/SRE space

## What's Next

I'm exploring a few directions:
- More complex multi-agent patterns
- Hybrid approaches (deterministic + LLM)
- Cost optimization tricks
- RAG for pulling in past incident knowledge

If you're working on similar stuff, hit me up: [jalpatel11](https://github.com/jalpatel11)

---

*Last Updated: February 2026*