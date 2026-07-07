"""
tts_voice.py

Text-to-speech using Microsoft Edge's neural voices (free, no API key).
Picks a British voice so Jarvis actually sounds British instead of the
default robotic pyttsx3/SAPI5 voice.

Install:
    pip install edge-tts pygame

Swap VOICE below to try different accents/genders:
    en-GB-RyanNeural    - male, British (closest to film-JARVIS, default)
    en-GB-ThomasNeural   - male, British, slightly younger
    en-GB-SoniaNeural    - female, British
"""

import asyncio
import os
import tempfile
import uuid

import edge_tts
import pygame

VOICE = "en-GB-RyanNeural"

pygame.mixer.init()


async def _generate_speech(text: str, path: str):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(path)


def speak(text: str, on_start=None, on_end=None):
    """
    Synthesize and play `text` in Jarvis's British voice.
    on_start/on_end are optional callbacks (used to show/hide the HUD overlay
    exactly while Jarvis is talking).
    """
    if not text:
        return

    if on_start:
        on_start()

    # Unique filename per call -- pygame keeps a file handle open on the
    # previously loaded track even after playback ends, so reusing one
    # fixed filename causes "Permission denied" on the next write.
    tmp_path = os.path.join(tempfile.gettempdir(), f"jarvis_speech_{uuid.uuid4().hex}.mp3")

    try:
        asyncio.run(_generate_speech(text, tmp_path))
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
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