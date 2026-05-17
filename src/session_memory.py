from typing import Dict, List


class SessionMemory:
    """
    Short-term meeting memory based on compact AI summaries.

    This does not store the full transcript.
    It stores only compressed summaries, questions, action items, decisions, and risks.
    """

    def __init__(self, max_recent_items: int = 12):
        self.meeting_so_far_summary = ""
        self.recent_items: List[Dict] = []
        self.max_recent_items = max_recent_items

    def add_analysis(self, analysis: Dict) -> None:
        """
        Updates short-term memory from one AI analysis result.
        """
        if not isinstance(analysis, dict):
            return

        updated_summary = analysis.get("updated_meeting_summary")

        if isinstance(updated_summary, str) and updated_summary.strip():
            self.meeting_so_far_summary = updated_summary.strip()

        memory_items = analysis.get("memory_items", [])

        if isinstance(memory_items, list):
            for item in memory_items:
                if isinstance(item, dict):
                    self.recent_items.append(item)

        self.recent_items = self.recent_items[-self.max_recent_items:]

    def get_context_for_ai(self) -> str:
        """
        Returns compact context for the AI model.

        This gives continuity without sending the whole meeting transcript.
        """
        parts = []

        if self.meeting_so_far_summary:
            parts.append("Meeting so far summary:")
            parts.append(self.meeting_so_far_summary)

        if self.recent_items:
            parts.append("\nRecent compact memory items:")

            for idx, item in enumerate(self.recent_items, start=1):
                item_type = item.get("type", "memory")
                importance = item.get("importance", "unknown")
                summary = item.get("summary", "")

                if summary:
                    parts.append(f"{idx}. [{item_type}; {importance}] {summary}")

        return "\n".join(parts).strip()

    def clear(self) -> None:
        self.meeting_so_far_summary = ""
        self.recent_items = []
