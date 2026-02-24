# Self-Healing SRE Agent 🤖

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.28-green.svg)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent AI-powered agent that automatically detects crashes, analyzes logs to find root causes, generates fixes, validates them through a **self-correction loop**, and creates GitHub Pull Requests—all while being observable via LangSmith tracing.

## 🎯 Overview

This project demonstrates an advanced agentic workflow using **LangGraph** to orchestrate multiple AI agents that work together autonomously:

1. **🔍 Detect & Investigate** - Analyze logs using AI to identify root causes
2. **🔧 Generate Fix** - Create code fixes for identified issues
3. **✅ Validate & Self-Correct** - Test fixes and loop back if they fail (up to 3 attempts)
4. **📝 Create PR** - Open GitHub Pull Requests with validated fixes
5. **📊 Observe** - Track everything in LangSmith for interviews/debugging

### 🌟 Key Features

- **Self-Correction Loop**: If validation fails, routes back to Investigator with feedback
- **LangSmith Integration**: Full observability of agent decision-making
- **Streamlit UI**: Beautiful web interface for demos and interviews
- **Demo Mode**: Works without GitHub credentials (simulates PRs)
- **Iteration Limits**: Maximum 3 attempts to prevent infinite loops and API costs

## 🏗️ Architecture

### Agent Workflow with Self-Correction Loop

```
                     START
                       ↓
              ┌────────────────┐
              │  Investigator  │←──────┐
              │     Agent      │       │
              │                │       │
              │ • Fetch logs   │       │
              │ • Analyze      │       │
              │ • Find root    │       │
              │   cause        │       │
              └────────┬───────┘       │
                       ↓               │
           ┌──────────────────────┐   │
           │ Root cause found?    │   │
           └──────────┬───────────┘   │
                      ↓               │
            Yes ─────→ Mechanic       │
            No ──→ Retry (max 3x)     │
                      ↓               │
              ┌────────────────┐      │
              │    Mechanic    │      │
              │     Agent      │      │
              │                │      │
              │ • Generate fix │      │
              │ • Full code    │      │
              └────────┬───────┘      │
                       ↓              │
              ┌────────────────┐      │
              │   Validator    │      │
              │     Node       │      │
              │                │      │
              │ • Run tests    │      │
              │ • Check syntax │      │
              └────────┬───────┘      │
                       ↓              │
           ┌──────────────────────┐  │
           │   Tests passed?      │  │
           └──────────┬───────────┘  │
                      ↓              │
            Yes ─────→ PR Creator    │
            No ──→ LOOP BACK ────────┘
                   (Self-Correction)
                      ↓
              ┌────────────────┐
              │  PR Creator    │
              │                │
              │ • Open PR      │
              │ • Commit fix   │
              └────────┬───────┘
                       ↓
                      END
```

### Why Self-Correction Matters

Traditional agents fail once and stop. This agent:
- Receives test failure feedback from the Validator
- Routes back to the Investigator with error details
- Reconsiders its root cause analysis
- Generates an improved fix
- Tries again (up to 3 times)

**This mimics how human engineers actually debug!**

## 📁 Project Structure

```
Self-Healing-SRE-Agent/
├── 📱 Core Application
│   ├── app.py              # FastAPI app with intentional KeyError bug
│   ├── test_app.py         # Script to trigger the bug
│   └── app_logs.txt        # Generated log file (gitignored)
│
├── 🧠 Agent System
│   ├── state.py            # LangGraph state TypedDict
│   ├── agents.py           # All agent nodes (Investigator, Mechanic, Validator, PR Creator)
│   ├── tools.py            # Tools (fetch_logs, run_tests, open_github_pr)
│   └── graph.py            # LangGraph StateGraph with self-correction loop
│
├── 🚀 Entry Points
│   ├── main.py             # CLI runner
│   ├── ui.py               # Streamlit web interface
│   ├── setup.sh            # Automated setup script
│   └── run.sh              # Convenience run script
│
├── ⚙️ Configuration
│   ├── .env                # Environment variables (gitignored)
│   ├── .env.example        # Template with all required vars
│   ├── requirements.txt    # Python dependencies
│   └── .gitignore          # Git exclusions
│
└── 📚 Documentation
    ├── README.md           # This file
    └── LICENSE             # MIT License
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **API Keys**: At least one of:
  - OpenAI API Key (for GPT-4o)
  - Anthropic API Key (for Claude 3.5 Sonnet) - Recommended
- **Optional but Highly Recommended**:
  - LangSmith API Key (for tracing - essential for interviews!)
  - GitHub Personal Access Token (for real PR creation)

### Installation

#### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/jalpatel11/Self-Healing-SRE-Agent.git
cd Self-Healing-SRE-Agent

# Run setup script
chmod +x setup.sh
./setup.sh

# Edit .env with your API keys
nano .env  # or use your favorite editor
```

#### Option 2: Manual Setup

```bash
# Clone the repository
git clone https://github.com/jalpatel11/Self-Healing-SRE-Agent.git
cd Self-Healing-SRE-Agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys
```

