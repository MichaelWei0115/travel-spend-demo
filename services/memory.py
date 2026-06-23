"""Working Memory Service - Manages ephemeral [WORKING_NOTES] for AI reasoning."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class WorkingMemory:
    """Ephemeral working memory that is cleared after each task."""
    notes: list[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    task_id: Optional[str] = None
    is_active: bool = False

    def start_task(self, task_id: str) -> None:
        self.task_id = task_id
        self.created_at = datetime.now()
        self.is_active = True
        self.notes = []
        self.add_note(f"Task started: {task_id}")

    def add_note(self, note: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.notes.append(f"[{timestamp}] {note}")

    def get_notes(self) -> list[str]:
        return self.notes.copy()

    def get_formatted(self) -> str:
        if not self.notes:
            return "[WORKING_NOTES]\n(empty - no active task)"
        header = f"[WORKING_NOTES] Task: {self.task_id}"
        body = "\n".join(f"  {n}" for n in self.notes)
        return f"{header}\n{body}"

    def clear(self) -> dict:
        """Clear working memory after task completion. Returns summary."""
        summary = {
            "task_id": self.task_id,
            "notes_count": len(self.notes),
            "duration_sec": (datetime.now() - self.created_at).total_seconds() if self.created_at else 0,
        }
        self.notes = []
        self.task_id = None
        self.created_at = None
        self.is_active = False
        return summary


# Singleton instance
working_memory = WorkingMemory()
