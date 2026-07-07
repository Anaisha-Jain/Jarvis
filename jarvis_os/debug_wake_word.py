"""
debug_wake_word.py

Standalone diagnostic: prints the live wake-word confidence score so you
can see whether "Hey Jarvis" is registering at all, and at what score, so
we can tell if this is a threshold problem or a model/mic problem.

Run this directly:
    python debug_wake_word.py

Say "Hey Jarvis" a few times and watch the printed scores. Ctrl+C to stop.
"""

import sounddevice as sd
from openwakeword.model import Model as WakeWordModel

import config as config

print("Available audio input devices:")
print(sd.query_devices())
print(f"\nDefault input device: {sd.query_devices(kind='input')['name']}")
print(f"Using wake word model: {config.WAKE_WORD_MODEL}")
print(f"Current threshold: {config.WAKE_WORD_THRESHOLD}\n")

wake_model = WakeWordModel(
    wakeword_models=[config.WAKE_WORD_MODEL],
    inference_framework="onnx",
)

print("Listening... say 'Hey Jarvis' now.\n")

with sd.InputStream(
    samplerate=config.SAMPLE_RATE,
    channels=1,
    dtype="int16",
    blocksize=config.WAKE_WORD_CHUNK,
) as stream:
    while True:
        chunk, _ = stream.read(config.WAKE_WORD_CHUNK)
        audio = chunk[:, 0]
        predictions = wake_model.predict(audio)
        score = predictions.get(config.WAKE_WORD_MODEL, 0.0)
        if score > 0.05:  # only print when something is happening
            print(f"score: {score:.3f}")
