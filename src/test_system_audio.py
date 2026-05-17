"""
JUST TO CHECK 5 SECONDS THAT THE AUDIO IS WORKING
"""

import sounddevice as sd
import numpy as np

DEVICE = 0  # BlackHole 2ch from your device list
SAMPLE_RATE = 16000
SECONDS = 5

print("Recording 5 seconds from BlackHole...")
print("Play YouTube, Spotify, or any audio now.\n")

audio = sd.rec(
    int(SECONDS * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="float32",
    device=DEVICE
)
sd.wait()

mean_volume = float(np.abs(audio).mean())
max_volume = float(np.abs(audio).max())

print(f"Mean volume: {mean_volume:.6f}")
print(f"Max volume:  {max_volume:.6f}")

if mean_volume > 0.001 or max_volume > 0.01:
    print("\n✅ SUCCESS: Python is capturing system audio through BlackHole.")
else:
    print("\n⚠️ No clear audio detected.")
    print("Check that:")
    print("1. System output is set to Multi-Output Device")
    print("2. Multi-Output Device includes BlackHole 2ch")
    print("3. Audio is actually playing")
    print("4. BlackHole device index is still 0")
