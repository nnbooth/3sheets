#!/usr/bin/env python3
"""
record_demo.py — record "The Month-End Run" demo into shareable media.

WHAT IT MAKES (in media/)
    month-end-run-15s.mp4    ~15 s cut for LinkedIn
    month-end-run-15s.gif    same cut as a GIF fallback (kept under 5 MB)
    month-end-run-full.mp4   the whole ~28 s story, for the site / email
    poster.png               a still of the title screen (site poster)

HOW IT WORKS
    1. Serves this repo on a local web address (like `python3 -m http.server`).
    2. Opens game/index.html?demo=1&capture=1 in Chrome via Playwright. In
       that mode the game plays itself (scripted inputs, seeded randomness),
       but only moves forward when this script says so.
    3. Steps the game 2 ticks at a time (the game runs at 60 ticks a second,
       so 2 ticks = one frame of 30 fps video) and saves each frame exactly
       as drawn: 1280x720, no screen recording blur, identical every run.
    4. The game notes when each story beat starts (window.__game.marks), so
       the 15-second cut is assembled from those timestamps (see CUT_15S).
    5. Every frame's text is checked by the game's own audit (off screen,
       overlapping, or half-hidden text) and any problems are listed.
    6. ffmpeg turns the frames into MP4s and a GIF.

SETUP (once)
    pip install playwright
    playwright install chromium     # only needed if Google Chrome isn't installed
    ffmpeg must be installed (macOS: brew install ffmpeg)

RUN (from the repo root)
    python3 tools/record_demo.py

Change the story or numbers in game/game.js (CONFIG), then run this again.
"""

import base64
import functools
import http.server
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
MEDIA = REPO / "media"

FPS = 30                 # video frame rate
TICKS_PER_FRAME = 60 // FPS
END_HOLD_S = 4.5         # how long the end card stays on screen in the full cut
MAX_SECONDS = 60         # safety stop if the demo never reaches the end card
GIF_LIMIT_MB = 5.0

# The 15-second cut: (story beat, seconds from the start of that beat, length in seconds).
# Beat names are the ones the game records in window.__game.marks.
CUT_15S = [
    ("open",    0.0, 1.5),   # the opening line, short
    ("before2", 0.0, 2.5),   # one "by hand" beat: Payroll & overtime, clocks multiplying
    ("switch",  0.0, 2.6),   # "Built by a CPA. Runs itself." and the sheet tidying
    ("summary", 0.0, 4.5),   # the month-end report card
    ("end",     0.0, 3.5),   # the call to action (stays for the last 3.5 s)
]
POSTER_AT = ("open", 2.0)    # which frame becomes poster.png


def serve_repo():
    """Serve the repo on a free local port in the background. Returns the base URL."""
    handler = functools.partial(QuietHandler, directory=str(REPO))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{httpd.server_address[1]}", httpd


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep the console tidy
        pass


def launch(p):
    """Use the installed Google Chrome if there is one, else Playwright's own Chromium."""
    try:
        return p.chromium.launch(channel="chrome")
    except Exception:
        return p.chromium.launch()


