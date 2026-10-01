# "Festive dholak": harmonium tune, dholak chaal, manjira, claps; tihai landing on the end card. 125 BPM.
# Usage: python3 music_festive.py [out.wav]   (default assets/music.wav)
from synth import SCENE_CHANGES, Mix
from indian import clap, fit, ghungroo, harmonium, manjira, membrane, rng, slap

BEAT = 60 / 125
STEP = BEAT / 4  # 16th notes
SAM = SCENE_CHANGES[-1] - .02  # where the tihai must land
SA = 60  # C4
mix = Mix()

S, R, G, M, P, D, N = SA, SA + 2, SA + 4, SA + 5, SA + 7, SA + 9, SA + 11
S2, R2, G2 = SA + 12, SA + 14, SA + 16

# harmonium left hand: Sa–Pa drone pulses
for b in range(0, int(SAM / BEAT), 4):
    mix.add(harmonium(SA - 12, 4 * BEAT - .03, .8) + harmonium(SA - 5, 4 * BEAT - .03, .6), b * BEAT, .38)

def tune(notes, t0, gain=.62):
    t = t0
    for m, b in notes:
        if m: mix.add(harmonium(m, b * BEAT - .025), t, gain)
        t += b * BEAT
    return t

# intro call (free, before the drums)
tune([(P, .5), (D, .5), (S2, 1), (D, .5), (P, .5), (G, 1.5), (None, .5), (R, .5), (G, .5)], .05)
# main folk-style tune: question / answer, repeated with a lift
phrase_a = [(G, .5), (G, .5), (M, .5), (P, 1), (P, .5), (D, .5), (P, .5), (M, .5), (G, .5), (R, .5), (G, 1.5)]
phrase_b = [(P, .5), (D, .5), (S2, .5), (S2, 1), (N, .5), (D, .5), (P, .5), (M, .5), (G, .5), (R, .5), (S, 1.5)]
lift     = [(S2, .5), (S2, .5), (R2, .5), (G2, 1), (R2, .5), (S2, .5), (N, .5), (D, .5), (P, .5), (D, .5), (S2, 1.5)]
phrases = [phrase_a, phrase_b, lift]
t, k = SCENE_CHANGES[0], 0
while t + sum(b for _, b in phrases[k % 3]) * BEAT <= SAM - 10 * STEP + .05:  # stop before the tihai
    t = tune(phrases[k % 3], t); k += 1
# final held Sa over the end card
mix.add(harmonium(S2, 2.4) + harmonium(S, 2.4, .7), SAM, .6)

# dholak
ghe = lambda: membrane(92, .45, (1,), decay=7, bend=.4, click=.25)      # bass head with gamak
na = lambda: membrane(560, .25, (1, 2, 3), decay=16, click=.45)        # ringing treble
ta = lambda: slap()
dha = lambda: fit(ghe(), na())
pattern = {0: "dha", 3: "ghe", 4: "ta", 6: "na", 8: "dha", 10: "ghe", 11: "ghe", 12: "ta", 14: "na", 15: "ta"}
voices = {"dha": (dha, .55), "ghe": (ghe, .5), "na": (na, .3), "ta": (ta, .28)}
tihai_hits = []  # three groups of (ta, ta, dha) with one-step gaps; last dha on SAM
for g in range(3):
    for h in range(3):
        steps_before_sam = (2 - g) * 4 + (2 - h)
        tihai_hits.append((SAM - steps_before_sam * STEP, "dha" if h == 2 else "ta"))
tihai_start = tihai_hits[0][0]
s = int(SCENE_CHANGES[0] / STEP)
while s * STEP < tihai_start - STEP / 2:
    pos = s % 16
    if pos in pattern:
        fn, g = voices[pattern[pos]]; mix.add(fn(), s * STEP + rng.uniform(-.005, .005), g * rng.uniform(.85, 1.05))
    if pos in (4, 12): mix.add(manjira(True), s * STEP, .13)           # "ching" on 2 and 4
    elif pos % 2 == 0: mix.add(manjira(False), s * STEP, .08)          # "chak" on 8ths
    if pos in (4, 12) and s * STEP > SCENE_CHANGES[1]: mix.add(clap(), s * STEP, .3)
    s += 1
for tt, b in tihai_hits:
    fn, g = voices[b]; mix.add(fn(), tt, g * (1.25 if tt == tihai_hits[-1][0] else 1))
mix.add(manjira(True), SAM, .3)
ghungroo(mix, SAM - .1, 20, .05)
for sc in SCENE_CHANGES[:-1]: ghungroo(mix, sc - .12, 10, .035)

mix.write("music.wav", fade_out=1.4)
