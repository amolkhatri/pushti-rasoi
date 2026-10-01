# Lo-fi café track: warm electric piano, swung boom-bap, vinyl crackle. 80 BPM.
# Usage: python3 music_lofi.py [out.wav]   (default assets/music.wav)
import numpy as np
from synth import SR, SCENE_CHANGES, Mix, hz, times, lowpass

rng = np.random.default_rng(11)
BEAT = 60 / 80
SWING = 0.18 * BEAT  # how late the off-beat 8ths land
mix, drums = Mix(), Mix()

def epiano(m, dur=2.4, vel=1.0):  # FM "Rhodes": 1:1 body + bright tine on attack
    t = times(dur); f = hz(m)
    idx = (1.6 * vel) * np.exp(-t * 2.5)
    s = np.sin(2*np.pi*f*t + idx*np.sin(2*np.pi*f*t))
    s += .12 * np.sin(2*np.pi*f*14*t) * np.exp(-t * 40)  # tine "ding"
    s += .08 * np.sin(2*np.pi*f*.5*t)  # warmth
    return s * np.exp(-t * 1.25) * np.minimum(1, t * 200) * vel

def chord(ms, t0, vel=1.0, dur=2.6, spread=.018):
    for i, m in enumerate(ms): mix.add(epiano(m, dur, vel), t0 + i * spread, .16)

def sub(m, dur):
    t = times(dur); return np.sin(2*np.pi*hz(m)*t) * np.exp(-t * 1.4) * np.minimum(1, t * 120)

def kick():
    t = times(.4); f = 45 + 70 * np.exp(-t * 30)
    return np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t * 9)

def snare():
    t = times(.3)
    body = np.sin(2*np.pi*185*t) * np.exp(-t * 25)
    noise = lowpass(rng.uniform(-1, 1, len(t)), .35) * np.exp(-t * 13)
    return .5 * body + noise

def hat(open_=False):
    t = times(.12 if not open_ else .3); n = np.diff(rng.uniform(-1, 1, len(t) + 1))
    return n * np.exp(-t * (55 if not open_ else 14))

# Jazzy loop in C: Fmaj9 · Em7 · Dm9 · G13 · Cmaj9 (one bar each, 3 s per bar)
bars = [  # (bass, voicing)
    (41, [57, 60, 64, 67]),   # Fmaj9  (A C E G)
    (40, [55, 59, 62, 64]),   # Em7    (G B D E)
    (38, [57, 60, 64, 65]),   # Dm9    (A C E F)
    (43, [53, 57, 59, 64]),   # G13    (F A B E)
    (36, [55, 59, 62, 64]),   # Cmaj9  (G B D E)
]
BAR = 4 * BEAT

for b, (root, v) in enumerate(bars):
    t0 = b * BAR
    last = b == len(bars) - 1
    if last: t0 = SCENE_CHANGES[-1] - .05  # land the final chord on the end card
    chord(v, t0, 1.0, 3.6 if last else 2.6)
    mix.add(sub(root, 2.8 if last else 1.6), t0, .55)
    if not last:
        chord(v[1:], t0 + 2.5 * BEAT, .6, 1.2)  # pushed comp on the "and" of 3
        mix.add(sub(root, 1.0), t0 + 2.5 * BEAT, .35)

# sparse high melody (beats from start, midi)
for bt, m, vel in [(4.5, 76, .7), (5, 79, .6), (6.5, 81, .7), (8, 79, .8), (9.5, 76, .6), (10, 74, .7),
                   (12.5, 77, .6), (13, 76, .7), (14.5, 74, .6), (16, 72, .5)]:
    mix.add(epiano(m, 1.6, vel), bt * BEAT, .14)
mix.add(epiano(84, 3.0, .7), SCENE_CHANGES[-1] + .35, .12)  # sparkle over the end card

# swung drums from scene 2 to just before the end card
def swing(b8): return (b8 // 2) * BEAT + (b8 % 2) * (BEAT / 2 + SWING)
start = round(SCENE_CHANGES[0] / BEAT * 2)  # in 8ths
for b8 in range(start, int(SCENE_CHANGES[-1] / BEAT * 2)):
    t = swing(b8); pos = b8 % 8
    if pos in (0, 5): drums.add(kick(), t, .9)
    if pos in (2, 6): drums.add(snare(), t, .42)
    drums.add(hat(pos == 7), t, .09 * (1.0 if b8 % 2 == 0 else .65) * rng.uniform(.8, 1.1))
drums.add(kick(), SCENE_CHANGES[-1] - .05, .9)

# soft "whoosh" (filtered noise swell) into each scene change
for sc in SCENE_CHANGES[:-1]:
    t = times(.5); n = lowpass(rng.uniform(-1, 1, len(t)), .08) * (t / .5) ** 2
    mix.add(n, sc - .45, .25)

# vinyl: low hiss + random crackles
hiss = lowpass(rng.uniform(-1, 1, len(mix.buf)), .05) * .012
crackle = np.zeros(len(mix.buf)); pops = rng.integers(0, len(crackle), 260)
crackle[pops] = rng.uniform(-.25, .25, len(pops))
mix.buf += hiss + lowpass(crackle, .6)

mix.buf += lowpass(drums.buf, .55)  # dusty drums
mix.buf = lowpass(mix.buf, .5)  # tape-warm top end
mix.write("music.wav", fade_out=1.2)
