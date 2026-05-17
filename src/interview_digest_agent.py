import json
import re
from typing import Dict

from llm_client import LLMClient


SYSTEM_PROMPT = """
You are NameWatch Interview Digest Agent.

You receive only a short recent transcript window from an interview.
Your job:
1. Summarize what is happening in this recent window.
2. Extract candidate-facing questions/prompts from this recent window.
3. Generate answer support only if recent questions/prompts are present.

Return ONLY valid JSON:

{
  "moment_summary": "",
  "questions": [],
  "answer_support": "",
  "should_alert": true,
  "confidence": "low/medium/high"
}

Rules:
- Use ONLY the recent transcript window for questions.
- Do not output old questions.
- questions must be a list of strings, not objects.
- Do not output transcript fragments like "for real", "hey", "okay", or "interesting" as questions.
- If the recent window is only filler, set should_alert false.
- If questions is empty, answer_support must be empty.
"""


FILLER_ONLY = {
    "okay", "ok", "hey", "interesting", "for real", "alright", "right",
    "thank you", "i see you", "cool"
}


def _clean_text(text: str) -> str:
    text = str(text or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _question_to_string(item) -> str:
    if isinstance(item, str):
        return _clean_text(item)

    if isinstance(item, dict):
        for key in ("normalized_question", "question", "text", "exact_text"):
            if item.get(key):
                return _clean_text(item.get(key))

    return ""


def _is_useful_text(text: str) -> bool:
    cleaned = _clean_text(text).lower().strip(".,?!")
    if not cleaned:
        return False
    if cleaned in FILLER_ONLY:
        return False
    if len(cleaned.split()) < 4:
        return False
    return True


def is_filler_recent_window(text: str) -> bool:
    cleaned = _clean_text(text).lower().strip(".,?!")
    if not cleaned:
        return True

    filler_phrases = {
        "okay", "ok", "okay interesting", "ok interesting",
        "interesting", "cool", "right", "alright", "for real",
        "thank you", "i see", "i see you"
    }

    if cleaned in filler_phrases:
        return True

    words = cleaned.split()
    if len(words) <= 3 and all(word in filler_phrases or word in {"okay", "ok", "interesting", "cool", "right", "alright"} for word in words):
        return True

    return False



class InterviewDigestAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def analyze(
        self,
        recent_transcript: str,
        profile_text: str = "",
        session_context: str = "",
    ) -> Dict:
        if is_filler_recent_window(recent_transcript):
            return {
                "moment_summary": "",
                "questions": [],
                "answer_support": "",
                "should_alert": False,
                "confidence": "low",
            }

        user_prompt = f"""
Recent interview transcript window:
{recent_transcript.strip()}

Candidate profile/CV:
{profile_text.strip() if profile_text.strip() else "(not provided)"}

Compact session memory:
{session_context.strip() if session_context.strip() else "(empty)"}

Create the live interview digest from the recent transcript only.
Return JSON only.
"""

        raw = self.llm.chat_text(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=750,
        )

        return self._normalize(self._parse_json_safely(raw))

    def _normalize(self, result: Dict) -> Dict:
        if not isinstance(result, dict):
            result = {}

        raw_questions = result.get("questions", [])
        if not isinstance(raw_questions, list):
            raw_questions = []

        questions = []
        for item in raw_questions:
            question = _question_to_string(item)
            if _is_useful_text(question):
                questions.append(question)

        questions = questions[-4:]

        moment_summary = _clean_text(result.get("moment_summary", ""))
        answer_support = _clean_text(result.get("answer_support", ""))
        confidence = _clean_text(result.get("confidence", "medium")).lower()

        if confidence not in {"low", "medium", "high"}:
            confidence = "medium"

        if not questions:
            answer_support = ""

        useful_summary = _is_useful_text(moment_summary)

        return {
            "moment_summary": moment_summary if useful_summary else "",
            "questions": questions,
            "answer_support": answer_support,
            "should_alert": bool(questions or useful_summary),
            "confidence": confidence,
        }

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

        return {}
