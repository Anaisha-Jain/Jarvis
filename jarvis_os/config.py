import os
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("JARVIS_EMAIL")
password = os.getenv("JARVIS_EMAIL_PASSWORD")

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

RESEARCH_SOURCE_COUNT = 5
MAX_CHARS_PER_SOURCE = 6000
SAMPLE_RATE = 16000

WAKE_WORD_MODEL = "hey_jarvis"
WAKE_WORD_THRESHOLD = 0.5          
WAKE_WORD_CHUNK = 1280             
SILENCE_RMS_THRESHOLD = 500        
SILENCE_DURATION_S = 1.2           
MAX_UTTERANCE_S = 15               

WHISPER_MODEL_SIZE = "base.en"

DEACTIVATION_PHRASES = [
    "go to sleep",
    "go back to sleep",
    "stop listening",
    "that's all",
    "that will be all",
    "goodbye jarvis",
    "jarvis stop",
]

TTS_ENABLED = True