### Configuration

Edit `.env` file with your API keys:

```bash
# Required: Choose one
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...

# Highly Recommended: For observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_PROJECT=SRE-Self-Healing-Agent

# Optional: For real GitHub PRs
GITHUB_TOKEN=ghp_...
GITHUB_REPO=your-username/your-repo
```

### Running the Demo

#### Method 1: Streamlit UI (Best for Demos)

#### Method 1: Streamlit UI (Best for Demos)

**Terminal 1** - Start FastAPI:
```bash
./run.sh app
# Or: python app.py
```

**Terminal 2** - Start Streamlit UI:
```bash
./run.sh ui
# Or: streamlit run ui.py
```

Then:
1. Open browser to `http://localhost:8501`
2. Click "🔥 Trigger System Crash"
3. Click "🚀 Run Self-Healing Agent"
4. Watch the workflow execute in real-time!
5. See the self-correction loop in action when tests fail

#### Method 2: Command Line

**Terminal 1** - Start FastAPI:
```bash
./run.sh app
```

**Terminal 2** - Run the agent:
```bash
./run.sh main
# Or: python main.py
```

Follow the interactive prompts to trigger crash and run the workflow.

#### Method 3: Just Test the Bug

```bash
# Terminal 1: Start app
./run.sh app

# Terminal 2: Trigger the bug
./run.sh test
# Or: python test_app.py
```

## 📝 Implementation Status

### ✅ Phase 1: Foundation (COMPLETE)

- [x] **state.py** - TypedDict state schema with all required fields
  - Messages with automatic appending (`Annotated[..., add]`)
  - Investigation phase tracking
  - Validation and self-correction state
  - PR creation status
  
- [x] **app.py** - FastAPI with crashable route
  - Intentional KeyError bug: `user_config["api_key"]`
  - Triggered by `X-Trigger-Bug: true` header
  - Comprehensive logging to `app_logs.txt`
  - Custom exception handlers

### ✅ Phase 2: Agent System (COMPLETE)

- [x] **tools.py** - Tool implementations
  - `fetch_logs`: Read and filter application logs
  - `run_tests`: Validate fixes with simulated pytest
  - `open_github_pr`: Create PRs (real or simulated)

- [x] **agents.py** - All agent nodes
  - **Investigator Agent**: Analyzes logs, identifies root causes
  - **Mechanic Agent**: Generates code fixes
  - **Validator Node**: Tests fixes and provides feedback
  - **PR Creator Node**: Opens GitHub Pull Requests

- [x] **graph.py** - LangGraph orchestration
  - StateGraph with conditional routing
  - **Self-Correction Loop**: Validator → Investigator on test failure
  - Maximum 3 attempts to prevent infinite loops
  - Memory persistence with MemorySaver

### ✅ Phase 3: User Experience (COMPLETE)

- [x] **main.py** - CLI runner with interactive prompts
- [x] **ui.py** - Streamlit web interface
  - Real-time workflow visualization
  - One-click crash triggering
  - LangSmith trace links
  - Configuration status dashboard
- [x] **setup.sh** & **run.sh** - Convenience scripts

### ✅ Phase 4: Observability (COMPLETE)

- [x] LangSmith integration for full tracing
- [x] Environment configuration
- [x] Real-time progress monitoring
- [x] Iteration counting and limits

## 🧠 Technical Deep Dive

### The Self-Correction Loop

The key innovation is the routing logic in [graph.py](graph.py):

```python
def should_continue_after_validation(state: SREAgentState) -> Literal["pr_creator", "investigator", "end"]:
    """
    Routes based on validation results:
    - Tests passed → Create PR
    - Tests failed + attempts < 3 → Loop back to Investigator
    - Tests failed + attempts >= 3 → Give up
    """
    if state["fix_validated"]:
        return "pr_creator"  # Success!
    
    if state["iteration_count"] >= 3:
        return "end"  # Max attempts reached
    
    # Self-correction: Feed validation errors back
    return "investigator"
```

**Why this matters**: Traditional agents fail once and stop. This agent learns from its mistakes!

### State Management

The [state.py](state.py) uses LangGraph's state reducer pattern:

```python
class SREAgentState(TypedDict):
    # Auto-append with operator.add
    messages: Annotated[Sequence[BaseMessage], add]
    
    # Control flow
    root_cause_identified: bool
    fix_validated: bool
    iteration_count: int
    
    # Data
    error_logs: str
    root_cause_analysis: str
    fix_code: str
    validation_errors: list[str]
    
    # Results
    pr_status: str
    pr_url: str
```

### The Bug

