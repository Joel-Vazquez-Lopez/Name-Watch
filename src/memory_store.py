import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class MemoryStore:
    """
    Stores compact meeting memory items.

    It does not store raw audio or full transcripts.
    """

    def __init__(self, path: str = "memory/meeting_memory.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def load(self) -> List[Dict]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def save_items(self, items: List[Dict]) -> None:
        if not items:
            return

        data = self.load()

        for item in items:
            data.append({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                **item
            })

        self.path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def search(self, query: str) -> List[Dict]:
        query_lower = query.lower()
        results = []

        for item in self.load():
            searchable = json.dumps(item, ensure_ascii=False).lower()

            if query_lower in searchable:
                results.append(item)

        return results

    def clear(self) -> None:
        self.path.write_text("[]", encoding="utf-8")
