"""
Jarvis Data Analyst - Configuration

All secrets/settings are read from environment variables. Never hardcode
anything sensitive here.

Optional env vars:
    OLLAMA_MODEL          - model name for Ollama, default "llama3.1"
    OLLAMA_HOST           - default "http://localhost:11434"

Requires Ollama running locally (ollama serve) with OLLAMA_MODEL pulled.
"""

import os

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# Number of sources to pull for a "deep research" request
RESEARCH_SOURCE_COUNT = 5

# Max characters of article text fed into the summarizer per source
# (keeps token usage sane and avoids blowing the context window)
MAX_CHARS_PER_SOURCE = 6000

# ---------------------------------------------------------------------------
# Voice pipeline
# ---------------------------------------------------------------------------

SAMPLE_RATE = 16000

# Wake word: openWakeWord ships a pretrained "hey_jarvis" model, downloaded
# on first run via openwakeword.utils.download_models()
WAKE_WORD_MODEL = "hey_jarvis"
WAKE_WORD_THRESHOLD = 0.5          # 0-1, lower = more sensitive / more false triggers
WAKE_WORD_CHUNK = 1280             # 80ms @ 16kHz, openWakeWord's expected frame size

# Utterance recording (ACTIVE state) - simple energy-based end-of-speech detection
SILENCE_RMS_THRESHOLD = 500        # tune this to your mic/room noise floor
SILENCE_DURATION_S = 1.2           # how long silence must persist to end an utterance
MAX_UTTERANCE_S = 15               # hard cap so a stuck open mic can't hang forever

# Speech-to-text (faster-whisper). "base.en" is a good speed/accuracy default;
# "small.en" is more accurate but slower on CPU-only machines.
WHISPER_MODEL_SIZE = "base.en"

# Say any of these while ACTIVE to put Jarvis back to sleep (checked as a
# substring match against the lowercased transcript, not a second wake model)
DEACTIVATION_PHRASES = [
    "go to sleep",
    "go back to sleep",
    "stop listening",
    "that's all",
    "that will be all",
    "goodbye jarvis",
    "jarvis stop",
]

# Set False to run silent (text-only) - useful for testing without speakers
TTS_ENABLED = True