import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from openwakeword.model import Model as WakeWordModel

import config as config
from orchestrator import route_command

try:
    import pyttsx3
    _PYTTSX3_AVAILABLE = True
except Exception:
    _PYTTSX3_AVAILABLE = False


def speak(text: str):
    print(f"🔊 Jarvis: {text}")
    if not (_PYTTSX3_AVAILABLE and config.TTS_ENABLED):
        return

    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    engine.stop()


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

    def _handle_active_turn(self):
        audio = self._record_until_silence()
        if audio is None or len(audio) < config.SAMPLE_RATE * 0.3:
            return  

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