def capture_frames(base_url, frames_dir):
    """Step the demo to the end card (+ END_HOLD_S) and save every frame. Returns marks in frames."""
    with sync_playwright() as p:
        browser = launch(p)
        page = browser.new_page(viewport={"width": 1400, "height": 900}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        page.goto(f"{base_url}/game/index.html?demo=1&capture=1", wait_until="networkidle")
        page.wait_for_function("window.__game !== undefined")
        page.evaluate("window.__game.ready")

        grab = "document.getElementById('game-canvas').toDataURL('image/png')"
        frame, end_frame = 0, None
        text_issues = {}  # frame number -> problems found by the game's text audit
        while frame < MAX_SECONDS * FPS:
            state = page.evaluate(f"window.__game.step({TICKS_PER_FRAME})")
            data = page.evaluate(grab)
            (frames_dir / f"{frame:05d}.png").write_bytes(base64.b64decode(data.split(",", 1)[1]))
            issues = page.evaluate("window.__game.audit()")
            if issues:
                text_issues[frame] = issues
            frame += 1
            if state == "end" and end_frame is None:
                end_frame = frame
            if end_frame is not None and frame - end_frame >= END_HOLD_S * FPS:
                break
            if frame % FPS == 0:
                print(f"  {frame // FPS:>3}s  {state}", flush=True)

        marks = page.evaluate("({...window.__game.marks})")
        browser.close()

    if errors:
        print("Browser errors during capture:", *errors, sep="\n  ")
    if text_issues:
        print(f"TEXT PROBLEMS in {len(text_issues)} frames (first 20 shown):")
        for f, issues in list(text_issues.items())[:20]:
            print(f"  {f / FPS:6.2f}s  " + "; ".join(issues))
    else:
        print("Text audit: no clipped, overlapping or half-hidden text in any frame.")
    if end_frame is None:
        sys.exit("The demo never reached the end card. Check game.js.")
    # marks are in game ticks; convert to video frames
    return {name: tick // TICKS_PER_FRAME for name, tick in marks.items()}, frame


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def encode_mp4(frames_dir, out):
    """Frames -> H.264 MP4 that plays everywhere (LinkedIn, browsers, email clients)."""
    ffmpeg(
        "-framerate", str(FPS), "-i", str(frames_dir / "%05d.png"),
        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-tune", "animation",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out),
    )


def build_cut(frames_dir, marks, cut, cut_dir):
    """Copy the frames for each (beat, offset, length) into cut_dir, numbered in order."""
    n = 0
    for beat, offset, length in cut:
        start = marks[beat] + round(offset * FPS)
        for i in range(start, start + round(length * FPS)):
            src = frames_dir / f"{i:05d}.png"
            if src.exists():
                shutil.copyfile(src, cut_dir / f"{n:05d}.png")
                n += 1
    return n


def encode_gif(frames_dir, out):
    """GIF at 512x288 (exactly 2x the game's pixels, so it stays crisp). Shrinks if over the limit."""
    for width, fps in [(512, 15), (512, 12), (384, 12), (256, 10)]:
        height = width * 9 // 16
        palette = frames_dir.parent / "palette.png"
        scale = f"fps={fps},scale={width}:{height}:flags=neighbor"
        ffmpeg("-framerate", str(FPS), "-i", str(frames_dir / "%05d.png"),
               "-vf", f"{scale},palettegen=max_colors=48:stats_mode=diff", str(palette))
        ffmpeg("-framerate", str(FPS), "-i", str(frames_dir / "%05d.png"), "-i", str(palette),
               "-lavfi", f"{scale}[x];[x][1:v]paletteuse=dither=none:diff_mode=rectangle",
               "-loop", "0", str(out))
        size_mb = out.stat().st_size / 1_000_000
        if size_mb < GIF_LIMIT_MB:
            return width, fps, size_mb
    sys.exit(f"GIF is still {size_mb:.1f} MB; shorten CUT_15S.")


def main():
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg isn't installed (macOS: brew install ffmpeg).")
    MEDIA.mkdir(exist_ok=True)
    base_url, httpd = serve_repo()

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        frames = tmp / "frames"
        frames.mkdir()
        print("Capturing the demo frame by frame...")
        marks, total = capture_frames(base_url, frames)
        httpd.shutdown()
        print(f"Captured {total} frames ({total / FPS:.1f} s). Story beats (s):",
              ", ".join(f"{k} {v / FPS:.1f}" for k, v in sorted(marks.items(), key=lambda kv: kv[1])))

        full = MEDIA / "month-end-run-full.mp4"
        encode_mp4(frames, full)

        cut_dir = tmp / "cut15"
        cut_dir.mkdir()
        n = build_cut(frames, marks, CUT_15S, cut_dir)
        short = MEDIA / "month-end-run-15s.mp4"
        encode_mp4(cut_dir, short)

        gif = MEDIA / "month-end-run-15s.gif"
        gw, gfps, gmb = encode_gif(cut_dir, gif)

        beat, offset = POSTER_AT
        shutil.copyfile(frames / f"{marks[beat] + round(offset * FPS):05d}.png", MEDIA / "poster.png")

    print("\nDone:")
    print(f"  {full.relative_to(REPO)}   {total / FPS:.1f} s")
    print(f"  {short.relative_to(REPO)}    {n / FPS:.1f} s")
    print(f"  {gif.relative_to(REPO)}    {gw}px, {gfps} fps, {gmb:.2f} MB")
    print("  media/poster.png")


if __name__ == "__main__":
    main()
