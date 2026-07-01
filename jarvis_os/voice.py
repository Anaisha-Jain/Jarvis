"""
Jarvis Data Analyst - Voice Activation

State machine:
  IDLE   -> listening only for the wake word (openWakeWord, cheap, always-on)
  ACTIVE -> listening for spoken commands, transcribing each utterance,
            routing it to the orchestrator, until a deactivation phrase
            is heard

Wake word:     "hey jarvis"   (openWakeWord ships a pretrained model for this)
Deactivation:  any phrase in config.DEACTIVATION_PHRASES - matched against
               the transcribed text, not a second wake-word model. This
               keeps things simple: whatever you say while ACTIVE gets
               transcribed anyway, so checking it for a sleep phrase is free.

First run will download the wake word model and whisper weights - both
happen automatically, but need internet access once.
"""

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from openwakeword.model import Model as WakeWordModel

import config as config
from orchestrator import route_command

try:
    import pyttsx3
    _tts_engine = pyttsx3.init()
except Exception:
    _tts_engine = None


def speak(text: str):
    print(f"\U0001F50A Jarvis: {text}")
    if _tts_engine and config.TTS_ENABLED:
        _tts_engine.say(text)
        _tts_engine.runAndWait()


class JarvisVoiceSession:
    def __init__(self):
        print("Loading wake word model...")
        self.wake_model = WakeWordModel(
            wakeword_models=[config.WAKE_WORD_MODEL],
            inference_framework="onnx",
        )
        print("Loading speech recognition model (first run downloads weights)...")
        self.whisper = WhisperModel(config.WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
        self.state = "IDLE"

    def run(self):
        speak("Standing by.")
        while True:
            if self.state == "IDLE":
                self._wait_for_wake_word()
            elif self.state == "ACTIVE":
                self._handle_active_turn()

    # -- IDLE: cheap always-on wake word spotting ---------------------------
    def _wait_for_wake_word(self):
        with sd.InputStream(
            samplerate=config.SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=config.WAKE_WORD_CHUNK,
        ) as stream:
            while self.state == "IDLE":
                chunk, _ = stream.read(config.WAKE_WORD_CHUNK)
                audio = chunk[:, 0]
                predictions = self.wake_model.predict(audio)
                score = predictions.get(config.WAKE_WORD_MODEL, 0.0)
                if score > config.WAKE_WORD_THRESHOLD:
                    self.wake_model.reset()
                    self.state = "ACTIVE"
                    speak("Yes, Sir?")

    # -- ACTIVE: record -> transcribe -> route, until sleep phrase ----------
    def _handle_active_turn(self):
        audio = self._record_until_silence()
        if audio is None or len(audio) < config.SAMPLE_RATE * 0.3:
            return  # too short / just noise - stay ACTIVE, listen again

        text = self._transcribe(audio)
        if not text.strip():
            return

        print(f"\U0001F399\uFE0F  Heard: {text}")

        if self._is_deactivation(text):
            speak("Going back to sleep.")
            self.state = "IDLE"
            return

        response = route_command(text)
        speak(response)

    def _is_deactivation(self, text: str) -> bool:
        lowered = text.lower()
        return any(phrase in lowered for phrase in config.DEACTIVATION_PHRASES)

    def _record_until_silence(self):
        """
        Energy-based (RMS) end-of-speech detection: start recording once
        volume crosses the noise floor, stop after SILENCE_DURATION_S of
        quiet. Simple and dependency-light; swap for webrtcvad if you need
        more robustness in noisy environments.
        """
        sr = config.SAMPLE_RATE
        chunk_ms = 100
        chunk_samples = int(sr * chunk_ms / 1000)
        silence_chunks_needed = int(config.SILENCE_DURATION_S * 1000 / chunk_ms)
        max_chunks = int(config.MAX_UTTERANCE_S * 1000 / chunk_ms)

        frames = []
        silent_streak = 0
        speech_started = False

        with sd.InputStream(
            samplerate=sr, channels=1, dtype="int16", blocksize=chunk_samples
        ) as stream:
            for _ in range(max_chunks):
                chunk, _ = stream.read(chunk_samples)
                chunk = chunk[:, 0]
                rms = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))

                if rms > config.SILENCE_RMS_THRESHOLD:
                    speech_started = True
                    silent_streak = 0
                    frames.append(chunk)
                elif speech_started:
                    silent_streak += 1
                    frames.append(chunk)
                    if silent_streak >= silence_chunks_needed:
                        break
                # else: still waiting for speech to start - keep looping

        if not frames:
            return None
        return np.concatenate(frames)

    def _transcribe(self, audio: np.ndarray) -> str:
        audio_float = audio.astype(np.float32) / 32768.0
        segments, _ = self.whisper.transcribe(audio_float, language="en")
        return " ".join(seg.text for seg in segments).strip()


if __name__ == "__main__":
    session = JarvisVoiceSession()
    session.run()
