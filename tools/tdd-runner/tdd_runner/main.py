"""Entry point for TDD Runner — Claude Agent SDK orchestrator."""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AgentDefinition, HookMatcher

from tdd_runner.utils.tracker import SubagentTracker
from tdd_runner.utils.transcript import setup_session, TranscriptWriter
from tdd_runner.utils.message_handler import process_assistant_message

load_dotenv()

PROMPTS_DIR = Path(__file__).parent / "prompts"
TEMPLATES_DIR = Path(__file__).parent / "templates"
PROMPTS_DIR.mkdir(exist_ok=True)


def load_prompt(filename: str) -> str:
    """Load a prompt from the prompts directory."""
    prompt_path = PROMPTS_DIR / filename
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_template(filename: str) -> str:
    """Load a template and return it as a prompt appendix."""
    template_path = TEMPLATES_DIR / filename
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    return f"\n\n## Output Template\n\nUse this exact structure for your output:\n\n{content}"


def build_agents() -> dict[str, AgentDefinition]:
    """Build all subagent definitions."""

    planner_prompt = load_prompt("planner.md") + load_template("test-cases.md")
    analyzer_prompt = load_prompt("analyzer.md") + load_template("coverage-analysis.md")
    generator_prompt = load_prompt("generator.md")
    reporter_prompt = load_prompt("reporter.md")

    return {
        "planner": AgentDefinition(
            description=(
                "Use this agent to extract structured test cases from a SPEC.md file. "
                "The planner reads the spec completely, identifies every testable requirement "
                "(happy flows, edge cases, API contracts, schema validations, business rules), "
                "and writes a TEST-CASES.md file in the same directory as the spec. "
                "Each test case includes layer prefix (UNIT/SVC/API), priority (P0/P1/P2), "
                "preconditions, steps, and expected outcome."
            ),
            tools=["Read", "Glob", "Grep", "Write", "Bash"],
            prompt=planner_prompt,
            model="sonnet",
        ),
        "analyzer": AgentDefinition(
            description=(
                "Use this agent AFTER the planner has produced TEST-CASES.md. "
                "The analyzer reads both the SPEC.md and TEST-CASES.md, maps every spec "
                "requirement to test cases, and finds gaps: uncovered requirements, weakly "
                "covered ones, and orphaned tests. Writes COVERAGE-ANALYSIS.md with risk "
                "levels (Critical/High/Medium/Low) and recommendations."
            ),
            tools=["Read", "Glob", "Grep", "Write"],
            prompt=analyzer_prompt,
            model="haiku",
        ),
        "generator": AgentDefinition(
            description=(
                "Use this agent AFTER test cases exist in TEST-CASES.md. "
                "The generator reads the test cases, examines existing test files and "
                "conftest.py for style reference, then writes runnable pytest files. "
                "Creates tests/unit/test_{feature}.py, tests/unit/test_{feature}_service.py, "
                "and tests/integration/test_{feature}_api.py following the project's patterns."
            ),
            tools=["Read", "Glob", "Grep", "Write", "Bash"],
            prompt=generator_prompt,
            model="sonnet",
        ),
        "reporter": AgentDefinition(
            description=(
                "Use this agent to run pytest and produce a structured test report. "
                "The reporter runs python -m pytest --tb=short -v, parses the output, "
                "analyzes failures (distinguishing RED phase ImportErrors from real bugs), "
                "and prints a formatted report with pass/fail counts, failure analysis, "
                "and prioritized recommendations."
            ),
            tools=["Read", "Bash", "Glob"],
            prompt=reporter_prompt,
            model="haiku",
        ),
    }


async def run_interactive() -> None:
    """Run TDD Runner in interactive mode."""

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\nError: ANTHROPIC_API_KEY not found.")
        print("Set it in a .env file or export it in your shell.")
        print("Get your key at: https://console.anthropic.com/settings/keys\n")
        return

    transcript_file, session_dir = setup_session()
    transcript = TranscriptWriter(transcript_file)
    tracker = SubagentTracker(session_dir=session_dir)

    lead_prompt = load_prompt("lead.md")
    agents = build_agents()
    hooks = {
        "PreToolUse": [
            HookMatcher(matcher=None, hooks=[tracker.pre_tool_use_hook])
        ],
        "PostToolUse": [
            HookMatcher(matcher=None, hooks=[tracker.post_tool_use_hook])
        ],
    }

    options = ClaudeAgentOptions(
        permission_mode="bypassPermissions",
        system_prompt=lead_prompt,
        allowed_tools=["Task"],
        agents=agents,
        hooks=hooks,
        model="sonnet",
    )

    print("\n" + "=" * 50)
    print("  TDD Runner — Test-Driven Development Pipeline")
    print("=" * 50)
    print("\nCommands:")
    print("  plan <SPEC.md>      — Extract test cases from spec")
    print("  analyze <SPEC.md>   — Coverage gap analysis")
    print("  generate <TEST-CASES.md> — Write pytest code")
    print("  report              — Run tests & summarize")
    print("  full <SPEC.md>      — Complete pipeline")
    print("\nType 'exit' to quit.\n")

    try:
        async with ClaudeSDKClient(options=options) as client:
            while True:
                try:
                    user_input = input("tdd> ").strip()
                except (EOFError, KeyboardInterrupt):
                    break

                if not user_input or user_input.lower() in ("exit", "quit", "q"):
                    break

                transcript.write_to_file(f"\ntdd> {user_input}\n")

                await client.query(prompt=user_input)

                transcript.write("\n", end="")

                async for msg in client.receive_response():
                    if type(msg).__name__ == "AssistantMessage":
                        process_assistant_message(msg, tracker, transcript)

                transcript.write("\n")
    finally:
        transcript.write("\nSession ended.\n")
        transcript.close()
        tracker.close()
        print(f"\nSession logs: {session_dir}")


async def run_command(command: str) -> None:
    """Run a single TDD command non-interactively."""

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not found.", file=sys.stderr)
        sys.exit(1)

    transcript_file, session_dir = setup_session()
    transcript = TranscriptWriter(transcript_file)
    tracker = SubagentTracker(session_dir=session_dir)

    lead_prompt = load_prompt("lead.md")
    agents = build_agents()

    hooks = {
        "PreToolUse": [
            HookMatcher(matcher=None, hooks=[tracker.pre_tool_use_hook])
        ],
        "PostToolUse": [
            HookMatcher(matcher=None, hooks=[tracker.post_tool_use_hook])
        ],
    }

    options = ClaudeAgentOptions(
        permission_mode="bypassPermissions",
        system_prompt=lead_prompt,
        allowed_tools=["Task"],
        agents=agents,
        hooks=hooks,
        model="sonnet",
    )

    try:
        async with ClaudeSDKClient(options=options) as client:
            transcript.write_to_file(f"\ntdd> {command}\n")
            await client.query(prompt=command)

            async for msg in client.receive_response():
                if type(msg).__name__ == "AssistantMessage":
                    process_assistant_message(msg, tracker, transcript)

            transcript.write("\n")
    finally:
        transcript.close()
        tracker.close()
        print(f"\nSession logs: {session_dir}")


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]

    if not args:
        # Interactive mode
        asyncio.run(run_interactive())
    else:
        # Single command mode: tdd-runner plan docs/specs/auth.SPEC.md
        command = " ".join(args)
        asyncio.run(run_command(command))


if __name__ == "__main__":
    main()
