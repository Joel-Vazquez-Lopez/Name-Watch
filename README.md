# NameWatch Live

NameWatch Live is a privacy-aware live AI companion for audio streams. It captures microphone or system audio, transcribes speech locally with `faster-whisper`, analyses short rolling transcript windows with an OpenAI-compatible LLM, and displays useful real-time alerts in a minimal Tkinter overlay.

The project supports three focused modes:

- **Meeting / Lecture**: live summaries, useful notes, and name-directed questions/actions
- **Interview**: interview question detection and answer support using an optional profile/CV
- **Video**: study notes, explanations, and key learning points from educational content

NameWatch is designed as an educational AI-agent prototype focused on live context selection, privacy-aware memory, and real-time assistance.

---

## Demo Idea

NameWatch runs as a small always-on-top desktop overlay.

It listens to a live audio stream, detects useful moments, and shows concise help such as:

```text
Meeting / lecture digest

The speaker introduced a key idea about the topic.

Question/action:
[Name], what do you think about this approach?

Suggested answer:
A concise response based on the recent context.
```

For videos or lectures, it saves compact notes that can be reviewed later.

For interviews, it detects prompts and generates answer support.

---

## Features

- Live local transcription with `faster-whisper`
- Microphone input support
- macOS system-audio support through BlackHole
- OpenAI-compatible LLM support
- Minimal Tkinter overlay
- Name/alias-aware question detection
- Interview answer support using an optional local profile/CV
- Video and lecture note generation
- Compact notes saved to `outputs/live_notes.md`
- Compact memory saved locally
- Privacy toggle to stop saving notes/memory
- Raw audio is not stored
- Full transcripts are not saved by default

---

## Modes

### Meeting / Lecture

Use this mode for:

- meetings
- seminars
- lectures
- group discussions
- supervision calls
- classes

This mode creates live digests of useful information and gives priority to questions or actions directed at the user.

The name field can contain multiple aliases separated by commas:

```text
[preferred name], [nickname], [common transcription variant]
```

Example transcript:

```text
[Name], what do you think about this method?
```

Example overlay:

```text
Question/action:
[Name], what do you think about this method?

Suggested answer:
A concise answer based on the recent discussion.
```

Meeting/Lecture mode also saves compact notes when useful information is discussed.

---

### Interview

Use this mode for:

- job interviews
- university admissions interviews
- scholarship interviews
- oral exams
- practice interviews

This mode listens for interview-style questions and prompts, then generates concise answer support.

Example transcript:

```text
Why did you choose this programme?
```

Example overlay:

```text
Interview questions

Questions/prompts:
- Why did you choose this programme?

Suggested answer:
Connect your background, motivation, and future goals to the programme.
```

If `data/profile.txt` exists, NameWatch can use it as personal context for answer suggestions.

---

### Video

Use this mode for:

- YouTube lectures
- tutorials
- online courses
- recorded talks
- study videos

This mode focuses on:

- key concepts
- definitions
- examples
- comparisons
- takeaways
- memory cues

It saves compact study notes to:

```text
outputs/live_notes.md
```

---

## Privacy Design

NameWatch is designed to avoid storing unnecessary private data.

By default:

- raw audio is not stored
- temporary audio files are deleted after transcription
- full transcripts are not saved
- only a short rolling transcript buffer is kept in memory
- only compact notes and memory items are saved
- the overlay includes a `Do not save notes/memory` checkbox

When the privacy checkbox is enabled, NameWatch can still display live assistance, but it will not save notes or memory items.

---

## Architecture

```text
microphone / system audio
        ↓
sounddevice audio chunks
        ↓
faster-whisper local transcription
        ↓
rolling transcript buffer
        ↓
mode-specific context selection
        ↓
OpenAI-compatible LLM analysis
        ↓
Tkinter overlay
        ↓
compact notes / memory
```

The system is mode-specific instead of using one general prompt for everything. This keeps the behavior easier to understand:

```text
Meeting / Lecture → live digest + name-directed questions/actions
Interview         → interview prompts + answer support
Video             → study notes + learning summaries
```

---

## Repository Structure

```text
NameWatch/
├── data/
│   ├── profile.example.txt
│   └── profile.txt              # local/private, ignored by git
├── memory/
│   └── .gitkeep
├── outputs/
│   └── .gitkeep
├── src/
│   ├── main.py
│   ├── live_transcriber.py
│   ├── llm_client.py
│   ├── meeting_analyzer.py
│   ├── interview_digest_agent.py
│   ├── interview_question_bank.py
│   ├── event_detector.py
│   ├── overlay_window.py
│   ├── rolling_buffer.py
│   ├── session_memory.py
│   ├── memory_store.py
│   ├── privacy_protector.py
│   ├── test_system_audio.py
│   └── test_transcription.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

Create a Python environment:

```bash
conda create -n namewatch python=3.10 -y
conda activate namewatch
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create a local environment file:

```bash
cp .env.example .env
```

Edit `.env`:

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.berget.ai/v1
MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
```

Any OpenAI-compatible endpoint can be used.

---

## Optional Profile / CV

For Interview mode, create a local profile:

```bash
cp data/profile.example.txt data/profile.txt
```

Then edit:

```text
data/profile.txt
```

This file can include:

- background
- education
- skills
- projects
- experience
- strengths
- goals
- interview notes

`data/profile.txt` is ignored by git because it may contain personal information.

---

## Audio Devices

List available audio input devices:

```bash
python - <<'PY'
import sounddevice as sd

for i, device in enumerate(sd.query_devices()):
    print(i, device["name"], "inputs:", device["max_input_channels"])
PY
```

Example output:

```text
0 BlackHole 2ch inputs: 2
1 Built-in Microphone inputs: 1
```

Use microphone input:

```bash
python src/main.py --verbose --device 1
```

Use system audio through BlackHole:

```bash
python src/main.py --verbose --device 0
```

---

## macOS System Audio

macOS does not allow Python to directly capture computer audio by default.

To capture audio from videos, calls, or meetings, install BlackHole 2ch and route system audio through it.

Use this for:

- video lectures
- online meetings
- recorded interviews
- tutorials
- browser audio

For quick testing with your own voice, use the microphone input instead.

---

## Running the App

Start NameWatch:

```bash
conda activate namewatch
python src/main.py --verbose --device 1
```

The overlay will open with:

- mode selector
- name/alias field
- privacy save toggle
- live alert area

Recommended name format:

```text
[preferred name], [nickname], [common transcription variant]
```

---

## Outputs

When saving is enabled, compact notes are saved to:

```text
outputs/live_notes.md
```

Compact memory items are saved to:

```text
memory/meeting_memory.json
```

These files are ignored by git.

---

## Responsible Use

NameWatch is an educational prototype.

Use it only where transcription or recording is permitted and participants are appropriately informed.

---

## Limitations

- Transcription quality depends on audio quality.
- Question detection depends on the transcript produced by Whisper.
- The overlay is intentionally minimal.
- LLM suggestions should be checked by the user.
- The system is not a replacement for official recording, accessibility, or compliance tools.

---

## Project Framing

NameWatch Live demonstrates an AI agent that improves live context handling.

Instead of saving or sending a full transcript, it uses:

- local transcription
- rolling context windows
- mode-specific analysis
- name-aware event detection
- compact notes
- privacy-aware memory

This makes the system useful for real-time meetings, interviews, and study sessions while keeping the implementation understandable and lightweight.