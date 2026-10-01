# Small shared helpers for the reel's synthesised music tracks.
import json
import os
import sys
import wave
from pathlib import Path
import numpy as np

SR = 44100
LENGTH = 15.0
SCENE_CHANGES = [3.2, 6.9, 10.7, 12.9]  # keep in sync with reel.html --in values
# TIMELINE=timeline-site.json switches to another reel's length and scene starts (last one = end card).
if os.environ.get("TIMELINE"):
    _tl = json.loads(Path(os.environ["TIMELINE"]).read_text())
    LENGTH, SCENE_CHANGES = float(_tl["length"]), [float(s) for s in _tl["scenes"]]


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def times(dur):
    return np.arange(int(dur * SR)) / SR


def lowpass(x, a):
    """One-pole low-pass; a in (0, 1], smaller is darker."""
    y = np.empty_like(x); acc = 0.0
    for k, v in enumerate(x):
        acc += a * (v - acc); y[k] = acc
    return y


class Mix:
    def __init__(self, length=LENGTH):
        self.buf = np.zeros(int(SR * length) + 2 * SR)
        self.length = length

    def add(self, sig, t, gain=1.0):
        i = int(round(t * SR))
        if i < 0: sig, i = sig[-i:], 0
        j = min(len(self.buf), i + len(sig))
        self.buf[i:j] += gain * sig[: j - i]

    def write(self, default_name, fade_out=1.5, width=220):
        out = self.buf[: int(SR * self.length)].copy()
        t = np.arange(len(out)) / SR
        out *= np.minimum(1, t / .03) * np.clip((self.length - t) / fade_out, 0, 1)
        out = np.tanh(out * 1.1)
        out *= 0.89 / np.abs(out).max()
        stereo = np.stack([out, np.roll(out, width) * .96 + out * .04], 1)
        path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("assets") / default_name
        with wave.open(str(path), "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((stereo * 32767).astype("<i2").tobytes())
        print("wrote", path)
