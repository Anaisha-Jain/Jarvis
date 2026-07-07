"""
overlay.py

A borderless, always-on-top HUD window that shows your Jarvis image.
Hidden by default; call .show() when the wake word fires and .hide() once
Jarvis finishes responding.

Must be created and run on the MAIN thread (tkinter requirement) -- see
jarvis_app.py for how this is wired up alongside the voice loop, which runs
on a background thread instead.

Install:
    pip install pillow
"""

import queue
import tkinter as tk

from PIL import Image, ImageTk


class JarvisOverlay:
    def __init__(self, image_path: str, size: int = 220, margin: int = 40):
        self.q = queue.Queue()

        self.root = tk.Tk()
        self.root.overrideredirect(True)          # no title bar/borders
        self.root.attributes("-topmost", True)     # always on top
        self.root.attributes("-transparentcolor", "black")  # black = invisible
        self.root.configure(bg="black")

        img = Image.open(image_path).convert("RGBA").resize((size, size))
        self.photo = ImageTk.PhotoImage(img)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - size - margin
        y = screen_h - size - margin - 60  # a bit above the taskbar
        self.root.geometry(f"{size}x{size}+{x}+{y}")

        self.label = tk.Label(self.root, image=self.photo, bg="black", bd=0)
        self.label.pack()

        self.root.withdraw()  # start hidden
        self.root.after(100, self._poll)

    def _poll(self):
        try:
            while True:
                cmd = self.q.get_nowait()
                if cmd == "show":
                    self.root.deiconify()
                    self.root.lift()
                elif cmd == "hide":
                    self.root.withdraw()
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def show(self):
        self.q.put("show")

    def hide(self):
        self.q.put("hide")

    def run(self):
        """Blocks -- call this from your main thread."""
        self.root.mainloop()
