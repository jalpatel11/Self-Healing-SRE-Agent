# Troubleshooting Guide

## Common Issues and Solutions

### 1. "No LLM API key configured"

```bash
# Check your .env file
cat .env | grep -E "OPENAI|ANTHROPIC"

# Make sure you have at least one set
export ANTHROPIC_API_KEY=sk-ant-xxxxx
```

**Solution**: Ensure you have either `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` set in your `.env` file.

---

### 2. "ModuleNotFoundError: No module named 'langchain'"

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Solution**: Always activate the virtual environment before running the scripts.

---

### 3. "LangSmith traces not appearing"

```bash
# Verify environment variables
echo $LANGCHAIN_TRACING_V2  # Should be "true"
echo $LANGCHAIN_API_KEY     # Should be "lsv2_pt_xxxxx"

# Check the LangSmith project exists
# Go to https://smith.langchain.com and verify project name
```

**Solution**: 
1. Ensure `LANGCHAIN_TRACING_V2=true` in `.env`
2. Verify API key is correct
3. Check project name matches in LangSmith dashboard

---

### 4. "GitHub PR creation failed"

```bash
# This is expected without credentials
# The system falls back to demo mode
# To enable real PRs:
export GITHUB_TOKEN=ghp_xxxxx
export GITHUB_REPO=your-username/your-repo
```

**Solution**: This is normal behavior. The agent will simulate PR creation in demo mode. For real PRs, add GitHub credentials to `.env`.

---

### 5. "Agent keeps failing validation"

```bash
# Check LangSmith trace to see what the Mechanic is generating
# Common issues:
# - Temperature too high (set to 0.1-0.3)
# - Prompt unclear about safe dictionary access
# - LLM hallucinating irrelevant fixes

# Try switching LLMs:
export LLM_PROVIDER=openai  # or "anthropic"
```

**Solution**:
1. Review the LangSmith trace to see the generated code
2. Check if the Mechanic is using `.get()` or proper error handling
3. Try the alternative LLM (Claude vs GPT-4o)
4. Lower the temperature in [agents.py](../agents.py)

---

### 6. "Port 8000 already in use"

```bash
# Kill the existing FastAPI process
lsof -ti:8000 | xargs kill -9

# Or change the port
# Edit app.py: uvicorn.run(app, host="0.0.0.0", port=8001)
```

**Solution**: Either kill the existing process or change the port in `app.py`.

---

### 7. "Streamlit won't start"

```bash
# Check if port 8501 is in use
lsof -ti:8501 | xargs kill -9

# Try running directly
streamlit run ui.py
```

**Solution**: Ensure port 8501 is available, or Streamlit will auto-increment.

---

### 8. "API rate limit exceeded"

**Symptoms**: 
- 429 errors in console
- Agent stops mid-execution
- LangSmith shows rate limit errors

**Solution**:
1. Wait a few minutes (rate limits are usually per-minute)
2. For OpenAI: Check your tier limits at platform.openai.com
3. For Anthropic: Check your usage at console.anthropic.com
4. Consider implementing retry logic with exponential backoff

---

### 9. "Agent generates incorrect fix"

**Symptoms**:
- Validation always fails
- Self-correction loop exhausts all 3 attempts
- Generated code doesn't address the root cause

**Solution**:
1. **Check the logs**: Open `app_logs.txt` - is the error clear?
2. **Review LangSmith trace**: What did the Investigator identify as root cause?
3. **Improve prompts**: Edit [agents.py](../agents.py) to be more specific
4. **Switch models**: Claude 3.5 Sonnet generally performs better for debugging

---

### 10. "Slow execution (>2 minutes)"

**Expected time**: 25-45 seconds per full workflow

**Possible causes**:
1. **Slow LLM response** (especially GPT-4o during peak hours)
2. **Network latency** to API endpoints
3. **Multiple self-correction iterations**

**Solution**:
1. Check LangSmith to see which agent is slow
2. Try Claude instead of GPT-4o (generally faster)
3. Ensure good internet connection
4. Consider caching common analyses in production

---

## Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Add to .env
DEBUG=true

# Or set environment variable
export DEBUG=true
python main.py
```

This will show:
- Full LLM prompts and responses
- State transitions between agents
- Timing information for each step

---

## Getting Help

If you encounter issues not covered here:

1. **Check LangSmith traces** - 90% of issues are visible here
2. **Review GitHub Issues** - Someone may have had the same problem
3. **Open a new issue** with:
   - Error message
   - LangSmith trace link
   - Your `.env` file (with keys redacted!)
   - Steps to reproduce

---

[← Back to Main README](../README.md) | [Setup Guide →](SETUP.md) | [Contributing →](../CONTRIBUTING.md)
