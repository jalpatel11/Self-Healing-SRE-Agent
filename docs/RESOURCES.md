# Technologies & Resources

## Technologies & Why I Chose Them

| Technology | Version | Purpose | Why Not Alternatives? |
|------------|---------|---------|----------------------|
| **LangGraph** | 0.2.28 | Agent orchestration | LangChain's alternatives (CrewAI, AutoGPT) lack the control over state and routing I needed for self-correction |
| **LangChain** | Latest | LLM abstraction | Standard in the industry, excellent documentation, seamless LangSmith integration |
| **Claude 3.5 Sonnet** | Latest | Primary LLM | Outperforms GPT-4o in code reasoning tasks and debugging; tested both extensively |
| **GPT-4o** | Latest | Alternative LLM | Faster and slightly cheaper; good fallback option |
| **FastAPI** | 0.115.0 | Demo application | Uvicorn auto-reload made bug testing painless; modern async support |
| **Streamlit** | 1.39.0 | Web UI | Fastest way to build impressive UIs; perfect for demos and interviews |
| **PyGithub** | 2.4.0 | GitHub API | Official library, well-maintained, handles auth cleanly |
| **LangSmith** | N/A | Observability | No alternative comes close for LLM observability; essential for production |

## What I Tried and Rejected

**CrewAI**: Too opinionated about agent roles, harder to implement custom routing logic

**Vertex AI Agent Builder**: Locked into Google Cloud, wanted multi-cloud flexibility

**OpenAI Assistants API**: Too black-box, couldn't introspect decision-making for debugging

**Semantic Kernel**: Microsoft's framework, but LangChain ecosystem is richer

**LlamaIndex**: Better for RAG than agentic workflows

## Dependencies Rationale

```txt
# requirements.txt breakdown
langchain-core==0.3.28      # Core abstractions
langchain==0.3.14           # Main framework
langgraph==0.2.28           # StateGraph orchestration
langsmith==0.2.5            # Observability (auto-included)

langchain-openai==0.2.14    # GPT-4o support
langchain-anthropic==0.3.4  # Claude 3.5 Sonnet support

fastapi==0.115.0            # Web framework
uvicorn==0.32.1             # ASGI server
pydantic==2.10.3            # Data validation

streamlit==1.39.0           # UI framework
requests==2.32.3            # HTTP client (for triggering crashes)

PyGithub==2.4.0             # GitHub API
python-dotenv==1.0.1        # Environment management
```

**Total install size**: ~500MB (mostly PyTorch for embeddings, even though we don't use them)

**Startup time**: ~2-3 seconds (LangChain initialization)

## Learning Resources That Actually Helped

### LangGraph (Must-Read)

**Official Documentation**:
- [LangGraph Core Concepts](https://langchain-ai.github.io/langgraph/concepts/) - Read this first
- [State Management Guide](https://langchain-ai.github.io/langgraph/concepts/low_level/#state-management) - Critical for understanding `Annotated` types
- [Conditional Routing Tutorial](https://langchain-ai.github.io/langgraph/how-tos/branching/) - How I learned the self-correction pattern

**YouTube**:
- Harrison Chase's [LangGraph Deep Dive](https://www.youtube.com/watch?v=9BPCV5TYPmg) - LangChain CEO explaining design decisions
- Sam Witteveen's [LangGraph Tutorials](https://www.youtube.com/@samwitteveenai) - Practical examples

**GitHub Examples**:
- [LangGraph Examples Repo](https://github.com/langchain-ai/langgraph/tree/main/examples) - Production patterns

### LangSmith (Observability)

**Essential Reading**:
- [LangSmith Quickstart](https://docs.smith.langchain.com/getting_started) - 10 minutes to first trace
- [Tracing Guide](https://docs.smith.langchain.com/tracing) - Understanding spans and runs
- [Debugging Agent Workflows](https://docs.smith.langchain.com/evaluation/agent_workflows) - How to find issues

**Pro Tip**: Create a separate project for each experiment. Makes comparing approaches trivial.

### SRE & Incident Response

**Books That Influenced This**:
- [Site Reliability Engineering](https://sre.google/sre-book/table-of-contents/) - Google's SRE bible; chapters on automation and monitoring
- [The Phoenix Project](https://www.oreilly.com/library/view/the-phoenix-project/9781457191350/) - DevOps novel that shows why automation matters

**Real-World SRE Blogs**:
- [Uber Engineering Blog](https://www.uber.com/blog/engineering/) - Incident response at scale
- [Netflix Tech Blog](https://netflixtechblog.com/) - Chaos engineering and automated remediation

### Prompt Engineering for Code

**What I Learned**:
- Be explicit about error handling requirements
- Include example code in prompts (few-shot learning)
- Use structured output (JSON mode) for parsing fixes
- Lower temperature (0.1-0.3) for code generation vs. 0.7+ for creative tasks

**Resources**:
- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic Prompt Library](https://docs.anthropic.com/claude/prompt-library) - Claude-specific best practices

---

[← Back to Main README](../README.md) | [Interview Guide →](INTERVIEW.md) | [Troubleshooting →](TROUBLESHOOTING.md)
