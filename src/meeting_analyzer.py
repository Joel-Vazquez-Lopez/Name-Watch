import json
import re
from typing import Dict, Optional

from interview_question_bank import match_interview_question

from llm_client import LLMClient


SYSTEM_PROMPT = """
You are NameWatch Live, a privacy-aware live audio assistant.

Rules:
- Return ONLY valid JSON.
- Do not invent transcript events.
- Do not store raw transcript.
- Save only compact summaries, notes, questions, and actions.
- Be concise.
"""


class MeetingAnalyzer:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def analyze_event(
        self,
        event: Dict,
        session_context: str,
        transcript_window: str,
        context_mode: str,
        user_name: str = "",
        profile_text: str = "",
    ) -> Dict:
        event_type = event.get("event_type", "event")
        event_text = event.get("text", "")
        evidence_text = event.get("evidence_text", event_text)
        confidence = event.get("confidence", "medium")

        if context_mode == "Interview":
            bank_match = match_interview_question(event_text)
            bank_text = ""
            if bank_match:
                bank_text = f"""
Closest canonical interview question:
{bank_match['canonical_question']}

Question category:
{bank_match['category']}

Recommended answer strategy:
{bank_match['strategy']}

Similarity:
{bank_match['similarity']}
"""

            task = f"""
Mode: Interview.
The event text is an interview question or prompt that was detected directly from the transcript.

Your job:
- Keep main_text grounded in the detected event text.
- Use the canonical question only as interpretation help, not as a replacement for what was said.
- Generate a concise answer strategy.
- Generate a short answer draft using the profile/CV if useful.
- Do not invent a different question.

{bank_text}
"""
            alert_type = "Interview question"

        else:
            task = """
Mode: Meeting / Lecture.
The event text is a question, task, or action detected directly from the transcript.

Your job:
- Keep main_text grounded in the detected event text.
- If it is a question, suggest a concise answer.
- If it is a task/action, summarize the next step.
- If the user name is provided, prioritize relevance to that person.
"""
            alert_type = "Question / action"

        user_prompt = f"""
{task}

Detected event:
Type: {event_type}
Normalized question/text:
{event_text}

Transcript evidence:
{evidence_text}

Confidence: {confidence}

User name:
{user_name if user_name else "(not provided)"}

Profile/CV:
{profile_text if profile_text else "(not provided)"}

Compact session memory:
{session_context if session_context else "(empty)"}

Recent transcript context:
{transcript_window}

Return this exact JSON schema:
{{
  "window_summary": "one sentence summary of the recent context",
  "updated_meeting_summary": "compact updated memory summary",
  "should_alert": true,
  "alert_type": "{alert_type}",
  "main_text": "{event_text}",
  "support_text": "short suggested answer, strategy, or next step",
  "questions": [],
  "action_items": [],
  "key_points": [],
  "flashcards": [],
  "memory_items": [
    {{
      "type": "{event_type}",
      "summary": "{event_text}",
      "importance": "medium"
    }}
  ],
  "confidence": "{confidence}"
}}
"""

        raw = self.llm.chat_text(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=650,
        )

        result = self._parse_json_safely(raw)
        return self._normalize_result(result, fallback_alert_type=alert_type, fallback_text=event_text)

    def analyze_meeting_digest(
        self,
        session_context: str,
        recent_transcript: str,
        user_name: str = "",
        profile_text: str = "",
    ) -> Dict:
        user_prompt = f"""
Mode: Meeting / Lecture.

You are a live meeting/class companion.
Your job is to understand the newest speech and produce a useful live digest.

Priorities:
1. If the user's name or alias is mentioned near a question/request, treat it as highest priority.
2. Also capture normal questions, comments, explanations, definitions, decisions, and useful lecture points.
3. If there is a direct question to the user, provide a short suggested answer.
4. If there is no direct question, still summarize what was just said if it contains useful content.
5. Do not alert for greetings, filler, repeated names only, unclear fragments, or random noise.

User name / aliases:
{user_name if user_name else "(not provided)"}

Profile/CV:
{profile_text if profile_text else "(not provided)"}

Compact session memory:
{session_context if session_context else "(empty)"}

Newest meeting/lecture transcript:
{recent_transcript}

Return ONLY this JSON:
{{
  "window_summary": "one sentence summary of what just happened",
  "updated_meeting_summary": "compact updated memory summary",
  "should_alert": true,
  "alert_type": "Meeting / lecture digest",
  "main_text": "clean digest of the newest speech. If a name-directed question exists, put it first under Question/action, then include the useful context.",
  "support_text": "short suggested answer if there is a direct question/request; otherwise a short takeaway or memory cue",
  "questions": [],
  "action_items": [],
  "key_points": [],
  "flashcards": [],
  "memory_items": [
    {{
      "type": "meeting_digest",
      "summary": "compact note worth saving",
      "importance": "medium"
    }}
  ],
  "confidence": "medium"
}}

Important:
- If the transcript contains only names, filler, silence, greetings, or unclear fragments, set should_alert false.
- If useful content exists, set should_alert true.
- Do not invent facts beyond the transcript.
- Do not copy a long raw transcript; rewrite it as a clean note.
"""

        raw = self.llm.chat_text(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=750,
        )

        return self._normalize_result(
            self._parse_json_safely(raw),
            fallback_alert_type="Meeting / lecture digest",
            fallback_text="",
        )


    def summarize_window(
        self,
        session_context: str,
        transcript_window: str,
        latest_transcript: str,
        context_mode: str,
    ) -> Dict:
        if context_mode == "Video":
            mode_task = """
Mode: Video.
Summarize useful learning content from the recent transcript window.
This mode is not for question detection.
Create compact notes that the user can read later.
"""
            alert_type = "Video note"

        else:
            mode_task = """
Mode: Meeting / Lecture.
Act like a live class/meeting notebook.
No direct question/task event was detected.
Extract useful meeting or lecture information if the recent transcript contains:
- a topic being introduced;
- an explanation;
- a definition;
- an example;
- a comparison;
- a decision;
- an important instruction;
- a useful takeaway.

Set should_alert true for meaningful content so it appears in the overlay and is saved to notes.
Set should_alert false only for filler, repeated fragments, unclear speech, or social noise.
"""
            alert_type = "Lecture note"

        user_prompt = f"""
{mode_task}

Compact session memory:
{session_context if session_context else "(empty)"}

Newest transcript chunk:
{latest_transcript}

Recent transcript window:
{transcript_window}

Return this exact JSON schema:
{{
  "window_summary": "short summary",
  "updated_meeting_summary": "compact updated memory summary",
  "should_alert": false,
  "alert_type": "{alert_type}",
  "main_text": "",
  "support_text": "",
  "questions": [],
  "action_items": [],
  "key_points": [],
  "flashcards": [],
  "memory_items": [],
  "confidence": "medium"
}}

Set should_alert true only if there is a clear useful idea, explanation, takeaway, definition, example, decision, or action.
If should_alert is true:
- main_text should be the clean note.
- support_text should be a short memory cue or practical takeaway.
- memory_items should contain the compact note.
Do not copy the raw transcript.
"""

        raw = self.llm.chat_text(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=650,
        )

        return self._normalize_result(
            self._parse_json_safely(raw),
            fallback_alert_type=alert_type,
            fallback_text="",
        )

    def _normalize_result(
        self,
        result: Dict,
        fallback_alert_type: str = "Important moment",
        fallback_text: str = "",
    ) -> Dict:
        if not isinstance(result, dict):
            result = {}

        result.setdefault("window_summary", "")
        result.setdefault("updated_meeting_summary", "")
        result.setdefault("should_alert", False)
        result.setdefault("alert_type", fallback_alert_type)
        result.setdefault("main_text", fallback_text)
        result.setdefault("support_text", "")
        result.setdefault("questions", [])
        result.setdefault("action_items", [])
        result.setdefault("key_points", [])
        result.setdefault("flashcards", [])
        result.setdefault("memory_items", [])
        result.setdefault("confidence", "medium")

        result["should_alert"] = bool(result.get("should_alert", False))
        result["alert_type"] = str(result.get("alert_type") or fallback_alert_type).strip()
        result["main_text"] = str(result.get("main_text") or fallback_text).strip()
        result["support_text"] = str(result.get("support_text") or "").strip()

        if result["should_alert"] and result["main_text"] and not result["memory_items"]:
            result["memory_items"] = [
                {
                    "type": result["alert_type"],
                    "summary": result["main_text"],
                    "importance": "medium",
                }
            ]

        return result

    def _parse_json_safely(self, raw: str) -> Dict:
        raw = raw.strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        cleaned = raw.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return {
            "window_summary": "The model output could not be parsed as JSON.",
            "updated_meeting_summary": "",
            "should_alert": False,
            "alert_type": "",
            "main_text": "",
            "support_text": "",
            "questions": [],
            "action_items": [],
            "key_points": [],
            "flashcards": [],
            "memory_items": [],
            "confidence": "low",
        }
