"""Session transcript writer — logs conversation to file."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path


def setup_session() -> tuple[Path, Path]:
    """Create a session directory with timestamp and return (transcript_path, session_dir)."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    session_dir = Path("sessions") / f"tdd_{timestamp}"
    session_dir.mkdir(parents=True, exist_ok=True)

    transcript_file = session_dir / "transcript.md"
    return transcript_file, session_dir


class TranscriptWriter:
    """Writes conversation transcript to file and optionally to console."""

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.file = open(filepath, "a", encoding="utf-8")
        self._write_header()

    def _write_header(self) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        self.file.write(f"# TDD Runner Session — {timestamp}\n\n")
        self.file.flush()

    def write(self, text: str, *, end: str = "\n") -> None:
        """Write to both console and file."""
        print(text, end=end, flush=True)
        self.file.write(text + end)
        self.file.flush()

    def write_to_file(self, text: str) -> None:
        """Write to file only (no console output)."""
        self.file.write(text)
        self.file.flush()

    def close(self) -> None:
        """Close the transcript file."""
        if self.file and not self.file.closed:
            self.file.close()
