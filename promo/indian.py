# Indian instrument voices for the reel's music (all additive / noise synthesis, no samples).
import numpy as np
from synth import SR, hz, times, lowpass

rng = np.random.default_rng(21)


def fit(*sigs):
    """Sum signals of different lengths."""
    out = np.zeros(max(len(s) for s in sigs))
    for s in sigs: out[: len(s)] += s
    return out


def tanpura_pluck(m, dur=3.2):
    """Drone string with jawari: overtones bloom one after another."""
    t = times(dur); f = hz(m); s = np.zeros_like(t)
    for n in range(1, 16):
        bloom = np.exp(-((t - .25 * n ** .5) ** 2) / .25)
        s += (1 / n) * (.4 + bloom) * np.sin(2 * np.pi * f * n * t + rng.uniform(0, 6))
    return s * np.exp(-t * .9) * np.minimum(1, t * 60)


def tanpura(mix, sa, length, gain=.05, gap=1.05):
    t, k = 0.0, 0
    while t < length:
        mix.add(tanpura_pluck([sa - 5, sa, sa, sa - 12][k % 4]), t, gain); t += gap; k += 1


def santoor(m, vel=1.0, dur=1.8):
    """Hammered metal strings: bright decaying partials, two detuned courses that shimmer."""
    t = times(dur); f = hz(m); s = np.zeros_like(t)
    for n in range(1, 11):
        a = vel ** (n * .25) / n ** 1.1  # softer strikes are less bright
        decay = 2.2 + n * 1.3
        for cents in (-3, 3):
            s += a * np.sin(2 * np.pi * f * n * (1 + .0004 * n) * 2 ** (cents / 1200) * t) * np.exp(-t * decay)
    hammer = lowpass(rng.uniform(-1, 1, len(t)), .9) * np.exp(-t * 400) * .4
    return (s + hammer) * np.minimum(1, t * 3000) * vel


def harmonium(m, dur, vel=1.0):
    """Reed organ: rich odd+even harmonics, two slightly beating reeds, bellows wobble."""
    t = times(dur); f = hz(m); s = np.zeros_like(t)
    for n in range(1, 13):
        a = 1 / n ** .8 * (1.25 if n in (2, 3) else 1)
        s += a * (np.sin(2 * np.pi * f * n * t) + .7 * np.sin(2 * np.pi * f * 1.0025 * n * t + 1.3))
    env = np.minimum(1, t / .03) * np.minimum(1, (dur - t) / .05).clip(0)
    return s * env * (1 + .05 * np.sin(2 * np.pi * 4.5 * t)) * vel / 6


def membrane(f0, dur, partials=(1, 2, 3, 4), decay=9, bend=0.0, click=.5):
    """Tabla / dholak head: harmonic (tuned) partials, optional pitch bend (gamak), strike click."""
    t = times(dur); f = f0 * (1 + bend * (1 - np.exp(-t * 12)))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum(np.sin(p * ph) / (i + 1) ** 1.2 for i, p in enumerate(partials))
    c = lowpass(rng.uniform(-1, 1, len(t)), .7) * np.exp(-t * 300)
    return (s * np.exp(-t * decay) + click * c) * np.minimum(1, t * 2000)


def slap(dur=.12, color=.6):
    """Open-hand slap / 'ta' on dholak treble head."""
    t = times(dur)
    return (lowpass(rng.uniform(-1, 1, len(t)), color) * np.exp(-t * 45)
            + .6 * np.sin(2 * np.pi * 620 * t) * np.exp(-t * 35))


def manjira(open_=True):
    """Small hand cymbals: inharmonic high partials; open 'ching' rings, closed 'chak' is short."""
    t = times(1.2 if open_ else .08); s = np.zeros_like(t)
    for f in (3150, 4280, 5370, 6930, 8120):
        s += np.sin(2 * np.pi * f * rng.uniform(.99, 1.01) * t) * rng.uniform(.5, 1)
    return s * np.exp(-t * (3.5 if open_ else 60)) * np.minimum(1, t * 4000) / 4


def clap():
    t = times(.15); s = np.zeros_like(t)
    for d in (0, .008, .017):  # a few hands, slightly apart
        i = int(d * SR); s[i:] += lowpass(rng.uniform(-1, 1, len(t) - i), .55) * np.exp(-t[: len(t) - i] * 40)
    return s


def ghungroo(mix, t0, n=14, gain=.05):
    for j in range(n):
        tt = times(.25)
        mix.add(np.sin(2 * np.pi * rng.uniform(5200, 7400) * tt) * np.exp(-tt * 30), t0 + j * rng.uniform(.012, .03), gain)
