"""
Tools for the Self-Healing SRE Agent.

This module defines the tools that agents can use:
- fetch_logs: Retrieve CI or application logs for analysis
- run_tests: Validate generated fix code via AST analysis
- open_github_pr: Create a GitHub Pull Request with a fix
"""

import ast
import os
from datetime import datetime
from typing import Optional

import httpx
from github import Github, GithubException
from langchain_core.tools import tool


@tool
def fetch_logs(time_range: str = "1h", severity: str = "error") -> str:
    """
    Fetch application logs for investigation.

    Behaviour (in priority order):
    1. If GITHUB_RUN_ID + GITHUB_TOKEN are set -> fetch the failing CI job's
       logs via the GitHub Actions API (works in any repo's CI pipeline).
    2. Otherwise -> read from the local log file configured by LOG_FILE
       (demo / local development mode).

    Args:
        time_range: Ignored for GitHub API logs; used for local file filtering.
        severity:   Ignored for GitHub API logs; used for local file filtering.

    Returns:
        Log text as a string, or an error message if logs are unavailable.
    """
    from sre_agent.config import settings

    run_id = os.getenv("GITHUB_RUN_ID", "").strip()
    github_token = os.getenv("GITHUB_TOKEN", settings.github_token or "").strip()
    repo = os.getenv("GITHUB_REPOSITORY", settings.github_repo or "").strip()

    # ── 1. GitHub Actions API path ──────────────────────────────────────────
    if run_id and github_token and repo:
        return _fetch_github_actions_logs(run_id, repo, github_token)

    # ── 2. Local log file (demo / dev mode) ────────────────────────────────
    return _fetch_local_logs(settings.log_file, time_range, severity)


def _fetch_github_actions_logs(run_id: str, repo: str, token: str) -> str:
    """Download logs for failed jobs in a GitHub Actions run via the API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    base = "https://api.github.com"

    try:
        with httpx.Client(headers=headers, follow_redirects=True, timeout=30) as client:
            # Get all jobs for this run
            jobs_resp = client.get(f"{base}/repos/{repo}/actions/runs/{run_id}/jobs")
            jobs_resp.raise_for_status()
            jobs = jobs_resp.json().get("jobs", [])

            # Find failed jobs
            failed_jobs = [j for j in jobs if j.get("conclusion") == "failure"]
            if not failed_jobs:
                return (
                    f"=== GitHub Actions Run {run_id} ===\n"
                    "No failed jobs found. All jobs may have passed or been skipped.\n"
                )

            log_sections: list[str] = []
            for job in failed_jobs[:3]:  # cap at 3 failed jobs to stay within context
                job_id = job["id"]
                job_name = job.get("name", "unknown")

                logs_resp = client.get(
                    f"{base}/repos/{repo}/actions/jobs/{job_id}/logs"
                )
                if logs_resp.status_code == 200:
                    log_sections.append(
                        f"=== Failed Job: {job_name} (ID: {job_id}) ===\n"
                        f"{logs_resp.text}\n"
                    )
                else:
                    log_sections.append(
                        f"=== Failed Job: {job_name} (ID: {job_id}) ===\n"
                        f"Could not retrieve logs (HTTP {logs_resp.status_code}).\n"
                    )

            combined = "\n".join(log_sections)
            return (
                f"=== GitHub Actions CI Logs (Run {run_id}, Repo: {repo}) ===\n\n"
                f"{combined}\n"
                f"=== End of CI Logs ===\n"
                f"Total failed jobs: {len(failed_jobs)}\n"
            )

    except httpx.HTTPError as exc:
        return f"[ERROR] Failed to fetch GitHub Actions logs: {exc}"
    except Exception as exc:
        return f"[ERROR] Unexpected error fetching CI logs: {exc}"


def _fetch_local_logs(log_file: str, time_range: str, severity: str) -> str:
    """Read logs from a local file (demo / development mode)."""
    if not os.path.exists(log_file):
        return (
            "No logs found. The application may not have been started yet, "
            "or no errors have occurred. Please ensure the FastAPI app is running "
            "and has received requests."
        )

    try:
        with open(log_file) as f:
            log_lines = f.readlines()

        if not log_lines:
            return "Log file is empty. No errors have been recorded yet."

        if severity.lower() != "all":
            filtered = [
                line for line in log_lines
                if severity.upper() in line or "CRITICAL" in line
            ]
        else:
            filtered = log_lines

        limits = {"5m": 10, "15m": 30, "30m": 50, "1h": 100, "6h": 300, "1d": 500}
        max_lines = limits.get(time_range, 100)
        recent = filtered[-max_lines:] if len(filtered) > max_lines else filtered

        if not recent:
            return f"No logs found with severity '{severity}' in the last {time_range}."

        return (
            f"\n=== Application Logs (Last {time_range}, Severity: {severity}) ===\n\n"
            f"{''.join(recent)}\n\n"
            f"=== End of Logs ===\n\n"
            f"Total lines returned: {len(recent)}\n"
        )

    except Exception as exc:
        return f"Error reading logs: {exc}"


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
    file_path: str = "main.py",
    branch_name: Optional[str] = None,
) -> str:
    """
    Create a GitHub Pull Request with the proposed fix.

    Args:
        title:       PR title summarising the fix.
        body:        PR description with root cause and fix explanation.
        fix_code:    Complete fixed file content (not a diff).
        file_path:   Repo-relative path of the file being fixed.
                     The Mechanic agent MUST identify this from the CI logs
                     (e.g. "src/auth.py", "utils/db.py"). Defaults to
                     "main.py" as a safe fallback only.
        branch_name: Branch for the PR (auto-generated from timestamp if None).

    Returns:
        PR URL string if successful, or error/simulation message.
    """
    from sre_agent.config import settings

    github_token = settings.github_token
    github_repo = settings.github_repo

    if not github_token or not github_repo:
        return _simulate_pr_creation(title, body, fix_code, file_path, branch_name)

    # Actual GitHub PR creation
    try:
        g = Github(github_token)
        repo = g.get_repo(github_repo)

        if not branch_name:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            branch_name = f"fix/sre-agent-{timestamp}"

        default_branch = repo.default_branch
        source = repo.get_branch(default_branch)

        repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=source.commit.sha,
        )

        file_content = repo.get_contents(file_path, ref=default_branch)
        repo.update_file(
            path=file_path,
            message=f"Fix: {title}",
            content=fix_code,
            sha=file_content.sha,
            branch=branch_name,
        )

        pr = repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base=default_branch,
        )

        return (
            f"[SUCCESS] Pull Request created successfully!\n\n"
            f"PR URL: {pr.html_url}\nPR Number: #{pr.number}"
        )

    except GithubException as e:
        return f"[ERROR] GitHub API Error: {e!s}"
    except Exception as e:
        return f"[ERROR] Error creating PR: {e!s}"


def _simulate_pr_creation(
    title: str,
    body: str,
    fix_code: str,
    file_path: str,
    branch_name: Optional[str],
) -> str:
    """Simulate PR creation when GitHub credentials are not configured."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if not branch_name:
        branch_name = f"fix/sre-agent-{timestamp}"

    fix_file = f"generated_fix_{timestamp}.py"
    try:
        with open(fix_file, "w") as f:
            f.write(fix_code)
    except Exception:
        pass

    return (
        f"\n[SIMULATED PR CREATION - Demo Mode]\n\n"
        f"[INFO] Pull Request would be created with:\n\n"
        f"Title: {title}\n"
        f"Branch: {branch_name}\n"
        f"File: {file_path}\n\n"
        f"Body:\n{body}\n\n"
        f"Fix code has been saved to: {fix_file}\n\n"
        f"To enable real PR creation:\n"
        f"1. Set GITHUB_TOKEN in .env\n"
        f"2. Set GITHUB_REPO in .env (format: username/repo-name)\n\n"
        f"Simulated PR URL: https://github.com/your-repo/pull/123\n"
    )
