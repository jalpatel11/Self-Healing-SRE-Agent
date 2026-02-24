# Contributing to Self-Healing SRE Agent

This is primarily a portfolio/learning project, but contributions are welcome!

## Areas for Enhancement

### High Priority
- [ ] Add more bug types (NullPointerException, TypeErrors, IndexErrors)
- [ ] Support JavaScript/TypeScript applications
- [ ] Implement actual test execution in Docker containers
- [ ] Add human approval workflow before PR creation
- [ ] Create a knowledge base of past fixes (RAG integration)

### Medium Priority
- [ ] Add performance benchmarking suite
- [ ] Implement cost tracking and alerting
- [ ] Support webhook triggers from monitoring tools
- [ ] Add rollback mechanisms
- [ ] Create a plugin system for custom validators

### Low Priority
- [ ] Multi-language log parsing
- [ ] Integration with Jira/Linear for ticket creation
- [ ] Slack notifications at each workflow step
- [ ] A/B testing different LLM models

## How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make your changes**
4. **Test thoroughly** (run the workflow with your changes)
5. **Commit**: `git commit -m "Add: your feature description"`
6. **Push**: `git push origin feature/your-feature`
7. **Open a Pull Request** with:
   - Clear description of the change
   - Why it's needed
   - Testing you've done
   - LangSmith trace showing it works

## Coding Standards

- **Type hints**: Use throughout (this is Python 3.10+)
- **Docstrings**: All functions, especially agents and tools
- **Error handling**: Graceful failures, no silent errors
- **Comments**: Brief but complete, no emojis
- **Testing**: Include example traces or test cases

## Testing Your Changes

Before submitting a PR:

1. **Lint your code**:
   ```bash
   # Install linting tools
   pip install black isort mypy
   
   # Format code
   black .
   isort .
   
   # Type check
   mypy agents.py tools.py graph.py
   ```

2. **Run the workflow**:
   ```bash
   # Terminal 1
   ./run.sh app
   
   # Terminal 2
   ./run.sh main
   ```

3. **Verify in LangSmith**:
   - Check that traces appear
   - Ensure no errors
   - Verify expected behavior

4. **Test edge cases**:
   - What happens when validation fails?
   - What if the LLM returns unexpected output?
   - Does it handle API errors gracefully?

## Pull Request Template

```markdown
## Description
Brief description of what this PR does.

## Motivation
Why is this change needed?

## Changes
- Change 1
- Change 2
- Change 3

## Testing
How did you test this?
- [ ] Manual testing in CLI
- [ ] Manual testing in Streamlit UI
- [ ] LangSmith trace link: [your trace]
- [ ] Edge cases tested

## Checklist
- [ ] Code follows project style guidelines
- [ ] Added/updated docstrings
- [ ] Tested locally
- [ ] No breaking changes (or documented if necessary)
```

## Code Review Process

1. **I'll review** within 1-2 days
2. **Feedback** may request changes
3. **Merge** once approved and tests pass

## Questions?

Open an issue or reach out on [GitHub](https://github.com/jalpatel11).

---

Thank you for contributing! 🙏

[← Back to Main README](README.md) | [Troubleshooting →](docs/TROUBLESHOOTING.md)
