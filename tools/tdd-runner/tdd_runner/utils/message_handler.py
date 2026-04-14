"""Process assistant messages from the Claude SDK stream."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tracker import SubagentTracker
    from .transcript import TranscriptWriter


def process_assistant_message(msg, tracker: SubagentTracker, transcript: TranscriptWriter) -> None:
    """Process an AssistantMessage from the Claude SDK response stream.

    Extracts text content and writes it to the transcript.
    """
    if not hasattr(msg, "content"):
        return

    for block in msg.content:
        block_type = type(block).__name__

        if block_type == "TextBlock":
            transcript.write(block.text, end="")

        elif block_type == "ToolUseBlock":
            # Tool use is tracked via hooks, just note it in transcript
            transcript.write_to_file(f"\n[Tool: {block.name}]\n")
