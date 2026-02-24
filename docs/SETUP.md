# Setup & Installation Guide

## Prerequisites

Before you begin, you'll need:

**Required:**
- **Python 3.10+** (3.11 recommended)
- **At least one LLM API key**:
  - **Anthropic API Key** (recommended) - Claude 3.5 Sonnet has superior reasoning for debugging
  - OR **OpenAI API Key** - GPT-4o works well too

**Highly Recommended:**
- **LangSmith API Key** - Free tier available, essential for:
  - Seeing how your agent thinks (critical for interviews!)
  - Debugging when things go wrong
  - Understanding token usage and costs

**Optional:**
- **GitHub Personal Access Token** - For real PR creation
  - Without this, system works in demo mode (simulated PRs)

## Installation

### Method 1: Automated Setup (Fastest)

```bash
# Clone the repository
git clone https://github.com/jalpatel11/Self-Healing-SRE-Agent.git
cd Self-Healing-SRE-Agent

# Run the setup script (creates venv, installs deps, copies .env)
chmod +x setup.sh
./setup.sh

# Edit .env with your API keys
nano .env  # Or use vim, code, etc.
```

### Method 2: Manual Setup (More Control)

```bash
# Clone the repository
git clone https://github.com/jalpatel11/Self-Healing-SRE-Agent.git
cd Self-Healing-SRE-Agent

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment file
cp .env.example .env
nano .env  # Add your API keys
```

## Configuration

Edit your `.env` file:

```bash
# LLM Provider (Choose one or both)
ANTHROPIC_API_KEY=sk-ant-xxxxx  # Recommended for debugging tasks
OPENAI_API_KEY=sk-xxxxx         # Alternative

# LangSmith (Highly recommended - get free key at smith.langchain.com)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=lsv2_pt_xxxxx
LANGCHAIN_PROJECT=SRE-Self-Healing-Agent

# GitHub (Optional - enables real PR creation)
GITHUB_TOKEN=ghp_xxxxx
GITHUB_REPO=your-username/your-repo

# Model Selection (defaults to claude-3-5-sonnet-20241022)
LLM_PROVIDER=anthropic  # or "openai"
```

## Running the System

I've provided three ways to run the system depending on your use case:

### Option 1: Streamlit Web UI (Best for Demos & Interviews)

Perfect for showing off the system visually.

**Terminal 1** - Start the FastAPI application:
```bash
./run.sh app
# Or manually: python app.py
```

**Terminal 2** - Start the Streamlit interface:
```bash
./run.sh ui
# Or manually: streamlit run ui.py
```

Then:
1. Open your browser to `http://localhost:8501`
2. Check the "Configuration Status" to verify your API keys
3. Click **"Trigger System Crash"** to create a bug
4. Click **"Run Self-Healing Agent"** to watch the magic
5. See real-time progress as each agent executes
6. View the self-correction loop when validation fails
7. Click the LangSmith trace link to see full reasoning

### Option 2: Command Line Interface (Best for Testing)

Terminal-based execution with detailed logging.

**Terminal 1** - Start FastAPI:
```bash
./run.sh app
```

**Terminal 2** - Run the agent:
```bash
./run.sh main
# Or manually: python main.py
```

Follow the interactive prompts:
1. System checks your environment
2. Choose to trigger the crash
3. Choose to run the self-healing workflow
4. Watch the progress in real-time
5. Get a LangSmith trace URL at the end

### Option 3: Quick Bug Test (Just to See It Crash)

Want to see the bug in action without running the agent?

```bash
# Terminal 1
./run.sh app

# Terminal 2
./run.sh test
# Or: python test_app.py
```

This triggers the KeyError and writes to `app_logs.txt`.

## Verifying It Works

After running, you should see:

1. **Console Output** showing:
   - `[INVESTIGATOR]` analyzing logs
   - `[MECHANIC]` generating fix
   - `[VALIDATOR]` testing fix
   - Possibly `[SELF-CORRECTION LOOP]` if first attempt fails
   - `[SUCCESS]` with PR creation

2. **Generated Files**:
   - `app_logs.txt` - The crash logs
   - (If using real GitHub) A new Pull Request in your repo

3. **LangSmith Dashboard** (if configured):
   - Click the trace URL
   - See every LLM call with prompts and responses
   - View tool invocations and results
   - Track the self-correction loop in action

## Troubleshooting

See the [Troubleshooting Guide](TROUBLESHOOTING.md) for common issues and solutions.

---

[← Back to Main README](../README.md) | [Architecture →](ARCHITECTURE.md) | [Technical Details →](TECHNICAL.md)
