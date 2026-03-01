"""CLI entry point for the Self-Healing SRE Agent.

Usage:
    sre-agent heal [--run-id RUN_ID] [--repo OWNER/REPO]

All options fall back to environment variables when not supplied:
    --run-id  ->  GITHUB_RUN_ID
    --repo    ->  GITHUB_REPOSITORY
"""

from __future__ import annotations

import argparse
import os
import sys


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sre-agent",
        description=(
            "Self-Healing SRE Agent — automatically investigates CI failures, "
            "generates fixes, and opens GitHub pull requests."
        ),
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    heal = sub.add_parser(
        "heal",
        help="Run the self-healing workflow against a failed CI run.",
    )
    heal.add_argument(
        "--run-id",
        default=os.getenv("GITHUB_RUN_ID", ""),
        help="GitHub Actions run ID of the failed workflow (default: $GITHUB_RUN_ID)",
    )
    heal.add_argument(
        "--repo",
        default=os.getenv("GITHUB_REPOSITORY", ""),
        help="Target repository in OWNER/REPO format (default: $GITHUB_REPOSITORY)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "heal":
        # Validate required env vars before importing heavy deps
        if not os.getenv("GROQ_API_KEY") and not os.getenv("GEMINI_API_KEY"):
            print(
                "[ERROR] GROQ_API_KEY (or GEMINI_API_KEY) must be set.\n"
                "  Export the key or add it to your .env file.\n"
                "  Get a free Groq key at https://console.groq.com",
                file=sys.stderr,
            )
            return 1

        # Inject CLI args back into env so auto_heal_ci picks them up
        if args.run_id:
            os.environ.setdefault("GITHUB_RUN_ID", args.run_id)
        if args.repo:
            os.environ.setdefault("GITHUB_REPOSITORY", args.repo)

        from sre_agent.auto_heal_ci import run_ci_auto_heal  # noqa: PLC0415

        return run_ci_auto_heal()

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
