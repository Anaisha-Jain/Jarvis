"""
jarvis_app.py

Run THIS file to start Jarvis as a background desktop app:
    - Listens continuously for "Hey Jarvis"
    - Shows your HUD image on screen while active/speaking
    - Speaks responses in a British voice
    - Runs all your existing dispatcher tools (stocks, weather, spotify, etc.)
    - No text UI at all, ever
    - Lives in the system tray so you can quit it cleanly

Install (on top of what your project already needs):
    pip install edge-tts pygame pillow pystray

Run silently with no console window:
    pythonw jarvis_app.py

To auto-start on login, see the note at the bottom of this file.
"""

import threading

import pystray
from PIL import Image

from overlay import JarvisOverlay
from voice import JarvisVoiceSession

HUD_IMAGE_PATH = "assets/jarvis_hud.png"  # <-- put your uploaded image here


def _run_voice_loop(overlay: JarvisOverlay):
    session = JarvisVoiceSession(overlay=overlay)
    session.run()


def _build_tray_icon(overlay: JarvisOverlay):
    icon_img = Image.open(HUD_IMAGE_PATH).convert("RGBA")

    def _quit(icon, item):
        icon.stop()
        overlay.root.after(0, overlay.root.destroy)

    menu = pystray.Menu(pystray.MenuItem("Quit Jarvis", _quit))
    icon = pystray.Icon("jarvis", icon_img, "Jarvis", menu)
    return icon


def main():
    overlay = JarvisOverlay(HUD_IMAGE_PATH, size=220)

    # Voice pipeline runs on its own thread so it never blocks the HUD's
    # tkinter mainloop (tkinter must live on the main thread).
    voice_thread = threading.Thread(target=_run_voice_loop, args=(overlay,), daemon=True)
    voice_thread.start()

    # Tray icon also runs on its own thread.
    tray_icon = _build_tray_icon(overlay)
    tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
    tray_thread.start()

    overlay.run()  # blocks here, keeps the app alive


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# Auto-start on login (Windows)
# ---------------------------------------------------------------------------
# 1. Make a shortcut that runs:
#      pythonw.exe "C:\Documents\Anaisha_documents\Extras\Coding\Jarvis\jarvis_os\jarvis_app.py"
#    (pythonw.exe, not python.exe -- this avoids a console window popping up)
#
# 2. Press Win+R, type: shell:startup, hit enter.
#
# 3. Drop the shortcut into that folder. Windows will launch it every time
#    you log in, silently, in the background.
