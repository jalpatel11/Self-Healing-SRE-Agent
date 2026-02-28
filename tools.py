"""
Tools for the Self-Healing SRE Agent.

This module defines the tools that agents can use:
- fetch_logs: Retrieve application logs for analysis
- open_github_pr: Create a GitHub Pull Request with a fix
- run_tests: Simulate running pytest on the generated fix
"""

import ast
import os
from datetime import datetime
from typing import Optional

from github import Github, GithubException
from langchain_core.tools import tool


@tool
def fetch_logs(time_range: str = "1h", severity: str = "error") -> str:
    """
    Fetch application logs from the monitoring system.

    In this demo, reads from app_logs.txt file. In production, this would
    query systems like Prometheus, Loki, CloudWatch, or Datadog.

    Args:
        time_range: Time range for logs (e.g., "1h", "30m", "1d")
        severity: Log severity filter ("error", "warning", "info", "all")

    Returns:
        Formatted log entries as a string, or error message if logs unavailable
    """
    from config import settings
    log_file = settings.log_file

    if not os.path.exists(log_file):
        return (
            "No logs found. The application may not have been started yet, "
            "or no errors have occurred. Please ensure the FastAPI app is running "
            "and has received requests."
        )

    try:
        with open(log_file, "r") as f:
            log_lines = f.readlines()

        if not log_lines:
            return "Log file is empty. No errors have been recorded yet."

        # Filter by severity if not "all"
        if severity.lower() != "all":
            filtered_lines = [
                line for line in log_lines
                if severity.upper() in line or "CRITICAL" in line
            ]
        else:
            filtered_lines = log_lines

        # Parse time_range (simple implementation)
        # In production, you'd parse timestamps and filter by actual time
        # For now, just return last N lines based on time_range
        line_limits = {
            "5m": 10,
            "15m": 30,
            "30m": 50,
            "1h": 100,
            "6h": 300,
            "1d": 500,
        }

        max_lines = line_limits.get(time_range, 100)
        recent_lines = filtered_lines[-max_lines:] if len(filtered_lines) > max_lines else filtered_lines

        if not recent_lines:
            return f"No logs found with severity '{severity}' in the last {time_range}."

        log_output = "".join(recent_lines)

        return f"""
=== Application Logs (Last {time_range}, Severity: {severity}) ===

{log_output}

=== End of Logs ===

Total lines returned: {len(recent_lines)}
"""

    except Exception as e:
        return f"Error reading logs: {str(e)}"


@tool
def run_tests(fix_code: str, original_code: str = "") -> dict:
    """
    Validate generated fix code using AST analysis.

    Generic validator that works with any Python codebase — not hardcoded
    to the demo app. Checks:
    1. Syntax validity (ast.parse)
    2. All original function signatures are preserved
    3. No bare 'except:' clauses (common sign of a sloppy fix)

    Args:
        fix_code: The generated/fixed Python code to validate
        original_code: The original buggy code (for function-signature comparison)

    Returns:
        dict with keys:
            - passed (bool): Whether all checks passed
            - message (str): Human-readable summary
            - errors (list[str]): Specific issues found
    """
    errors = []

    # ── 1. Syntax check ────────────────────────────────────────────────────
    try:
        tree = ast.parse(fix_code)
    except SyntaxError as e:
        return {
            "passed": False,
            "message": "Fix code has syntax errors",
            "errors": [f"Syntax error at line {e.lineno}: {e.msg}"],
        }

    # ── 2. Preserve original function signatures ───────────────────────────
    if original_code:
        try:
            orig_tree = ast.parse(original_code)
            original_funcs = {
                node.name
                for node in ast.walk(orig_tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            fixed_funcs = {
                node.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            missing = original_funcs - fixed_funcs
            if missing:
                errors.append(
                    f"Functions removed from original code: {missing}. "
                    "All original functions must be preserved."
                )
                return {
                    "passed": False,
                    "message": f"Tests failed: {len(errors)} issue(s) found",
                    "errors": errors,
                }
        except SyntaxError:
            pass  # original was broken — skip comparison

    # ── 3. No bare except clauses ──────────────────────────────────────────
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            errors.append(
                "Bare 'except:' found — use specific exception types "
                "(e.g. 'except KeyError:') to avoid masking unrelated errors."
            )

    if errors:
        return {
            "passed": False,
            "message": f"Tests failed: {len(errors)} issue(s) found",
            "errors": errors,
        }

    return {
        "passed": True,
        "message": "All tests passed! The fix is valid.",
        "errors": [],
    }


@tool
def open_github_pr(
    title: str,
    body: str,
    fix_code: str,
    file_path: str = "app.py",
    branch_name: Optional[str] = None
) -> str:
    """
    Create a GitHub Pull Request with the proposed fix.

    This simulates PR creation. In a real implementation with proper credentials:
    1. Creates a new branch from main
    2. Commits the fix
    3. Opens a PR
    4. Returns the PR URL

    For this demo (without actual GitHub credentials), it returns a
    simulated PR response.

    Args:
        title: PR title (e.g., "Fix: Handle missing api_key in user_config")
        body: PR description with root cause analysis
        fix_code: The complete fixed code
        file_path: Path to the file being fixed (default: "app.py")
        branch_name: Branch name for the PR (auto-generated if None)

    Returns:
        PR URL if successful, or error message
    """
    from config import settings
    github_token = settings.github_token
    github_repo = settings.github_repo

    if not github_token or not github_repo:
        return _simulate_pr_creation(title, body, fix_code, file_path, branch_name)

    # Actual GitHub PR creation
    try:
        g = Github(github_token)
        repo = g.get_repo(github_repo)

        # Generate branch name if not provided
        if not branch_name:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            branch_name = f"fix/sre-agent-{timestamp}"

        # Get the default branch
        default_branch = repo.default_branch
        source = repo.get_branch(default_branch)

        # Create new branch
        repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=source.commit.sha
        )

        # Get the file and update it
        file_content = repo.get_contents(file_path, ref=default_branch)

        repo.update_file(
            path=file_path,
            message=f"Fix: {title}",
            content=fix_code,
            sha=file_content.sha,
            branch=branch_name
        )

        # Create pull request
        pr = repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base=default_branch
        )

        return f"[SUCCESS] Pull Request created successfully!\n\nPR URL: {pr.html_url}\nPR Number: #{pr.number}"

    except GithubException as e:
        return f"[ERROR] GitHub API Error: {str(e)}"
    except Exception as e:
        return f"[ERROR] Error creating PR: {str(e)}"


def _simulate_pr_creation(
    title: str,
    body: str,
    fix_code: str,
    file_path: str,
    branch_name: Optional[str]
) -> str:
    """
    Simulate PR creation when GitHub credentials are not configured.

    This is for demo purposes. In production, you would always have
    proper credentials configured.
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if not branch_name:
        branch_name = f"fix/sre-agent-{timestamp}"

    # Save the fix to a local file for inspection
    fix_file = f"generated_fix_{timestamp}.py"
    try:
        with open(fix_file, "w") as f:
            f.write(fix_code)
    except Exception:
        pass

    simulated_pr_url = "https://github.com/your-repo/pull/123"

    return f"""
[SIMULATED PR CREATION - Demo Mode]

[INFO] Pull Request would be created with:

Title: {title}
Branch: {branch_name}
File: {file_path}

Body:
{body}

Fix code has been saved to: {fix_file}

To enable real PR creation:
1. Set GITHUB_TOKEN in .env
2. Set GITHUB_REPO in .env (format: username/repo-name)

Simulated PR URL: {simulated_pr_url}
"""
