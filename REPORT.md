
# NameWatch Live: A Privacy-Aware Live AI Companion

**GitHub repository:** https://github.com/Joel-Vazquez-Lopez/Name-Watch  
**Demo video:** https://youtu.be/VqUyK7D0EX0  

**Video note:** the demo video has intentionally loud music at the beginning and end, so please be careful with the volume.

## 1. Introduction

NameWatch Live is a privacy-aware AI agent for live audio streams. The system captures microphone or system audio, transcribes it locally with `faster-whisper`, keeps a short rolling transcript buffer, and uses an OpenAI-compatible language model to decide which moments are useful enough to show in a desktop overlay. The final prototype supports three modes: Meeting / Lecture, Interview, and Video.

The goal of the project is to extend an AI agent in a practical way: instead of acting only as a chatbot, the agent monitors a live information stream and helps the user react to important moments. In Meeting / Lecture mode, it creates live digests and prioritizes questions directed at the user. In Interview mode, it detects interview-style prompts and suggests answer support. In Video mode, it summarizes key learning points and saves compact notes.

## 2. Motivation

The motivation for this project was to experiment with the possibilities and limitations of speech-to-text technology in a live AI-agent setting. I wanted to see how useful a small local transcription pipeline could be when combined with an LLM agent, and whether the system could react to live speech quickly enough to feel helpful.

The project also explores a practical problem: in meetings, lectures, interviews, and videos, important moments are easy to miss. Someone might say your name, ask a question, explain a key concept, or give an important instruction. A useful agent should not only answer typed questions, but should also help filter a live stream of information.

Systems such as OpenClaw show the broader direction of personal AI agents: agents that can connect to user workflows and act proactively. NameWatch Live explores a narrower and more controlled version of this idea. Instead of giving the agent broad control over the computer, the system focuses on one useful capability: helping the user follow live audio. This makes the project more limited than a general personal assistant, but also easier to reason about from a privacy and safety perspective.

The novelty of the project is the combination of live speech transcription, mode-specific agent behaviour, name-aware event detection, compact memory, and a privacy toggle in a small desktop assistant. The system is not just a summarizer; it changes its behaviour depending on the selected context mode.

## 3. System Design

The pipeline is:

```text
audio input
→ local transcription
→ rolling transcript buffer
→ mode-specific analysis
→ LLM response
→ Tkinter overlay
→ optional compact notes / memory
The system uses three modes because a single general prompt became unreliable during development. Each mode has a clearer purpose:

Meeting / Lecture: detect useful discussion, create live digests, and prioritize questions or actions directed at the user.
Interview: detect interview prompts and generate answer support using an optional local profile.
Video: extract key concepts, explanations, and study notes.
This design makes the agent easier to control. It also improves the user experience because the same audio stream can be interpreted differently depending on the task.

## 4. Privacy Design
Privacy was a core requirement. NameWatch Live avoids storing unnecessary raw data. Raw audio is deleted after transcription, full transcripts are not saved by default, and only a short rolling transcript window is kept temporarily. The app includes a visible checkbox labelled “Do not save notes/memory”. When enabled, the system can still provide live assistance but does not save notes or memory items.

This is important because the system may be used in meetings, interviews, or lectures where sensitive information could be spoken. The prototype is intended only for situations where transcription is permitted and participants are appropriately informed.

## 5. Implementation
The project is implemented in Python. Audio capture is handled with sounddevice; local transcription is handled with faster-whisper; LLM calls use an OpenAI-compatible API client; and the user interface is a minimal Tkinter overlay.

The code is organized into separate modules for transcription, buffering, memory, privacy filtering, event detection, interview digestion, and overlay display. This separation made it easier to debug the system and replace earlier over-complicated logic with clearer mode-specific behaviour.

##6. Reflection on Working With AI (done with ai as it was similar to the first project)
AI coding tools were helpful throughout the assignment, especially for brainstorming, debugging, refactoring, and writing documentation. They helped generate possible architectures and made it faster to test different approaches. For example, the project initially had too many overlapping rules for interview detection, meeting detection, summaries, and fallback alerts. AI assistance helped identify that the design was becoming too complex, and the system was simplified into three focused modes.

However, the process also showed the limits of AI-generated code. Some early versions over-detected questions, missed incomplete transcript chunks, or repeated old alerts. These issues only became clear through real testing with microphone and system audio. The final version improved because I tested the behaviour manually, checked the outputs, and decided when the design needed to change.

AI was also useful for creating the README and report drafts, but I still needed to verify that the documentation matched the actual code. I also checked that private files such as .env, data/profile.txt, saved memory, and output notes were ignored before uploading the repository.

For the demo video, I also experimented with AI-generated media. Some of the images, video-style intro/outro material, and music were generated with AI for fun. This was not essential to the technical system, but it was interesting to experiment with how generative AI can also support presentation and communication. It helped make the demo more memorable, although the actual grading focus should remain on the code and system behaviour.

Overall, AI made the development process faster, but it did not remove the need for human judgment. The most useful workflow was to use AI as a collaborator for suggestions and debugging while keeping responsibility for testing, design decisions, privacy choices, and final verification.

##7. Limitations and Future Work
The system is a working prototype, but it is not perfect. Transcription quality depends on audio quality, and the agent may still miss or misinterpret some questions. The current event detection is intentionally lightweight. Future work could improve robustness with better voice activity detection, stronger semantic retrieval, speaker diarization, configurable profiles, and more formal evaluation.
```
