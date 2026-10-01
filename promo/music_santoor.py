# "Santoor morning": Raag Bhupali (Sa Re Ga Pa Dha) on santoor, tanpura drone, soft tabla keherwa. 92 BPM.
# Usage: python3 music_santoor.py [out.wav]   (default assets/music.wav)
from synth import LENGTH, SCENE_CHANGES, Mix, hz
from indian import fit, ghungroo, membrane, rng, santoor, tanpura

BEAT = 60 / 92
SA = 62  # D4: bright but warm for santoor
mix = Mix()
tanpura(mix, SA - 12, LENGTH, .06)

S, R, G, P, D = SA, SA + 2, SA + 4, SA + 7, SA + 9
S2, R2, G2, P2 = SA + 12, SA + 14, SA + 16, SA + 19
D_ = SA - 3  # lower Dha

def play(notes, t0, gain=.2):
    """notes: (midi, beats, style) where style is '' (single strike), 'roll' (tremolo) or 'run' (quick grace)."""
    t = t0
    for m, b, style in notes:
        dur = b * BEAT
        if style == "roll":  # santoor tremolo: fast repeated strikes, swelling then fading
            k, step = 0, .068
            while k * step < dur - .02:
                v = .55 + .35 * min(1, k / 4) * (1 - k * step / dur)
                mix.add(santoor(m, v, .9), t + k * step, gain * .8); k += 1
        else:
            mix.add(santoor(m, 1.0 if style != "soft" else .7), t, gain)
            if style == "run":  # grace note from above
                mix.add(santoor(m + 2, .6, .4), t - .07, gain * .6)
        t += dur
    return t

# alaap-like opening, free and spacious
play([(D_, .5, ""), (S, .5, ""), (R, .5, ""), (G, 1, "roll"), (P, 1, "run"), (G, 1.5, "roll")], .1)
# gat (composition) once tabla enters, repeated to fill the reel, then a quick taan into the end card
gat = [
    [(G, .5, ""), (P, .5, ""), (D, .5, ""), (S2, .5, ""), (D, .5, ""), (P, .5, ""), (G, 1, "roll"),
     (R, .5, ""), (G, .5, ""), (P, .5, "run"), (G, .5, ""), (R, .5, ""), (S, 1.5, "roll")],
    [(P, .5, ""), (D, .5, ""), (S2, .5, ""), (R2, .5, ""), (G2, 1, "roll"), (R2, .5, ""), (S2, .5, ""),
     (D, .5, ""), (P, .5, ""), (D, .5, "run"), (S2, 1.5, "roll")],
]
taan = [(S, .25, ""), (R, .25, ""), (G, .25, ""), (P, .25, ""), (D, .25, ""), (S2, .25, ""), (R2, .25, ""), (G2, .25, ""),
        (R2, .25, ""), (S2, .25, ""), (D, .25, ""), (P, .25, ""), (G, .5, "roll"), (R, .5, "")]
beats = lambda ph: sum(b for _, b, _ in ph) * BEAT
taan_at = SCENE_CHANGES[-1] - .02 - beats(taan)
t, k = SCENE_CHANGES[0], 0
while t + beats(gat[k % len(gat)]) <= taan_at + .05:
    t = play(gat[k % len(gat)], t); k += 1
short = [(S2, .5, ""), (D, .5, ""), (P, .5, ""), (G, .5, ""), (R, 1, "roll"), (S, 1, "roll")]
if taan_at - t >= beats(short) - .05:  # a short answering phrase fits before the taan
    t = play(short, t)
if taan_at - t > .6:  # fill any gap with a soft roll on Sa
    play([(S2, (taan_at - t) / BEAT, "roll")], t, .16)
play(taan, taan_at)
# land on high Sa as the logo appears, with a long shimmering roll
play([(S2, 3.0, "roll")], SCENE_CHANGES[-1] - .02, .22)
mix.add(santoor(S, 1.0, 2.5), SCENE_CHANGES[-1] - .02, .18)

# soft tabla keherwa (8ths) from scene 2 up to the end card
na = lambda: membrane(hz(SA + 12), .5, decay=10, click=.35)
tin = lambda: membrane(hz(SA + 12), .3, decay=24, click=.3) * .7
ge = lambda: membrane(78, .6, (1,), decay=5, bend=.35, click=.2)
ka = lambda: membrane(300, .06, (1, 2.3), decay=60, click=.6) * .5
bol = {"dha": lambda: fit(na(), ge()), "dhin": lambda: fit(tin(), ge()), "ge": ge, "na": na, "ti": tin, "ka": ka}
theka = ["dha", "ge", "na", "ti", "na", "ka", "dhin", "na"]
t, i = SCENE_CHANGES[0] - .02, 0
while t < SCENE_CHANGES[-1] - .25:
    b = theka[i % 8]
    mix.add(bol[b](), t + rng.uniform(-.004, .004), (.36 if b in ("dha", "dhin") else .22) * rng.uniform(.85, 1.05))
    t += BEAT / 2; i += 1
mix.add(bol["dha"](), SCENE_CHANGES[-1] - .02, .45)  # sam

for sc in SCENE_CHANGES: ghungroo(mix, sc - .12, 16 if sc == SCENE_CHANGES[-1] else 10, .04)
mix.write("music.wav", fade_out=1.5)
