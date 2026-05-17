import argparse
import warnings
import threading
import time
import sounddevice as sd
from datetime import datetime
from pathlib import Path
from typing import Dict

from rich.console import Console
from rich.table import Table

from live_transcriber import LiveAudioTranscriber
from rolling_buffer import RollingTranscriptBuffer
from session_memory import SessionMemory
from llm_client import LLMClient
from meeting_analyzer import MeetingAnalyzer
from privacy_protector import PrivacyProtector
from memory_store import MemoryStore
from overlay_window import NameWatchOverlay
from event_detector import detect_event
from interview_digest_agent import InterviewDigestAgent


warnings.filterwarnings(
    "ignore",
    message="resource_tracker: There appear to be .* leaked semaphore objects.*",
)


console = Console()


RESPONSIBLE_USE_NOTICE = """
Responsible use notice:
NameWatch is an educational prototype. Use it only where transcription or recording is permitted and participants are appropriately informed.
Raw audio is deleted after transcription, full transcripts are not stored by default, and only compact memory items are saved.
"""


class SimpleCooldown:
    def __init__(self, min_seconds: int = 5, repeat_seconds: int = 45):
        self.min_seconds = min_seconds
        self.repeat_seconds = repeat_seconds
        self.last_alert_time = 0.0
        self.last_text_times = {}

    def allow(self, text: str, confidence: str = "medium") -> bool:
        now = time.time()
        normalized = " ".join(text.lower().split())

        if not normalized:
            return False

        previous = self.last_text_times.get(normalized)
        if previous and now - previous < self.repeat_seconds:
            return False

        if confidence != "high" and now - self.last_alert_time < self.min_seconds:
            return False

        self.last_alert_time = now
        self.last_text_times[normalized] = now
        return True


def load_profile(path: str) -> str:
    profile_path = Path(path)
    if not profile_path.exists():
        return ""
    return profile_path.read_text(encoding="utf-8").strip()


