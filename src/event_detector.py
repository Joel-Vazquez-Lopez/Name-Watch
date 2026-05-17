import re
from typing import Dict, List, Optional


QUESTION_STARTS = (
    "who", "what", "why", "how", "where", "when",
    "do", "does", "did", "is", "are", "was", "were",
    "can", "could", "would", "will", "should",
)

PROMPT_STARTS = (
    "tell me", "tell us", "walk me", "walk us",
    "describe", "explain", "introduce yourself",
    "let's start", "lets start", "let us start",
    "i would like to hear", "we would like to hear",
    "it would be useful to understand",
    "i am curious", "we are curious",
)

TASK_SIGNALS = (
    "can you", "could you", "please", "you should",
    "you need to", "you have to", "make sure you",
    "prepare", "review", "send", "follow up", "by friday",
    "by tomorrow", "deadline",
)

INVITE_QUESTION_SIGNALS = (
    "ask me anything",
    "ask me whatever",
    "ask me what",
    "about the company",
    "about the role",
    "do you have any questions for us",
    "do you have questions for us",
    "feel free to ask",
    "let me know if you have questions",
)


def normalize(text: str) -> str:
    text = text.lower().replace("’", "'")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def name_matches(text: str, user_name: str = "") -> bool:
    if not user_name.strip():
        return False

    lowered = normalize(text)
    aliases = [
        alias.strip().lower()
        for alias in re.split(r"[,/|]", user_name)
        if alias.strip()
    ]

    return any(alias in lowered for alias in aliases)


def split_segments(text: str) -> List[str]:
    text = text.replace("\n", " ").strip()
    if not text:
        return []

    parts = re.split(r"(?<=[\?\.\!])\s+|;\s+", text)
    segments = []

    for part in parts:
        part = part.strip(" ,")
        if len(part.split()) >= 3:
            segments.append(part)

    return segments[-10:]


def looks_incomplete(text: str) -> bool:
    words = normalize(text).strip("?.!,").split()
    if len(words) < 3:
        return True

    bad_endings = {
        "why", "what", "how", "who", "where", "when",
        "your", "about", "and", "or", "then",
        "the", "a", "an", "to", "for", "with", "of",
    }

    return words[-1] in bad_endings


def is_invitation_to_ask(text: str) -> bool:
    lowered = normalize(text)
    return any(signal in lowered for signal in INVITE_QUESTION_SIGNALS)


def is_question_like(text: str) -> bool:
    lowered = normalize(text).strip()

    if is_invitation_to_ask(lowered) or looks_incomplete(lowered):
        return False

    words = lowered.split()
    first = words[0] if words else ""

    if "?" in lowered and len(words) >= 4:
        return True

    if first in QUESTION_STARTS and len(words) >= 4:
        return True

    if lowered.startswith(PROMPT_STARTS) and len(words) >= 4:
        return True

    return False


def is_task_like(text: str, user_name: str = "") -> bool:
    lowered = normalize(text)
    if looks_incomplete(lowered):
        return False

    has_task_signal = any(signal in lowered for signal in TASK_SIGNALS)
    if not has_task_signal:
        return False

    if user_name and not name_matches(lowered, user_name):
        return False

    return True


def collect_questions_from_latest(latest_transcript: str) -> Optional[str]:
    """
    If the newest chunk contains several interview questions, keep them together.
    This avoids reducing "Who are you? What have you studied so far?" to only one.
    """
    segments = split_segments(latest_transcript)
    questions = [segment for segment in segments if is_question_like(segment)]

    if not questions:
        return None

    combined = " ".join(questions).strip()
    if len(combined.split()) < 4:
        return None

    return combined


def detect_event(
    latest_transcript: str,
    transcript_window: str,
    mode: str,
    user_name: str = "",
) -> Optional[Dict]:
    latest_segments = split_segments(latest_transcript)
    window_segments = split_segments(transcript_window)

    if mode == "Interview":
        # Interview alerts must come from the newest transcript chunk only.
        # The rolling window is context for answer generation, not a source of
        # repeated old questions.
        combined_latest_questions = collect_questions_from_latest(latest_transcript)
        if combined_latest_questions:
            return {
                "event_type": "interview_question",
                "text": combined_latest_questions,
                "source": "latest",
                "confidence": "high",
            }

        return None

    if mode == "Meeting / Lecture":
        segments = latest_segments + [s for s in window_segments if s not in latest_segments]
        segments = segments[-10:]

        for segment in reversed(segments):
            lowered = normalize(segment)

            if is_task_like(segment, user_name=user_name):
                return {
                    "event_type": "task_or_action",
                    "text": segment,
                    "source": "latest" if segment in latest_segments else "window",
                    "confidence": "high" if segment in latest_segments else "medium",
                }

            if is_question_like(segment):
                if user_name and not name_matches(lowered, user_name):
                    continue

                return {
                    "event_type": "question",
                    "text": segment,
                    "source": "latest" if segment in latest_segments else "window",
                    "confidence": "high" if segment in latest_segments else "medium",
                }

    return None
