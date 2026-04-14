"""Subagent activity tracker — logs tool calls and progress."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class SubagentTracker:
    """Tracks subagent tool calls and writes them to a JSONL log."""

    def __init__(self, session_dir: Path) -> None:
        self.session_dir = session_dir
        self.log_path = session_dir / "tool_calls.jsonl"
        self.log_file = open(self.log_path, "a", encoding="utf-8")
        self.active_agents: dict[str, str] = {}  # tool_use_id -> agent name

    def pre_tool_use_hook(self, tool_use_id: str, tool_name: str, tool_input: dict) -> dict:
        """Called before each tool use. Logs the call."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "pre_tool_use",
            "tool": tool_name,
            "input_summary": _summarize_input(tool_name, tool_input),
        }
        self.log_file.write(json.dumps(entry) + "\n")
        self.log_file.flush()

        # Print progress indicator
        if tool_name == "Agent":
            agent_name = tool_input.get("description", "unknown")
            print(f"  -> Delegating to: {agent_name}")
        elif tool_name == "Write":
            path = tool_input.get("file_path", "unknown")
            print(f"  -> Writing: {path}")
        elif tool_name == "Read":
            path = tool_input.get("file_path", "unknown")
            print(f"  -> Reading: {path}")
        elif tool_name == "Bash":
            cmd = tool_input.get("command", "")[:80]
            print(f"  -> Running: {cmd}")

        return {"decision": "approve"}

    def post_tool_use_hook(self, tool_use_id: str, tool_name: str, tool_output: str) -> dict:
        """Called after each tool use. Logs the result."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "post_tool_use",
            "tool": tool_name,
            "output_length": len(tool_output) if tool_output else 0,
        }
        self.log_file.write(json.dumps(entry) + "\n")
        self.log_file.flush()
        return {}

    def close(self) -> None:
        """Close the log file."""
        if self.log_file and not self.log_file.closed:
            self.log_file.close()


def _summarize_input(tool_name: str, tool_input: dict) -> str:
    """Create a short summary of tool input for logging."""
    if tool_name == "Read":
        return tool_input.get("file_path", "")
    if tool_name == "Write":
        return tool_input.get("file_path", "")
    if tool_name == "Bash":
        return tool_input.get("command", "")[:100]
    if tool_name == "Grep":
        return f"pattern={tool_input.get('pattern', '')}"
    if tool_name == "Glob":
        return f"pattern={tool_input.get('pattern', '')}"
    if tool_name == "Agent":
        return tool_input.get("description", "")
    return str(tool_input)[:100]
