import argparse
from live_transcriber import LiveAudioTranscriber


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=int, default=None)
    parser.add_argument("--chunk-seconds", type=int, default=5)
    parser.add_argument("--model-size", default="base")
    parser.add_argument("--language", default="en")
    args = parser.parse_args()

    transcriber = LiveAudioTranscriber(
        device=args.device,
        chunk_seconds=args.chunk_seconds,
        model_size=args.model_size,
        language=args.language,
    )

    print("\nListening to audio input.")
    print("For BlackHole/system audio: play a clear English video or meeting audio.")
    print("For microphone: speak clearly into the microphone.")
    print("Press Ctrl+C to stop.\n")

    try:
        for text in transcriber.stream():
            print(f"TRANSCRIPT: {text}")
    except KeyboardInterrupt:
        print("\nStopped transcription.")


if __name__ == "__main__":
    main()
