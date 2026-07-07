"""
spotify_control.py
 
Controls Spotify's desktop app using OS-level media key simulation only.
No Spotify API, no developer app, no credentials, no premium required.
 
This works because Spotify's desktop client listens for the same global
media-key signals your keyboard's play/pause/skip buttons send — same
mechanism as any other media player.
 
Install:
    pip install pycaw comtypes
"""
 
import ctypes
import os
import time
 
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
 
KEYEVENTF_KEYUP = 0x0002
 
 
def _send_media_key(vk_code: int):
    """Simulate a hardware media-key press+release (Windows only)."""
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
 
 
def _is_spotify_running() -> bool:
    try:
        from pycaw.pycaw import AudioUtilities
        for session in AudioUtilities.GetAllSessions():
            if session.Process and session.Process.name().lower() == "spotify.exe":
                return True
    except Exception:
        pass
    return False
 
 
def _ensure_spotify_running():
    """Launch Spotify if it isn't already running, so media keys have a target."""
    if not _is_spotify_running():
        try:
            os.startfile("spotify:")
            time.sleep(3)
        except OSError:
            pass
 
 
def play_pause() -> str:
    _ensure_spotify_running()
    _send_media_key(VK_MEDIA_PLAY_PAUSE)
    return "Toggled playback, Sir."
 
 
def next_track() -> str:
    _ensure_spotify_running()
    _send_media_key(VK_MEDIA_NEXT_TRACK)
    return "Skipping to the next track, Sir."
 
 
def previous_track() -> str:
    _ensure_spotify_running()
    _send_media_key(VK_MEDIA_PREV_TRACK)
    return "Going back a track, Sir."
 
 
def system_volume_up(steps: int = 2) -> str:
    for _ in range(steps):
        _send_media_key(VK_VOLUME_UP)
        time.sleep(0.03)
    return "Volume increased, Sir."
 
 
def system_volume_down(steps: int = 2) -> str:
    for _ in range(steps):
        _send_media_key(VK_VOLUME_DOWN)
        time.sleep(0.03)
    return "Volume decreased, Sir."
 
 
def set_spotify_app_volume(level: float) -> str:
    """
    App-specific volume (only affects Spotify, not your whole system).
    level is 0.0 (silent) to 1.0 (full).
    """
    try:
        from pycaw.pycaw import AudioUtilities
    except ImportError:
        return "pycaw isn't installed, Sir. Run: pip install pycaw comtypes"
 
    level = max(0.0, min(1.0, level))
    found = False
    for session in AudioUtilities.GetAllSessions():
        if session.Process and session.Process.name().lower() == "spotify.exe":
            session.SimpleAudioVolume.SetMasterVolume(level, None)
            found = True
 
    if not found:
        return "Spotify doesn't appear to be running, Sir."
    return f"Spotify volume set to {int(level * 100)} percent, Sir."