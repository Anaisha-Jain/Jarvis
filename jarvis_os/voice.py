import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from openwakeword.model import Model as WakeWordModel

import config as config
from orchestrator import route_command, clean_spoken_text
from tts_voice import speak as tts_speak


class JarvisVoiceSession:
    def __init__(self, overlay=None):
        """
        overlay: an optional JarvisOverlay instance (see overlay.py). If
        provided, its .show()/.hide() are called around wake-word detection
        and Jarvis's spoken response, so the HUD image appears exactly
        while Jarvis is "on".
        """
        self.overlay = overlay

        print("Loading wake word model...")
        self.wake_model = WakeWordModel(
            wakeword_models=[config.WAKE_WORD_MODEL],
            inference_framework="onnx",
        )
        print("Loading speech recognition model (first run downloads weights)...")
        self.whisper = WhisperModel(config.WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
        self.state = "IDLE"

    def _speak(self, text: str):
        # Overlay stays visible for the whole time Jarvis is talking,
        # then disappears once he's done. Pass the model for interruptions.
        tts_speak(
            text,
            on_start=self.overlay.show if self.overlay else None,
            on_end=self.overlay.hide if self.overlay else None,
            interrupter_model=self.wake_model  
        )

    def run(self):
        self._speak("Standing by.")
        while True:
            if self.state == "IDLE":
                self._wait_for_wake_word()
            elif self.state == "ACTIVE":
                self._handle_active_turn(first_turn=True)

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
                    if self.overlay:
                        self.overlay.show()
                    self._speak("Yes, Sir?")

    def _handle_active_turn(self, first_turn: bool = False):
        # After the first turn, give a shorter window to keep talking
        wait_s = config.MAX_UTTERANCE_S if first_turn else config.FOLLOWUP_LISTEN_TIMEOUT_S

        audio = self._record_until_silence(max_wait_for_speech_s=wait_s)
        if audio is None or len(audio) < config.SAMPLE_RATE * 0.3:
            self.state = "IDLE"
            if self.overlay:
                self.overlay.hide()
            return

        text = self._transcribe(audio)
        text = clean_spoken_text(text)  # Cleans up "at the rate" for emails
        
        if not text.strip():
            self.state = "IDLE"
            if self.overlay:
                self.overlay.hide()
            return

        print(f"\U0001F399\uFE0F  Heard: {text}")

        if self._is_deactivation(text):
            self._speak("Going back to sleep.")
            self.state = "IDLE"
            return

        response = route_command(text)
        self._speak(response)

    def _is_deactivation(self, text: str) -> bool:
        lowered = text.lower()
        return any(phrase in lowered for phrase in config.DEACTIVATION_PHRASES)

    def _record_until_silence(self, max_wait_for_speech_s=None):
        sr = config.SAMPLE_RATE
        chunk_ms = 100
        chunk_samples = int(sr * chunk_ms / 1000)
        silence_chunks_needed = int(config.SILENCE_DURATION_S * 1000 / chunk_ms)
        max_chunks = int(config.MAX_UTTERANCE_S * 1000 / chunk_ms)
        max_wait_chunks = int((max_wait_for_speech_s or config.MAX_UTTERANCE_S) * 1000 / chunk_ms)

        frames = []
        silent_streak = 0
        speech_started = False
        waited_chunks = 0

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
                else:
                    waited_chunks += 1
                    if waited_chunks >= max_wait_chunks:
                        break  # gave up waiting for speech to start

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