**Location**: [app.py](app.py#L103-L120)

```python
user_config = {
    "user_id": 12345,
    "username": "demo_user",
    "preferences": {...}
    # Missing: "api_key"  ← THE BUG
}

if x_trigger_bug and x_trigger_bug.lower() == "true":
    api_key = user_config["api_key"]  # KeyError!
```

**Expected Fix**:
```python
api_key = user_config.get("api_key", "default_key")
# OR
if "api_key" in user_config:
    api_key = user_config["api_key"]
```

## 📊 LangSmith Observability

### Why LangSmith is Essential

When you interview for GenAI roles, you **MUST** show:
1. **How your agent thinks** - What reasoning did it use?
2. **Tool usage** - Which tools were called and why?
3. **Self-correction** - How did it recover from failures?
4. **Performance** - Latency, token usage, costs

LangSmith provides all of this automatically!

### Setup LangSmith

1. **Get API Key**: https://smith.langchain.com/ (free tier available)
2. **Add to .env**:
   ```bash
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=lsv2_pt_...
   LANGCHAIN_PROJECT=SRE-Self-Healing-Agent
   ```
3. **Run your agent** - traces appear automatically!
4. **Open dashboard**: View complete execution trace

### What You'll See

- 🔍 Each LLM call with prompts and responses
- 🛠️ Tool invocations with inputs and outputs
- 🔄 The self-correction loop in action
- ⏱️ Timing and performance metrics
- 💰 Token usage and estimated costs

**This is your proof of expertise!**

## 🎯 Use Cases & Extensions

### Current Demo

- Simulated production crash (KeyError)
- Log analysis
- Automated fix generation
- Self-correction on validation failure
- GitHub PR creation (real or simulated)

### Real-World Extensions

1. **Production Integration**
   - Connect to real monitoring (Datadog, Prometheus)
   - Trigger on actual alerts
   - Deploy fixes via CI/CD

2. **Multi-Language Support**
   - Add parsers for other languages
   - Language-specific test validation
   - Different fix patterns per language

3. **Human-in-the-Loop**
   - Add approval gates before PR creation
   - Allow human feedback on fixes
   - Learn from human corrections

4. **Advanced Validation**
   - Run actual unit tests in containers
   - Integration test validation
   - Performance regression checks

5. **Escalation**
   - Create Jira tickets for complex issues
   - Page on-call engineers
   - Automatic rollback triggers

## 🛠️ Technologies Used

| Technology | Purpose | Why This Choice |
|------------|---------|-----------------|
| **LangGraph** | Agent orchestration | Best-in-class for stateful agent workflows |
| **LangChain** | LLM abstraction | Industry standard, great tooling |
| **FastAPI** | Demo application | Modern, fast, easy to crash intentionally |
| **Streamlit** | Web UI | Quick beautiful UIs for demos |
| **Claude 3.5 Sonnet** | LLM reasoning | Superior reasoning for debugging tasks |
| **GPT-4o** | Alternative LLM | Fast, reliable, good for production |
| **LangSmith** | Observability | Essential for debugging and interviews |
| **PyGithub** | GitHub API | Official library for PR creation |

## 🎓 Learning Resources

### LangGraph
- [Official Docs](https://langchain-ai.github.io/langgraph/)
- [Agentic Workflows Tutorial](https://python.langchain.com/docs/use_cases/agent_workflows)
- [State Management Guide](https://langchain-ai.github.io/langgraph/concepts/low_level/#state-management)

### Observability
- [LangSmith Docs](https://docs.smith.langchain.com/)
- [Tracing Setup](https://docs.smith.langchain.com/tracing)

### SRE & Observability
- [Google SRE Book](https://sre.google/sre-book/table-of-contents/)
- [Observability Engineering](https://www.oreilly.com/library/view/observability-engineering/9781492076438/)

## 🎤 Interview Tips

When presenting this project:

1. **Start with the demo** - Show the Streamlit UI in action
2. **Explain the self-correction loop** - This is your differentiator
3. **Show LangSmith traces** - Prove you understand observability
4. **Discuss trade-offs**:
   - Why 3 attempts max? (Cost vs. success rate)
   - Why route to Investigator instead of directly to Mechanic? (Fresh analysis)
   - Real vs. simulated tests? (Speed vs. accuracy)
5. **Talk about production readiness**:
   - Rate limiting for API costs
   - Human approval gates
   - Rollback mechanisms
   - Monitoring the monitor

## 🤝 Contributing

This is a learning/portfolio project, but contributions are welcome!

Areas for improvement:
- [ ] Add more bug types (null pointers, type errors, etc.)
- [ ] Support multiple programming languages
- [ ] Real pytest execution in Docker containers
- [ ] Add more sophisticated routing logic
- [ ] Implement rollback mechanisms
- [ ] Add performance benchmarks

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Inspired by real SRE challenges
- Designed for demonstrating GenAI engineering skills

---

## 🚀 Status

**✅ Production Ready for Portfolio/Interviews**

This project is complete and demonstrates:
- ✅ Advanced LangGraph agentic workflows
- ✅ Self-correction and iterative improvement
- ✅ Tool integration and validation
- ✅ Observability best practices
- ✅ Beautiful UI for demonstrations
- ✅ Production-grade error handling

**Perfect for your next interview!** 🎯

---

*Built by [jalpatel11](https://github.com/jalpatel11) to demonstrate GenAI Platform Engineering skills*

*Last Updated: February 2026*