def empty_analysis(session_context: str = "") -> Dict:
    return {
        "window_summary": "",
        "updated_meeting_summary": session_context,
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


def analysis_to_alert(analysis: Dict) -> Dict:
    return {
        "type": analysis.get("alert_type") or "Important moment",
        "summary": analysis.get("main_text") or analysis.get("window_summary") or "",
        "suggested_answer": analysis.get("support_text") or "",
        "action_item": "",
        "extra": f"Confidence: {analysis.get('confidence')}" if analysis.get("confidence") else "",
    }


def append_note(path: str, mode: str, analysis: Dict) -> None:
    notes_path = Path(path)
    notes_path.parent.mkdir(parents=True, exist_ok=True)

    main_text = str(analysis.get("main_text") or "").strip()
    support_text = str(analysis.get("support_text") or "").strip()
    alert_type = analysis.get("alert_type") or "Note"

    if not main_text:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    note = f"\n## {timestamp} - {mode} - {alert_type}\n\n{main_text}\n"

    if support_text:
        note += f"\nTakeaway:\n{support_text}\n"

    notes_path.open("a", encoding="utf-8").write(note)


def digest_to_analysis(digest: Dict, session_context: str) -> Dict:
    questions = digest.get("questions", [])
    questions_text = "\n".join(f"- {q}" for q in questions)

    main_text = digest.get("moment_summary", "").strip()

    if questions_text:
        main_text = (main_text + "\n\nQuestions/prompts:\n" + questions_text).strip()

    return {
        "window_summary": digest.get("moment_summary", ""),
        "updated_meeting_summary": session_context,
        "should_alert": bool(digest.get("should_alert")),
        "alert_type": "Interview digest" if not questions else "Interview questions",
        "main_text": main_text,
        "support_text": digest.get("answer_support", ""),
        "questions": questions,
        "action_items": [],
        "key_points": [],
        "flashcards": [],
        "memory_items": [
            {
                "type": "interview_digest",
                "summary": main_text,
                "importance": "medium",
            }
        ] if main_text else [],
        "confidence": digest.get("confidence", "medium"),
    }


def run_live_ai(args):
    console.print("[bold yellow]" + RESPONSIBLE_USE_NOTICE.strip() + "[/bold yellow]\n")

    overlay = NameWatchOverlay()
    stop_event = threading.Event()
    worker = threading.Thread(target=live_ai_worker, args=(args, overlay, stop_event), daemon=False)
    worker.start()

    try:
        overlay.run()
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        try:
            sd.stop()
        except Exception:
            pass
        worker.join(timeout=max(2, args.chunk_seconds + 2))
        console.print("\n[bold green]Closing NameWatch. Thank you for using this system![/bold green]")


def live_ai_worker(args, overlay: NameWatchOverlay, stop_event=None):
    buffer = RollingTranscriptBuffer(max_seconds=args.rolling_window_seconds)
    session_memory = SessionMemory(max_recent_items=args.max_session_items)
    memory_store = MemoryStore(path=args.memory_path)
    privacy = PrivacyProtector(strict=True)

    cooldown = SimpleCooldown(
        min_seconds=args.min_alert_seconds,
        repeat_seconds=args.repeat_alert_seconds,
    )

    profile_text = load_profile(args.profile_path)

    llm_client = LLMClient(model_name=args.ai_model)
    analyzer = MeetingAnalyzer(llm_client=llm_client)
    interview_digest_agent = InterviewDigestAgent(llm_client=llm_client)

    transcriber = LiveAudioTranscriber(
        device=args.device,
        chunk_seconds=args.chunk_seconds,
        model_size=args.transcription_model,
        language=args.language,
    )

    console.print("[bold green]NameWatch live AI mode started.[/bold green]")
    console.print("[dim]Interview digest + meeting events + video notes mode is running.[/dim]\n")

    last_analysis_time = time.time()
    chunk_count = 0
    interview_recent_chunks = []
    meeting_recent_chunks = []

    try:
        for transcript_text in transcriber.stream(stop_event=stop_event):
            chunk_count += 1
            transcript_text = transcript_text.strip()

            context_mode = overlay.get_context_mode()

            if transcript_text:
                buffer.add(transcript_text)
                if context_mode == "Interview":
                    interview_recent_chunks.append(transcript_text)
                    interview_recent_chunks = interview_recent_chunks[-5:]
                elif context_mode == "Meeting / Lecture":
                    meeting_recent_chunks.append(transcript_text)
                    meeting_recent_chunks = meeting_recent_chunks[-5:]

            if args.verbose:
                console.print(f"[dim]TRANSCRIPT: {transcript_text if transcript_text else '(silence)'}[/dim]")
            else:
                console.print(f"[dim]Transcript chunk received ({chunk_count}).[/dim]")
            user_name = overlay.get_user_name()
            session_context = session_memory.get_context_for_ai()

            if context_mode == "Interview":
                effective_interval = args.interview_analysis_interval
            elif context_mode == "Video":
                effective_interval = args.video_analysis_interval
            else:
                effective_interval = args.analysis_interval

            now = time.time()
            immediate_meeting_event = False

            if context_mode == "Meeting / Lecture" and user_name.strip() and transcript_text.strip():
                immediate_meeting_event = bool(
                    detect_event(
                        latest_transcript=transcript_text,
                        transcript_window=transcript_text,
                        mode=context_mode,
                        user_name=user_name,
                    )
                )

            if not immediate_meeting_event and now - last_analysis_time < effective_interval:
                continue

            transcript_window = buffer.get_window_text().strip()
            if not transcript_window:
                last_analysis_time = now
                continue

            console.print(
                f"[cyan]Analyzing window... Mode: {context_mode}. "
                f"Name: {user_name or 'off'}.[/cyan]"
            )

            try:
                if context_mode == "Interview":
                    recent_interview_text = " ".join(interview_recent_chunks).strip() or transcript_window

                    digest = interview_digest_agent.analyze(
                        recent_transcript=recent_interview_text,
                        profile_text=profile_text,
                        session_context="",
                    )
                    analysis = digest_to_analysis(digest, session_context)

                elif context_mode == "Meeting / Lecture":
                    recent_meeting_text = " ".join(meeting_recent_chunks).strip() or transcript_window

                    event = detect_event(
                        latest_transcript=recent_meeting_text,
                        transcript_window=recent_meeting_text,
                        mode=context_mode,
                        user_name=user_name,
                    )

                    analysis = analyzer.analyze_meeting_digest(
                        session_context=session_context,
                        recent_transcript=recent_meeting_text,
                        user_name=user_name,
                        profile_text=profile_text,
                    )

                    if event:
                        console.print(f"[cyan]Detected event: {event['event_type']} - {event['text']}[/cyan]")
                        current_main = str(analysis.get("main_text") or "").strip()
                        analysis["alert_type"] = "Question"
                        analysis["main_text"] = (
                            "Question/action:\n"
                            + event["text"].strip()
                            + ("\n\nContext:\n" + current_main if current_main else "")
                        )
                        analysis["confidence"] = "high"

                    if analysis.get("should_alert"):
                        meeting_recent_chunks.clear()

                else:
                    analysis = analyzer.summarize_window(
                        session_context=session_context,
                        transcript_window=transcript_window,
                        latest_transcript=transcript_text,
                        context_mode=context_mode,
                    )

            except Exception as exc:
                console.print(f"[red]AI analysis failed: {exc}[/red]")
                last_analysis_time = now
                continue

            if overlay.should_save_outputs():
                session_memory.add_analysis(analysis)
                safe_items = privacy.filter_analysis_for_memory(analysis)
                memory_store.save_items(safe_items)
            else:
                console.print("[dim]Privacy save toggle is on: memory/notes not saved.[/dim]")

            if not analysis.get("should_alert", False):
                console.print("[dim]No important alert/note for this window.[/dim]")
                if context_mode == "Interview":
                    interview_recent_chunks.clear()
                last_analysis_time = now
                continue

            alert = analysis_to_alert(analysis)

            note_saved = False
            if context_mode in ("Video", "Meeting / Lecture") and overlay.should_save_outputs():
                append_note(args.notes_path, context_mode, analysis)
                console.print(f"[green]Note saved to {args.notes_path}[/green]")
                note_saved = True

            cooldown_confidence = analysis.get("confidence", "medium")
            if context_mode == "Interview":
                cooldown_confidence = "high"

            if context_mode != "Interview":
                if not cooldown.allow(alert.get("summary", ""), cooldown_confidence):
                    console.print("[dim]Alert suppressed by cooldown, but note was kept.[/dim]")
                    last_analysis_time = now
                    continue

            overlay.push_alert(alert)
            console.print("[bold yellow]Alert sent to overlay.[/bold yellow]")

            if context_mode == "Interview":
                interview_recent_chunks.clear()

            last_analysis_time = now

    except KeyboardInterrupt:
        console.print("\n[bold green]Closing NameWatch. Thank you for using it![/bold green]")


def run_ask(args):
    memory_store = MemoryStore(path=args.memory_path)
    results = memory_store.search(args.question)

    if not results:
        console.print("[yellow]No matching memory items found.[/yellow]")
        return

    table = Table(title="Memory Search Results")
    table.add_column("Time")
    table.add_column("Type")
    table.add_column("Importance")
    table.add_column("Summary")

    for item in results:
        table.add_row(
            item.get("timestamp", ""),
            item.get("type", ""),
            item.get("importance", ""),
            item.get("summary", ""),
        )

    console.print(table)


def run_clear_memory(args):
    memory_store = MemoryStore(path=args.memory_path)
    memory_store.clear()
    console.print("[green]Memory cleared.[/green]")


def main():
    parser = argparse.ArgumentParser(description="NameWatch Live")

    parser.add_argument("--mode", choices=["live-ai", "ask", "clear-memory"], default="live-ai")

    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--chunk-seconds", type=int, default=5)
    parser.add_argument("--transcription-model", default="base")
    parser.add_argument("--language", default="en")

    parser.add_argument("--analysis-interval", type=int, default=8)
    parser.add_argument("--interview-analysis-interval", type=int, default=7)
    parser.add_argument("--video-analysis-interval", type=int, default=10)
    parser.add_argument("--rolling-window-seconds", type=int, default=150)
    parser.add_argument("--max-session-items", type=int, default=20)
    parser.add_argument("--ai-model", default=None)

    parser.add_argument("--min-alert-seconds", type=int, default=5)
    parser.add_argument("--repeat-alert-seconds", type=int, default=45)

    parser.add_argument("--memory-path", default="memory/meeting_memory.json")
    parser.add_argument("--profile-path", default="data/profile.txt")
    parser.add_argument("--notes-path", default="outputs/live_notes.md")
    parser.add_argument("--question", default="")
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()

    if args.mode == "live-ai":
        run_live_ai(args)
    elif args.mode == "ask":
        if not args.question:
            raise ValueError("--question is required in ask mode")
        run_ask(args)
    elif args.mode == "clear-memory":
        run_clear_memory(args)


if __name__ == "__main__":
    main()
