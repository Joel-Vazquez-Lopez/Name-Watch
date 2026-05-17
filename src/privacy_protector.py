from typing import Dict, List


ALLOWED_MEMORY_FIELDS = {"type", "summary", "importance"}


class PrivacyProtector:
    """
    Privacy layer for NameWatch.

    It prevents raw transcript context from being saved and keeps only compact,
    structured meeting/study memory.
    """

    def __init__(self, strict: bool = True):
        self.strict = strict

    def filter_analysis_for_memory(self, analysis: Dict) -> List[Dict]:
        memory_items = analysis.get("memory_items", [])

        if not isinstance(memory_items, list):
            return []

        safe_items = []

        for item in memory_items:
            if not isinstance(item, dict):
                continue

            safe_item = {
                key: value
                for key, value in item.items()
                if key in ALLOWED_MEMORY_FIELDS
            }

            summary = str(safe_item.get("summary", "")).strip()

            if not summary:
                continue

            safe_item.setdefault("type", "memory")
            safe_item.setdefault("importance", "medium")

            safe_items.append(safe_item)

        return safe_items

    def make_alert_payload(self, analysis: Dict) -> Dict:
        questions = analysis.get("questions", [])
        action_items = analysis.get("action_items", [])
        decisions = analysis.get("decisions", [])
        risks = analysis.get("risks", [])
        key_points = analysis.get("key_points", [])
        flashcards = analysis.get("flashcards", [])
        important_events = analysis.get("important_events", [])

        alert_type = "Meeting update"
        summary = analysis.get("window_summary", "Important moment detected.")
        suggested_answer = ""
        action_item = ""
        extra = ""

        if isinstance(questions, list) and questions:
            first_q = questions[0]
            alert_type = "Question detected"
            summary = first_q.get("question", summary)
            suggested_answer = first_q.get("suggested_answer", "")

            confidence = first_q.get("confidence", "")
            answer_mode = first_q.get("answer_mode", "")
            question_scope = first_q.get("question_scope", "")

            details = []
            if confidence:
                details.append(f"Confidence: {confidence}")
            if answer_mode:
                details.append(f"Answer mode: {answer_mode}")
            if question_scope:
                details.append(f"Scope: {question_scope}")

            if details:
                extra = " · ".join(details)

        elif isinstance(key_points, list) and key_points:
            first_key = key_points[0]
            alert_type = "Key concept"
            summary = first_key.get("summary", summary)

        elif isinstance(flashcards, list) and flashcards:
            first_card = flashcards[0]
            alert_type = "Flashcard"
            summary = f"Q: {first_card.get('question', '')}"
            suggested_answer = first_card.get("answer", "")

        elif isinstance(action_items, list) and action_items:
            first_action = action_items[0]
            alert_type = "Action item detected"
            task = first_action.get("task", "")
            deadline = first_action.get("deadline", "unspecified")
            assignee = first_action.get("assignee", "unspecified")

            summary = task or summary
            action_item = f"{task} Assignee: {assignee}. Deadline: {deadline}."

        elif isinstance(decisions, list) and decisions:
            first_decision = decisions[0]
            alert_type = "Decision detected"
            summary = first_decision.get("summary", summary)

        elif isinstance(risks, list) and risks:
            first_risk = risks[0]
            alert_type = "Risk/blocker detected"
            summary = first_risk.get("summary", summary)

        elif isinstance(important_events, list) and important_events:
            first_event = important_events[0]
            alert_type = first_event.get("type", "Important event")
            summary = first_event.get("summary", summary)

        return {
            "type": alert_type,
            "summary": summary,
            "suggested_answer": suggested_answer,
            "action_item": action_item,
            "extra": extra
        }
