# Name-Watch

## Project summary

**NameWatch Live** is a privacy-aware live meeting intelligence agent. It captures live audio, transcribes it into text, analyzes the recent transcript context, and produces useful meeting intelligence in real time.

The system is designed for meetings, interviews, lectures, and group discussions where live transcription or note-taking is permitted. Instead of storing or summarizing an entire meeting, NameWatch works with short rolling transcript windows. It extracts only the information that matters and discards unnecessary context.

The agent can:

- capture live audio from a microphone or system audio;
- transcribe speech locally using `faster-whisper`;
- analyze recent transcript windows with an AI model;
- summarize what has just been said;
- detect important questions;
- generate suggested answers to questions when enough context is available;
- extract action items, deadlines, decisions, and risks;
- identify moments that should be brought to the user’s attention;
- save compact structured memory instead of storing the full transcript;
- allow later search over saved meeting memory.

The main idea is not simply to detect when a specific name is mentioned. The goal is broader: NameWatch acts as a real-time meeting companion that helps the user stay informed, understand what is happening, and respond more effectively.

### Example

If the conversation contains:

```text
Alice: We need someone to explain why adaptive retrieval is better than fixed top-k.
Ben: Could someone prepare a short answer for that before Friday?


## Responsible and intended use

NameWatch Live is an educational prototype for exploring live transcription, AI agents, Information Retrieval, and privacy-aware memory design.

The system is intended to be used only in contexts where transcription, recording, or AI-assisted note-taking is permitted. This may include:

- personal study sessions;
- self-recorded test audio;
- synthetic or demo meetings;
- consented meetings or interviews;
- lectures or discussions where transcription is allowed;
- accessibility or note-taking contexts where use is authorized.

NameWatch is **not intended** for covert surveillance, unauthorized recording, hidden monitoring, or use in situations where participants have not been informed or where recording/transcription is prohibited by law, institutional rules, workplace policies, or meeting expectations.

Users are responsible for making sure that their use of the system complies with applicable laws, policies, and consent requirements in their jurisdiction.

For the project demo, the recommended setup is to use synthetic, self-created, or clearly authorized audio rather than private real-world conversations.

---

## Privacy protector system

NameWatch includes a privacy-protection layer designed to minimize how much information is stored.

The main principle is:

> The system should process live audio temporarily, extract useful meeting intelligence, and delete unnecessary conversation data.

Instead of keeping a full recording or full transcript, NameWatch uses **short-term rolling memory**.

### What the protector system does

The privacy protector is designed to:

- avoid permanent storage of raw audio;
- delete temporary audio chunks immediately after transcription;
- avoid saving the full transcript by default;
- keep only a short rolling transcript buffer during live processing;
- discard old transcript context automatically;
- store only compact structured outputs when needed;
- avoid saving irrelevant small talk or personal details;
- allow the user to run the system in strict privacy mode.

### Rolling memory

During a live meeting, NameWatch keeps only the most recent transcript window, for example the last 30–120 seconds.

This short-term memory is used so the AI model can understand recent context.

Example:

```text
Recent rolling window:
- last 60 seconds of transcript
- used for summary/question/action-item extraction
- automatically overwritten as new speech arrives
