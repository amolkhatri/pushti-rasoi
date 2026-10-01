# Original 15 s background track for the reel (synthesised, so no licensing issues).
# Writes assets/music.wav. Usage: python3 music.py
import wave
from pathlib import Path
import numpy as np

SR = 44100
BPM = 120
BEAT = 60 / BPM
LENGTH = 15.0
SCENE_CHANGES = [3.2, 6.9, 10.7, 12.9]  # keep in sync with reel.html --in values
rng = np.random.default_rng(7)
mix = np.zeros(int(SR * LENGTH) + SR)

def hz(m): return 440 * 2 ** ((m - 69) / 12)
def add(sig, t, gain=1.0):
    i = int(t * SR); j = min(len(mix), i + len(sig)); mix[i:j] += gain * sig[: j - i]
def lowpass(x, a):  # one-pole smoother, a in (0,1): smaller = darker
    y = np.empty_like(x); acc = 0.0
    for k, v in enumerate(x): acc += a * (v - acc); y[k] = acc
    return y

def pluck(m, dur=0.9):  # Karplus-Strong string, ukulele-ish
    n = int(SR / hz(m)); buf = rng.uniform(-1, 1, n); out = np.empty(int(dur * SR))
    for k in range(len(out)):
        out[k] = buf[k % n]; buf[k % n] = 0.996 * 0.5 * (buf[k % n] + buf[(k + 1) % n])
    return out * np.exp(-np.linspace(0, 3, len(out)))

def bell(m, dur=1.2):
    t = np.arange(int(dur * SR)) / SR; f = hz(m)
    s = np.sin(2*np.pi*f*t) + .35*np.sin(2*np.pi*2*f*t)*np.exp(-t*6) + .15*np.sin(2*np.pi*3.01*f*t)*np.exp(-t*9)
    return s * np.exp(-t * 3.2) * np.minimum(1, t * 400)

def pad(ms, dur):
    t = np.arange(int(dur * SR)) / SR; s = sum(np.sin(2*np.pi*hz(m)*t) + .5*np.sin(2*np.pi*hz(m)*1.003*t) for m in ms)
    env = np.minimum(1, t / .35) * np.minimum(1, (dur - t) / .4)
    return s * env / len(ms)

def bass(m, dur):
    t = np.arange(int(dur * SR)) / SR
    return (np.sin(2*np.pi*hz(m)*t) + .25*np.sin(4*np.pi*hz(m)*t)) * np.exp(-t * 2.2) * np.minimum(1, t * 300)

def kick():
    t = np.arange(int(.35 * SR)) / SR; f = 50 + 90 * np.exp(-t * 28)
    return np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t * 11)

def shaker(): n = int(.07 * SR); return np.diff(rng.uniform(-1, 1, n + 1)) * np.exp(-np.linspace(0, 6, n))
def snap():
    n = int(.18 * SR); return lowpass(rng.uniform(-1, 1, n), .5) * np.exp(-np.linspace(0, 14, n))

def sparkle(t0, base=84, up=True):  # quick bell run marking a scene change
    notes = [0, 4, 7, 12, 16] if up else [16, 12, 7, 4, 0]
    for i, n in enumerate(notes): add(bell(base + n, .7), t0 + i * .045, .16)

# chord progression in beats: (start, length, root, chord tones)
C, Am, F, G = (48, [60, 64, 67]), (45, [57, 60, 64]), (41, [57, 60, 65]), (43, [55, 59, 62])
prog = [(0,4,*C),(4,4,*Am),(8,4,*F),(12,4,*G),(16,4,*C),(20,4,*Am),(24,1,*F),(25,1,*G),(26,4,*C)]

for b0, nb, root, tones in prog:
    t0 = b0 * BEAT; final = b0 == 26
    add(pad([m + 12 for m in tones], nb * BEAT + (1.2 if final else .3)), t0, .055)
    if final:
        for i, m in enumerate(tones + [tones[0] + 12, tones[1] + 12]): add(pluck(m + 12, 2.0), t0 + i * .06, .32)
        add(bass(root, 2.0), t0, .5); add(kick(), t0, .55)
        continue
    arp = [tones[0], tones[2], tones[1] + 12, tones[2]]  # 8th-note pattern
    for k in range(int(nb * 2)):
        add(pluck(arp[k % 4] + 12, .8), t0 + k * BEAT / 2, .28 if k % 2 == 0 else .2)
    for k in range(0, nb, 2): add(bass(root, BEAT * 2), t0 + k * BEAT, .45)
    if b0 >= 4:  # groove enters after the 2 s intro
        for k in range(nb):
            tb = t0 + k * BEAT
            if k % 2 == 0: add(kick(), tb, .55)
            else: add(snap(), tb, .22)
            add(shaker(), tb + BEAT / 2, .1); add(shaker(), tb, .05)

# bell melody (beat, midi, length)
melody = [(4,76,.5),(4.5,79,.5),(5,81,.5),(5.5,79,.5),(6,76,1),(7,72,1),
          (8,77,.5),(8.5,76,.5),(9,74,.5),(9.5,72,.5),(10,77,1),(11,81,1),
          (12,79,1.5),(13.5,77,.5),(14,74,1),(15,71,1),
          (16,76,.5),(16.5,79,.5),(17,81,.5),(17.5,79,.5),(18,84,1),(19,83,.5),(19.5,81,.5),
          (20,79,.5),(20.5,76,.5),(21,72,1),(22,74,.5),(22.5,76,.5),(23,77,1),
          (24,77,.5),(24.5,76,.5),(25,74,.5),(25.5,71,.5),(26,72,2)]
for b, m, l in melody: add(bell(m, max(.6, l * BEAT + .5)), b * BEAT, .2)

for t in SCENE_CHANGES[:-1]: sparkle(t - .1)
sparkle(SCENE_CHANGES[-1] - .1, 88)

out = mix[: int(SR * LENGTH)]
t = np.arange(len(out)) / SR
out *= np.minimum(1, t / .05) * np.clip((LENGTH - t) / 1.4, 0, 1)  # fade out over the last 1.4 s
out = np.tanh(out * 1.1)  # gentle glue
out *= 0.89 / np.abs(out).max()  # peak ≈ -1 dBFS
stereo = np.stack([out, np.roll(out, 220) * .96 + out * .04], 1)  # tiny width
path = Path(__file__).with_name("assets") / "music.wav"
with wave.open(str(path), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((stereo * 32767).astype("<i2").tobytes())
print("wrote", path)
