# Desi track: tanpura drone, bansuri-style flute with meend (glides), tabla keherwa. 100 BPM, Sa = C.
# Usage: python3 music_desi.py [out.wav]   (default assets/music.wav)
import numpy as np
from synth import SR, LENGTH, SCENE_CHANGES, Mix, hz, times, lowpass

rng = np.random.default_rng(5)
BEAT = 60 / 100
mix = Mix()
SA = 60  # C4

# --- tanpura: Pa Sa' Sa' Sa cycle with buzzy, evolving overtones (jawari)
def tanpura_pluck(m, dur=3.2):
    t = times(dur); f = hz(m); s = np.zeros_like(t)
    for n in range(1, 16):
        bloom = np.exp(-((t - .25 * n**.5) ** 2) / .25)  # overtones swell one after another
        s += (1 / n) * (0.4 + bloom) * np.sin(2*np.pi*f*n*t + rng.uniform(0, 6))
    return s * np.exp(-t * .9) * np.minimum(1, t * 60)
cycle = [SA - 5, SA, SA, SA - 12]
t = 0.0; k = 0
while t < LENGTH:
    mix.add(tanpura_pluck(cycle[k % 4]), t, .05); t += 1.05; k += 1

# --- flute: one continuous voice with glides between notes, breath noise and delayed vibrato
def flute_phrase(notes, t0, gain=.22):
    """notes: list of (midi, beats). Glides 70 ms into each new note."""
    total = sum(b for _, b in notes) * BEAT + .35
    t = times(total); f = np.zeros_like(t); pos = 0; prev = None; amp = np.zeros_like(t)
    for m, b in notes:
        i0 = int(pos * SR); i1 = int((pos + b * BEAT) * SR); seg = np.arange(i1 - i0) / SR
        target = hz(m); start = target if prev is None else prev
        f[i0:i1] = target + (start - target) * np.exp(-seg / .045)
        a = np.minimum(1, seg / .05) * (1 - .25 * np.minimum(1, seg / (b * BEAT)))  # tongue + slight decay
        amp[i0:i1] = a; prev = target; pos += b * BEAT
    f[int(pos * SR):] = prev; amp[int(pos * SR):] = np.linspace(amp[int(pos * SR) - 1], 0, len(t) - int(pos * SR))
    vib = 1 + .006 * np.sin(2*np.pi*5.3*t) * np.minimum(1, t / .6)
    ph = 2*np.pi*np.cumsum(f * vib) / SR
    tone = np.sin(ph) + .18*np.sin(2*ph) + .06*np.sin(3*ph)
    breath = lowpass(rng.uniform(-1, 1, len(t)), .3) * .12
    sig = (tone + breath) * amp
    mix.add(sig, t0, gain)
    # small room echo
    mix.add(sig, t0 + .19, gain * .22)

S, R, G, P, D = SA, SA + 2, SA + 4, SA + 7, SA + 9  # Sa Re Ga Pa Dha (bright, Bilawal/Deshkar-ish)
S2, R2, G2 = SA + 12, SA + 14, SA + 16
flute_phrase([(G, 1), (P, .5), (D, .5), (S2, 1.5)], .25)                         # intro alaap
flute_phrase([(D, .5), (S2, .5), (R2, .5), (G2, 1), (R2, .5), (S2, 1), (D, 1)], 3.6)  # with tabla
flute_phrase([(P, .5), (D, .5), (S2, .5), (D, .5), (P, 1), (G, .5), (R, .5), (G, 1.5)], 7.2)
flute_phrase([(G, .5), (P, .5), (D, .5), (S2, .5), (R2, .5), (G2, 1.5)], 10.6)
flute_phrase([(R2, .5), (S2, 3.5)], SCENE_CHANGES[-1] - .3, .24)               # resolve on Sa at the end card

# --- tabla
def membrane(f0, dur, partials=(1, 2, 3, 4), decay=9, bend=0.0):
    t = times(dur); f = f0 * (1 + bend * (1 - np.exp(-t * 12)))
    ph = 2*np.pi*np.cumsum(f) / SR
    s = sum(np.sin(p * ph) / (i + 1) ** 1.2 for i, p in enumerate(partials))
    click = lowpass(rng.uniform(-1, 1, len(t)), .7) * np.exp(-t * 300)
    return (s * np.exp(-t * decay) + .5 * click) * np.minimum(1, t * 2000)
na = lambda: membrane(hz(SA + 12), .5, decay=9)
tin = lambda: membrane(hz(SA + 12), .3, decay=22) * .7
ge = lambda: membrane(80, .6, (1,), decay=5, bend=.35)
ka = lambda: lowpass(rng.uniform(-1, 1, int(.06 * SR)), .5) * np.exp(-np.linspace(0, 8, int(.06 * SR)))
def both(a, b):
    out = np.zeros(max(len(a), len(b))); out[:len(a)] += a; out[:len(b)] += b; return out
bols = {"dha": lambda: both(na(), ge()), "dhin": lambda: both(tin(), ge()), "ge": ge, "na": na, "ti": tin, "ka": ka, "tin": tin}
keherwa = ["dha", "ge", "na", "ti", "na", "ka", "dhin", "na"]  # 8 matras, one per beat... played as 8ths
t = SCENE_CHANGES[0] - .02; i = 0; step = BEAT / 2
while t < SCENE_CHANGES[-1] - .2:
    bol = keherwa[i % 8]
    g = .5 if bol in ("dha", "dhin") else .32
    mix.add(bols[bol](), t + rng.uniform(-.004, .004), g * rng.uniform(.85, 1.05))
    t += step; i += 1
mix.add(bols["dha"](), SCENE_CHANGES[-1] - .05, .6)  # sam on the end card

# --- ghungroo (ankle-bell) shimmer on scene changes
def ghungroo(t0, n=14):
    for j in range(n):
        tt = times(.25); f = rng.uniform(5200, 7400)
        mix.add(np.sin(2*np.pi*f*tt) * np.exp(-tt * 30), t0 + j * rng.uniform(.012, .03), .05)
for sc in SCENE_CHANGES: ghungroo(sc - .12, 18 if sc == SCENE_CHANGES[-1] else 12)

mix.write("music.wav", fade_out=1.4)
