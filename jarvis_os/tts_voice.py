import asyncio
import os
import tempfile
import uuid

import edge_tts
import pygame
import sounddevice as sd
import keyboard

import config as config

VOICE = "en-GB-RyanNeural"
pygame.mixer.init()

async def _generate_speech(text: str, path: str):
    # Fast voice rate
    communicate = edge_tts.Communicate(text, VOICE, rate="+25%")
    await communicate.save(path)

def speak(text: str, on_start=None, on_end=None, interrupter_model=None):
    if not text:
        return

    if on_start:
        on_start()

    tmp_path = os.path.join(tempfile.gettempdir(), f"jarvis_speech_{uuid.uuid4().hex}.mp3")

    try:
        asyncio.run(_generate_speech(text, tmp_path))
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        
        with sd.InputStream(
            samplerate=config.SAMPLE_RATE, 
            channels=1, 
            dtype="int16", 
            blocksize=config.WAKE_WORD_CHUNK
        ) as stream:
            while pygame.mixer.music.get_busy():
                
                # 1. The Physical Killswitch (Guaranteed to work)
                if keyboard.is_pressed('space'):
                    print("\n[Interrupt] Spacebar pressed! Cutting audio.")
                    pygame.mixer.music.stop()
                    if interrupter_model:
                        interrupter_model.reset()
                    break
                
                # 2. The Voice Killswitch (Works best with headphones)
                if interrupter_model:
                    try:
                        chunk, _ = stream.read(config.WAKE_WORD_CHUNK)
                        predictions = interrupter_model.predict(chunk[:, 0])
                        
                        if predictions.get(config.WAKE_WORD_MODEL, 0.0) > config.WAKE_WORD_THRESHOLD:
                            print("\n[Interrupt] Voice detected! Cutting audio.")
                            pygame.mixer.music.stop()
                            interrupter_model.reset()
                            break
                    except Exception:
                        # Ignore audio buffer overflows that happen while playing audio
                        pass
                        
    except Exception as e:
        print(f"[TTS error] {e}")
    finally:
        if on_end:
            on_end()
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass