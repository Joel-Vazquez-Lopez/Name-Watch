from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Deque


@dataclass
class TranscriptChunk:
    timestamp: datetime
    text: str


class RollingTranscriptBuffer:
    """
    Keeps a temporary rolling transcript window in RAM.

    This is the raw short-term context used for live analysis.
    Old transcript chunks are automatically discarded.
    """

    def __init__(self, max_seconds: int = 120):
        self.max_seconds = max_seconds
        self.chunks: Deque[TranscriptChunk] = deque()

    def add(self, text: str) -> None:
        text = text.strip()

        if not text:
            return

        self.chunks.append(
            TranscriptChunk(
                timestamp=datetime.now(),
                text=text
            )
        )

        self._discard_old_chunks()

    def _discard_old_chunks(self) -> None:
        cutoff = datetime.now() - timedelta(seconds=self.max_seconds)

        while self.chunks and self.chunks[0].timestamp < cutoff:
            self.chunks.popleft()

    def get_window_text(self) -> str:
        self._discard_old_chunks()
        return "\n".join(chunk.text for chunk in self.chunks)

    def clear(self) -> None:
        self.chunks.clear()

    def __len__(self) -> int:
        self._discard_old_chunks()
        return len(self.chunks)
