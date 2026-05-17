import os
import tempfile
from typing import Iterator, Optional

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel


class LiveAudioTranscriber:
    """
    Captures audio from a selected input device, transcribes it locally with faster-whisper,
    and deletes temporary audio immediately after transcription.

    This class works for both:
    - microphone input
    - BlackHole/system-audio input
    """

    def __init__(
        self,
        device: Optional[int] = None,
        model_size: str = "base",
        sample_rate: int = 16000,
        chunk_seconds: int = 5,
        language: str = "en",
    ):
        self.device = device
        self.sample_rate = sample_rate
        self.chunk_seconds = chunk_seconds
        self.language = language

        print(f"Loading faster-whisper model: {model_size}")
        self.model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8"
        )

    def record_chunk(self) -> np.ndarray:
        audio = sd.rec(
            int(self.chunk_seconds * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            device=self.device,
        )
        sd.wait()
        return audio

    def transcribe_chunk(self, audio: np.ndarray) -> str:
        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_path = tmp.name

            audio = np.clip(audio, -1.0, 1.0)
            audio_int16 = (audio * 32767).astype(np.int16)

            write(temp_path, self.sample_rate, audio_int16)

            segments, _ = self.model.transcribe(
                temp_path,
                language=self.language,
                beam_size=1,
                vad_filter=True,
            )

            text = " ".join(segment.text.strip() for segment in segments)
            return text.strip()

        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def stream(self, stop_event=None) -> Iterator[str]:
        while True:
            if stop_event is not None and stop_event.is_set():
                break

            audio = self.record_chunk()

            if stop_event is not None and stop_event.is_set():
                del audio
                break

            text = self.transcribe_chunk(audio)

            # Privacy: remove raw audio from memory reference immediately.
            del audio

            if text:
                yield text
