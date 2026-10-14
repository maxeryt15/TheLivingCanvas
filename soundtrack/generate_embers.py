"""'Embers and Lamplight' - Ballade in Ab for piano and violin (6/8), written in the spirit of Chopin's
impromptus/ballades and Liszt.  One note model -> Standard MIDI File + MusicXML 4.0.
Run:  python generate_embers.py
"""
import random
import re
import struct
from pathlib import Path

from lxml import etree

OUT = Path(__file__).parent
BASE = "embers_and_lamplight"
TITLE = "Embers and Lamplight"
SUBTITLE = "Ballade in A♭ for piano and violin"
COMPOSER = "Claude (original composition)"
PPQ = 480
DIV = 8                      # MusicXML divisions per quarter  -> 1 division = 60 ticks
TICK = PPQ // DIV
DU = 2                       # divisions per sixteenth ("u")
BAR = 24                     # 6/8 bar = 24 divisions = 12 u
BARQ = 3                     # quarter notes per bar
NBARS = 80
KEY_FIFTHS = -4              # Ab major
KEY_FLATS = {"B", "E", "A", "D"}
STEP_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


# ================================================================ pitch / chord helpers
def P(name):
    step, acc, octv = re.fullmatch(r"([A-G])(b|#)?(-?\d)", name).groups()
    alter = {None: 0, "b": -1, "#": 1}[acc]
    return dict(step=step, alter=alter, octave=int(octv),
                midi=12 * (int(octv) + 1) + STEP_PC[step] + alter)


def placements(tone, lo, hi):
    return [f"{tone}{o}" for o in range(0, 9) if lo <= P(f"{tone}{o}")["midi"] <= hi]


CHORDS = {   # name: (label, tones root-first, bass tone or None)
    "Ab":      ("A♭", ["Ab", "C", "Eb"], None),
    "Abadd9":  ("A♭add9", ["Ab", "C", "Eb", "Bb"], None),
    "Ab/Eb":   ("A♭/E♭", ["Ab", "C", "Eb"], "Eb"),
    "Fm":      ("Fm", ["F", "Ab", "C"], None),
    "Fm7":     ("Fm7", ["F", "Ab", "C", "Eb"], None),
    "Db":      ("D♭", ["Db", "F", "Ab"], None),
    "Dbmaj7":  ("D♭maj7", ["Db", "F", "Ab", "C"], None),
    "Dbm":     ("D♭m", ["Db", "Fb", "Ab"], None),
    "Dbm6":    ("D♭m6", ["Db", "Fb", "Ab", "Bb"], None),
    "Bbm":     ("B♭m", ["Bb", "Db", "F"], None),
    "Bbm7":    ("B♭m7", ["Bb", "Db", "F", "Ab"], None),
    "Eb":      ("E♭", ["Eb", "G", "Bb"], None),
    "Eb7":     ("E♭7", ["Eb", "G", "Bb", "Db"], None),
    "Eb7sus":  ("E♭7sus4", ["Eb", "Ab", "Bb", "Db"], None),
    "Cm7":     ("Cm7", ["C", "Eb", "G", "Bb"], None),
    "C7":      ("C7", ["C", "E", "G", "Bb"], None),
    "F7":      ("F7", ["F", "A", "C", "Eb"], None),
    "Ddim7":   ("D°7", ["D", "F", "Ab", "Cb"], None),
    "Bdim7":   ("B°7", ["B", "D", "F", "Ab"], None),
}


def pool(ch, lo, hi):
    tones = CHORDS[ch][1]
    ps = [p for t in tones for p in placements(t, lo, hi)]
    return sorted(ps, key=lambda p: P(p)["midi"])


def bass_note(ch):
    t = CHORDS[ch][2] or CHORDS[ch][1][0]
    return placements(t, 34, 47)[0]


def fifth_low(ch):
    return placements(CHORDS[ch][1][2], 34, 47)[0]


def mid(ch, n=3):
    for lo, hi in ((52, 66), (50, 68), (48, 70)):
        p = pool(ch, lo, hi)
        if len(p) >= n:
            return p[:n]
    raise ValueError(ch)


def ladder(ch, lo, n):
    return pool(ch, lo, lo + 70)[:n]


def updown(n):
    return list(range(n)) + list(range(n - 2, 0, -1))


# ================================================================ harmony per bar  (chord, start u)
def seq(bars_from, items):
    return {bars_from + i: ([(c[0], 0)] if len(c) == 1 else [(c[0], 0), (c[1], 6)]) for i, c in enumerate(items)}


A_HARM = [("Ab",), ("Fm7",), ("Db",), ("Eb7",), ("Ab",), ("C7",), ("Fm",), ("Bbm7", "Eb7"),
          ("Db",), ("Dbm",), ("Ab/Eb", "Eb7"), ("Ab",)]
HARM = {}
HARM.update(seq(1, [("Abadd9",), ("Fm7",), ("Dbmaj7",), ("Eb7sus", "Eb7")]))
HARM.update(seq(5, A_HARM))
HARM.update(seq(17, A_HARM))
HARM.update(seq(29, [("Fm",), ("Fm",), ("C7",), ("Fm",), ("Db",), ("Bbm7",), ("Eb7",), ("Ab",),
                     ("Bbm",), ("Bbm",), ("F7",), ("Bbm",), ("Eb7",), ("Cm7", "F7"), ("Bbm7", "Eb7"), ("Eb7",)]))
HARM.update(seq(45, [("Ab",), ("Fm7",), ("Db",), ("Ddim7",), ("Eb7",), ("Ab",), ("Bdim7",), ("Cm7",),
                     ("Fm7",), ("Bbm7",), ("Db",), ("Dbm6",), ("Ab/Eb",), ("Eb7sus", "Eb7"), ("Eb7",), ("Eb7",)]))
HARM.update(seq(61, A_HARM))
HARM.update(seq(73, [("Abadd9",), ("Fm7",), ("Dbmaj7",), ("Dbm6",), ("Ab/Eb", "Eb7"), ("Ab",), ("Abadd9",), ("Abadd9",)]))

# ================================================================ melodies: (pitch, dur in u)
A_MEL = [
    [("C5", 6), ("Eb5", 4), ("Ab5", 2)],
    [("Ab5", 6), ("G5", 4), ("F5", 2)],
    [("F5", 6), ("Ab5", 4), ("Db6", 2)],
    [("Db6", 6), ("C6", 4), ("Bb5", 2)],
    [("Ab5", 6), ("C6", 4), ("Eb6", 2)],
    [("G6", 6), ("E6", 4), ("C6", 2)],
    [("C6", 6), ("Ab5", 4), ("F5", 2)],
    [("Db6", 4), ("F5", 2), ("G5", 4), ("Bb5", 2)],
    [("F6", 6), ("Db6", 4), ("Ab5", 2)],
    [("Ab5", 6), ("Fb5", 4), ("Db5", 2)],
    [("C6", 4), ("Eb6", 2), ("Db6", 4), ("Bb5", 2)],
    [("Ab5", 12)],
]
B_MEL = [
    [("C5", 2), ("F5", 2), ("Ab5", 2), ("C6", 2), ("Ab5", 2), ("F5", 2)],
    [("C6", 3), ("Bb5", 1), ("Ab5", 2), ("F5", 2), ("C5", 4)],
    [("G5", 2), ("E5", 2), ("G5", 2), ("Bb5", 2), ("G5", 2), ("E5", 2)],
    [("Ab5", 3), ("G5", 1), ("F5", 2), ("C5", 6)],
    [("F5", 2), ("Ab5", 2), ("Db6", 2), ("Ab5", 2), ("F5", 2), ("Db5", 2)],
    [("Db6", 3), ("C6", 1), ("Bb5", 2), ("Ab5", 2), ("F5", 4)],
    [("G5", 2), ("Bb5", 2), ("Db6", 2), ("Bb5", 2), ("G5", 2), ("Eb5", 2)],
    [("Eb6", 3), ("C6", 1), ("Ab5", 8)],
    [("F5", 2), ("Bb5", 2), ("Db6", 2), ("F6", 2), ("Db6", 2), ("Bb5", 2)],
    [("F6", 3), ("Eb6", 1), ("Db6", 2), ("C6", 2), ("Bb5", 4)],
    [("A5", 2), ("C6", 2), ("Eb6", 2), ("C6", 2), ("A5", 2), ("F5", 2)],
    [("Bb5", 3), ("Ab5", 1), ("F5", 2), ("Db5", 2), ("Bb4", 4)],
    [("G5", 2), ("Bb5", 2), ("Db6", 2), ("G6", 2), ("Eb6", 2), ("Bb5", 2)],
    [("G5", 2), ("Bb5", 2), ("Eb6", 2), ("A5", 2), ("C6", 2), ("Eb6", 2)],
    [("Db6", 2), ("F6", 2), ("Ab6", 2), ("Bb5", 2), ("Db6", 2), ("G6", 2)],
]   # bar 44 (chromatic run) is generated
C_MEL = [
    [("C6", 6), ("Eb6", 4), ("Ab6", 2)],
    [("Ab6", 6), ("G6", 4), ("F6", 2)],
    [("F6", 6), ("Ab6", 4), ("F6", 2)],
    [("D6", 6), ("F6", 4), ("Ab6", 2)],
    [("Bb6", 6), ("G6", 4), ("Eb6", 2)],
    [("Ab6", 6), ("Eb6", 4), ("C6", 2)],
    [("Ab6", 6), ("F6", 4), ("D6", 2)],
    [("Eb6", 6), ("G6", 4), ("Bb6", 2)],
    [("F6", 6), ("Ab6", 4), ("G6", 2)],
    [("Bb6", 6), ("Ab6", 4), ("F6", 2)],
    [("Ab6", 6), ("F6", 4), ("Db6", 2)],
    [("Bb6", 6), ("Ab6", 4), ("Fb6", 2)],
    [("Eb6", 6), ("Ab6", 4), ("C7", 2)],
    [("Ab6", 4), ("Bb6", 2), ("G6", 4), ("Db6", 2)],
]
CODA_VN = {73: [("Eb6", 12)], 74: [("C6", 12)], 75: [("Ab5", 12)], 76: [("Fb5", 12)],
           77: [("Eb5", 6), ("Db5", 6)], 78: [("C6", 12)], 79: [("Eb6", 12)], 80: [("C6", 12)]}

# ================================================================ expression
DYN_VEL = {"ppp": 28, "pp": 40, "p": 52, "mp": 64, "mf": 76, "f": 90, "ff": 104}
DYNS = {1: "pp", 5: "p", 9: "mp", 13: "mf", 16: "p", 21: "mp", 25: "mf", 29: "pp", 33: "p", 37: "mp", 41: "mf",
        45: "f", 49: "f", 54: "ff", 59: "ff", 60: "mf", 61: "p", 65: "mf", 67: "f", 71: "mp", 73: "pp", 80: "ppp"}
WEDGES = [("crescendo", 5, 9), ("crescendo", 9, 13), ("diminuendo", 13, 16), ("crescendo", 17, 21),
          ("crescendo", 21, 25), ("diminuendo", 25, 29), ("crescendo", 29, 33), ("crescendo", 33, 37),
          ("crescendo", 37, 41), ("crescendo", 41, 45), ("crescendo", 49, 54), ("diminuendo", 60, 61),
          ("crescendo", 61, 65), ("crescendo", 65, 67), ("diminuendo", 67, 71), ("diminuendo", 71, 73),
          ("diminuendo", 75, 80)]
VIOLIN_FIRST_BAR = 17
WORDS = {
    ("piano", 1): "Andante sognando, con Ped.", ("piano", 5): "cantabile, dolce",
    ("violin", 17): "dolce, cantabile", ("piano", 29): "Scherzando, leggiero",
    ("violin", 29): "pizz.", ("violin", 37): "arco, espressivo", ("piano", 45): "Appassionato",
    ("violin", 45): "con fuoco", ("piano", 59): "Cadenza, ad libitum", ("piano", 61): "A tempo, più dolce",
    ("violin", 61): "dolcissimo", ("piano", 73): "come una scatola musicale",
    ("piano", 79): "morendo", ("violin", 79): "morendo",
    ("piano", 15): "rit.", ("piano", 27): "rit.", ("piano", 3): "rit.",
    ("piano", 57): "stringendo", ("piano", 70): "rit.",
}
# tempo = dotted-quarter bpm per bar
TEMPO = {1: 52, 4: 46, 5: 56, 8: 53, 9: 56, 12: 53, 13: 56, 15: 50, 16: 44, 17: 56, 27: 52, 28: 46,
         29: 64, 35: 62, 36: 56, 37: 64, 41: 68, 44: 72, 45: 66, 49: 70, 53: 72, 57: 74, 58: 64, 59: 42,
         60: 38, 61: 54, 66: 56, 69: 54, 70: 50, 72: 44, 73: 50, 77: 46, 78: 42, 79: 38, 80: 33}
TEMPO_VISIBLE = {1, 5, 29, 45, 61}
PEDAL = {}
for b in range(1, NBARS + 1):
    PEDAL[b] = "chord"
for b in range(29, 37):
    PEDAL[b] = "none"
for b in range(37, 59):
    PEDAL[b] = "half"
PEDAL[59] = "hold"
for b in range(73, 77):
    PEDAL[b] = "chord"


def dyn_at(bar):
    d = "pp"
    for b in sorted(DYNS):
        if b <= bar:
            d = DYNS[b]
    return DYN_VEL[d]


def vel_at(q):
    bar = int(q // BARQ) + 1
    for _, s, e in WEDGES:
        if s <= bar < e:
            v0, v1 = dyn_at(s), dyn_at(e)
            return v0 + (v1 - v0) * (q - (s - 1) * BARQ) / ((e - s) * BARQ)
    return dyn_at(bar)


# ================================================================ note model
NOTES = []
RESTS = []


def mk(part, staff, voice, bar, start, dur, pitch, **kw):
    n = dict(part=part, staff=staff, voice=voice, bar=bar, start=start, dur=dur, rest=False,
             artic=[], slur=None, fermata=False, arp=False, chord=False, vo=0, stretch=False, **P(pitch))
    n.update(kw)
    return n


def add(part, staff, voice, bar, start_u, dur_u, pitch, **kw):
    n = mk(part, staff, voice, bar, (bar - 1) * BAR + int(round(start_u * DU)), int(round(dur_u * DU)), pitch, **kw)
    NOTES.append(n)
    return n


def pf(bar, start_u, dur_u, pitch, **kw):                 # piano RH
    return add("piano", 1, 1, bar, start_u, dur_u, pitch, **kw)


def pl(bar, start_u, dur_u, pitch, **kw):                 # piano LH
    return add("piano", 2, 5, bar, start_u, dur_u, pitch, **kw)


def vl(bar, start_u, dur_u, pitch, **kw):
    return add("violin", 1, 1, bar, start_u, dur_u, pitch, **kw)


def default_artic(d, mode):
    if mode == "stac":
        return ["staccato"] if d <= 2 else (["accent"] if d == 3 else ["tenuto"])
    if mode == "acc":
        return ["accent"] if d >= 6 else []
    return []


def melody(fn, bar, tuples, mode=None, octave_below=False, vo=8, extra=None):
    pos = 0
    for p, d in tuples:
        n = fn(bar, pos, d, p, vo=vo, artic=list(default_artic(d, mode)))
        if octave_below:
            q = P(p)
            lower = f"{q['step']}{'b' if q['alter'] == -1 else '#' if q['alter'] == 1 else ''}{q['octave'] - 1}"
            fn(bar, pos, d, lower, chord=True, vo=vo - 4, artic=list(n["artic"]))
        pos += d
    assert pos == 12, (bar, pos)


# ---- left-hand textures
def lh_ballade(bar, ch, s, span, vo=-4):
    m = mid(ch)
    seqn = [bass_note(ch), m[0], m[1], m[2], m[1], m[0]][: span // 2]
    for i, p in enumerate(seqn):
        pl(bar, s + 2 * i, 2, p, vo=vo + (3 if i == 0 else 0))


def lh_hold(bar, ch, s, span, vo=-6):
    m = mid(ch)
    if span == 12:
        pl(bar, s, 6, bass_note(ch), vo=vo + 3)
        for i, p in enumerate(m):
            pl(bar, s + 6, 6, p, chord=i > 0, vo=vo)
    else:
        pl(bar, s, 6, bass_note(ch), vo=vo + 3)
        for p in m:
            pl(bar, s, 6, p, chord=True, vo=vo)


def lh_oompah(bar, ch, s, span, vo=-6):
    m = mid(ch)
    for k, beat in enumerate(range(s, s + span, 6)):
        pl(bar, beat, 2, bass_note(ch) if (k == 0 or span == 6) else fifth_low(ch), vo=vo + 4, artic=["staccato"])
        for off in (2, 4):
            for i, p in enumerate(m):
                pl(bar, beat + off, 2, p, chord=i > 0, vo=vo, artic=["staccato"])


def lh_roll(bar, ch, s, span, vo=-6):
    b = bass_note(ch)
    pl_ = [p for p in pool(ch, P(b)["midi"], P(b)["midi"] + 45)][:7]
    idx = [0, 1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1] if span == 12 else [0, 1, 2, 3, 4, 3]
    for i, k in enumerate(idx):
        pl(bar, s + i, 1, pl_[k], vo=vo + (4 if i == 0 else 0))


# ---- right-hand textures
def rh_filig(bar, ch, s, span, vo=-10):
    pp = pool(ch, 55, 76)
    ud = updown(len(pp))
    for i in range(span):
        pf(bar, s + i, 1, pp[ud[i % len(ud)]], vo=vo)


def rh_stac_arp(bar, ch, s, span, rising, vo=-2):
    ps = ladder(ch, 55, span // 2)
    if not rising:
        ps = ps[::-1]
    for i, p in enumerate(ps):
        pf(bar, s + 2 * i, 2, p, vo=vo, artic=["staccato"])


def chords_of(bar):
    h = HARM[bar]
    return [(c, s, 12 if len(h) == 1 else 6) for c, s in h]


# ================================================================ composition
def compose():
    # ---------- intro 1-4: music-box arpeggios
    for bar in range(1, 5):
        for i, (ch, s, span) in enumerate(chords_of(bar)):
            rh_stac_arp(bar, ch, s, span, rising=(bar % 2 == 1) if span == 12 else (i == 0))
            lh_hold(bar, ch, s, span, vo=-2)

    # ---------- A1 5-16: piano sings
    for i, tup in enumerate(A_MEL):
        bar = 5 + i
        melody(pf, bar, tup)
        for ch, s, span in chords_of(bar):
            lh_ballade(bar, ch, s, span)
    # ---------- A2 17-28: violin sings, piano ripples
    for i, tup in enumerate(A_MEL):
        bar = 17 + i
        melody(vl, bar, tup, vo=4)
        for ch, s, span in chords_of(bar):
            rh_filig(bar, ch, s, span)
            lh_hold(bar, ch, s, span, vo=-8)

    # ---------- B 29-44: scherzando
    for i, tup in enumerate(B_MEL):
        bar = 29 + i
        melody(pf, bar, tup, mode="stac", vo=6)
        for ch, s, span in chords_of(bar):
            lh_oompah(bar, ch, s, span)
    # bar 44: chromatic rush  B4 -> Bb5
    for k in range(12):
        nm = ["B", "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb"][k]
        octv = 4 if k == 0 else 5
        pf(44, k, 1, f"{nm}{octv}", vo=4 + k)
    for ch, s, span in chords_of(44):
        lh_roll(44, ch, s, span, vo=-2)
    # violin: pizzicato in B1, arco pads in B2
    for bar in range(29, 37):
        ch = chords_of(bar)[0][0]
        pp = pool(ch, 70, 88)
        vl(bar, 4, 2, pp[2], vo=6, artic=["staccato"])
        vl(bar, 10, 2, pp[1], vo=6, artic=["staccato"])
    for bar in range(37, 45):
        for ch, s, span in chords_of(bar):
            pp = pool(ch, 72, 86)
            vl(bar, s, span, pp[1], vo=2, artic=["tenuto"] if span == 12 else [])

    # ---------- C 45-60: storm
    for i, tup in enumerate(C_MEL):
        bar = 45 + i
        melody(pf, bar, tup, mode="acc", octave_below=True, vo=8)
        melody(vl, bar, tup, mode="acc", vo=4)
        for ch, s, span in chords_of(bar):
            lh_roll(bar, ch, s, span)
    # bar 59: cadenza - Eb7 arpeggio, six octaves, hands in turn (32nds)
    run = pool("Eb7", 27, 110)[:24]
    for k, p in enumerate(run):
        fn = pl if k < 12 else pf
        fn(59, k * 0.5, 0.5, p, vo=2 + k, artic=[])
    NOTES[-1]["fermata"] = True
    # bar 60: breath, falling staccato Eb7 drops, violin holds the fifth
    ps = pool("Eb7", 58, 90)[-6:][::-1]
    for i, p in enumerate(ps):
        pf(60, 2 * i, 2, p, vo=-4, artic=["staccato"])
    lh_hold(60, "Eb7", 0, 12, vo=-6)
    vl(60, 0, 12, "Bb5", vo=0, artic=["tenuto"], fermata=True)

    # ---------- A3 61-72: return, octaves + violin in unison
    for i, tup in enumerate(A_MEL):
        bar = 61 + i
        melody(pf, bar, tup, octave_below=True, vo=6)
        melody(vl, bar, tup, vo=2)
        for ch, s, span in chords_of(bar):
            lh_roll(bar, ch, s, span, vo=-9) if (bar in (67, 68, 69, 70)) else lh_ballade(bar, ch, s, span, vo=-4)

    # ---------- coda 73-80: music box, violin floats
    for bar in range(73, 80):
        for i, (ch, s, span) in enumerate(chords_of(bar)):
            rh_stac_arp(bar, ch, s, span, rising=(bar % 2 == 1) if span == 12 else (i == 0), vo=-4)
            lh_hold(bar, ch, s, span, vo=-4)
        pos = 0
        for p, d in CODA_VN[bar]:
            vl(bar, pos, d, p, artic=["tenuto"] if d == 12 else [])
            pos += d
    # bar 80 final rolled chord
    final = [pl(80, 0, 12, p) for p in (placements("Ab", 34, 47)[0], placements("Eb", 48, 58)[0])]
    final += [pf(80, 0, 12, p) for p in ("Ab3", "C4", "Eb4", "Bb4")]
    final.sort(key=lambda n: n["midi"])
    for r, n in enumerate(final):
        n.update(fermata=True, arp=True, arp_i=r, vo=0, stretch=True)
    seen = set()                                    # first-emitted note per staff is the principal one
    for n in sorted(final, key=lambda n: NOTES.index(n)):
        n["chord"] = n["staff"] in seen
        seen.add(n["staff"])
    vl(80, 0, 12, "C6", artic=["tenuto"], fermata=True, stretch=True)

    # ---------- slurs on the principal melody notes
    def slurs(part, staff, pairs):
        for s, e in pairs:
            grp = [n for n in NOTES if n["part"] == part and n["staff"] == staff and not n["chord"] and s <= n["bar"] <= e
                   and n["voice"] in (1, 5)]
            grp.sort(key=lambda n: n["start"])
            first = next(n for n in grp if n["bar"] == s)
            last = [n for n in grp if n["bar"] == e][-1]
            first["slur"], last["slur"] = "start", "stop"
    slurs("piano", 1, [(b, b + 1) for b in range(5, 17, 2)])
    slurs("violin", 1, [(b, b + 1) for b in range(17, 29, 2)])
    slurs("piano", 1, [(b, b + 1) for b in range(45, 59, 2)])
    slurs("violin", 1, [(b, b + 1) for b in range(45, 59, 2)])
    slurs("piano", 1, [(b, b + 1) for b in range(61, 73, 2)])
    slurs("violin", 1, [(b, b + 1) for b in range(61, 73, 2)])
    slurs("violin", 1, [(b, b + 1) for b in range(73, 80, 2) if b + 1 <= 79])
    # 32nd-note cadenza + chromatic rush get their own slurs
    for bar in (44,):
        g = sorted([n for n in NOTES if n["part"] == "piano" and n["staff"] == 1 and n["bar"] == bar], key=lambda n: n["start"])
        g[0]["slur"], g[-1]["slur"] = "start", "stop"
    for nn in NOTES:
        if nn["part"] == "piano" and nn["bar"] == 59:
            nn["artic"] = []
    resolve_hand_collisions()
    # fill gaps with rests
    fill_rests()


def resolve_hand_collisions():
    """A piano cannot sound the same key twice: an LH note that doubles a sounding RH pitch drops an octave."""
    changed = True
    while changed:
        changed = False
        sounding = [n for n in NOTES if n["part"] == "piano"]
        for lh in (n for n in sounding if n["staff"] == 2):
            for other in sounding:
                if other is lh or other["midi"] != lh["midi"]:
                    continue
                if other["start"] < lh["start"] + lh["dur"] and lh["start"] < other["start"] + other["dur"]:
                    nm = f"{lh['step']}{'b' if lh['alter'] == -1 else '#' if lh['alter'] == 1 else ''}{lh['octave'] - 1}"
                    lh.update(P(nm))
                    changed = True
                    break


ALLOWED = [24, 16, 12, 8, 6, 4, 3, 2, 1]


def fill_rests():
    keys = {(p, st, v) for p, st, v in (("violin", 1, 1), ("piano", 1, 1), ("piano", 2, 5))}
    for part, staff, voice in keys:
        for bar in range(1, NBARS + 1):
            base = (bar - 1) * BAR
            grp = sorted((n for n in NOTES if (n["part"], n["staff"], n["voice"], n["bar"]) == (part, staff, voice, bar)),
                         key=lambda n: n["start"])
            cur = base
            for n in grp:
                if n["chord"]:
                    continue
                assert n["start"] >= cur, f"overlap {part} {staff} bar {bar} at {n['start']} < {cur}"
                if n["start"] > cur:
                    add_rest(part, staff, voice, bar, cur, n["start"] - cur)
                cur = n["start"] + n["dur"]
            assert cur <= base + BAR, f"bar {bar} {part}/{staff} overruns ({cur - base})"
            if cur < base + BAR:
                add_rest(part, staff, voice, bar, cur, base + BAR - cur)


def add_rest(part, staff, voice, bar, start, dur):
    while dur:
        d = next(a for a in ALLOWED if a <= dur)
        NOTES.append(dict(part=part, staff=staff, voice=voice, bar=bar, start=start, dur=d, rest=True, artic=[],
                          slur=None, fermata=False, arp=False, chord=False, vo=0, stretch=False))
        start += d
        dur -= d


# ================================================================ MIDI
def vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


def meta(tick, typ, data):
    return (tick, 1, b"\xff" + bytes([typ]) + vlq(len(data)) + data)


def track_bytes(events):
    events.sort(key=lambda e: (e[0], e[1]))
    out, last = b"", 0
    for t, _, data in events:
        out += vlq(t - last) + data
        last = t
    out += vlq(0) + b"\xff\x2f\x00"
    return b"MTrk" + struct.pack(">I", len(out)) + out


BAR_TICKS = BAR * TICK


def build_midi():
    rng = random.Random(11)
    cond = [meta(0, 0x03, TITLE.encode()), meta(0, 0x02, f"(c) {COMPOSER}".encode()),
            meta(0, 0x58, bytes([6, 3, 36, 8])),                         # 6/8
            meta(0, 0x59, struct.pack("bB", KEY_FIFTHS, 0))]             # Ab major
    for bar, bpm in TEMPO.items():
        quarter_bpm = bpm * 1.5
        cond.append(meta((bar - 1) * BAR_TICKS, 0x51, struct.pack(">I", int(60_000_000 / quarter_bpm))[1:]))

    def setup(ch, prog, name, vol, pan, rev):
        return [meta(0, 0x03, name.encode()), (0, 0, bytes([0xC0 | ch, prog])), (0, 0, bytes([0xB0 | ch, 7, vol])),
                (0, 0, bytes([0xB0 | ch, 10, pan])), (0, 0, bytes([0xB0 | ch, 91, rev]))]

    vio = setup(0, 40, "Violin", 88, 40, 62) + [(0, 0, bytes([0xB0, 1, 40]))]
    pno = setup(1, 0, "Piano", 108, 74, 48)
    # pizzicato strings (GM 46) for bars 29-36
    vio.append(((29 - 1) * BAR_TICKS - 2, 0, bytes([0xC0, 45])))
    vio.append(((37 - 1) * BAR_TICKS - 2, 0, bytes([0xC0, 40])))
    notes = [n for n in NOTES if not n["rest"]]
    for n in notes:
        ch = 0 if n["part"] == "violin" else 1
        ev = vio if ch == 0 else pno
        on, dur = n["start"] * TICK, n["dur"] * TICK
        if n["stretch"]:
            dur = int(dur * 1.6)
        base = vel_at(n["start"] / DIV)
        vel = base + n["vo"] + (12 if "accent" in n["artic"] else 0)
        if n["part"] == "violin" and "staccato" in n["artic"]:
            vel -= 4
        vel = max(18, min(122, int(round(vel + rng.uniform(-2.5, 2.5)))))
        if n["arp"]:
            on += 70 * n["arp_i"] if "arp_i" in n else 0
        if "staccato" in n["artic"]:
            off = on + max(20, int(dur * 0.42))
        elif "tenuto" in n["artic"]:
            off = on + int(dur * 0.995)
        else:
            off = on + int(dur * 0.97)
        ev.append((on, 3, bytes([0x90 | ch, n["midi"], vel])))
        ev.append((off, 2, bytes([0x80 | ch, n["midi"], 0])))
    for half_q in range(NBARS * BARQ * 2):
        q = half_q / 2
        vio.append((int(q * PPQ), 1, bytes([0xB0, 11, int(max(36, min(122, vel_at(q) * 1.1 + 22)))])))
    # sustain pedal
    for bar in range(1, NBARS + 1):
        t0 = (bar - 1) * BAR_TICKS
        mode = PEDAL[bar]
        pts = []
        if mode == "chord":
            pts = [t0 + s * DU * TICK for _, s in HARM[bar]]
        elif mode == "half":
            pts = [t0, t0 + 6 * DU * TICK]
        elif mode == "hold":
            pts = [t0]
        if mode == "none":
            if t0:
                pno.append((t0 - 8, 1, bytes([0xB1, 64, 0])))
            continue
        for t in pts:
            if t:
                pno.append((t - 8, 1, bytes([0xB1, 64, 0])))
            pno.append((t + 4, 1, bytes([0xB1, 64, 127])))
    last_off = max(e[0] for e in vio + pno)
    pno.append((last_off, 1, bytes([0xB1, 64, 0])))
    header = b"MThd" + struct.pack(">IHHH", 6, 1, 3, PPQ)
    return header + track_bytes(cond) + track_bytes(vio) + track_bytes(pno)


# ================================================================ MusicXML
TYPE = {24: ("half", 1), 16: ("half", 0), 12: ("quarter", 1), 8: ("quarter", 0), 6: ("eighth", 1),
        4: ("eighth", 0), 3: ("16th", 1), 2: ("16th", 0), 1: ("32nd", 0)}
ACC_NAME = {-1: "flat", 0: "natural", 1: "sharp"}


def el(parent, tag, text=None, **attrs):
    e = etree.SubElement(parent, tag, {k: str(v) for k, v in attrs.items()})
    if text is not None:
        e.text = str(text)
    return e


def add_direction(m, placement="below", staff=None, dyn=None, wedge=None, words=None, metro=None, tempo=None):
    d = el(m, "direction", placement=placement)
    dt = el(d, "direction-type")
    if dyn:
        el(el(dt, "dynamics"), dyn)
    if wedge:
        el(dt, "wedge", type=wedge, number=1)
    if words:
        el(dt, "words", words, **{"font-style": "italic"})
    if metro:
        mt = el(dt, "metronome")
        el(mt, "beat-unit", "quarter")
        el(mt, "beat-unit-dot")
        el(mt, "per-minute", metro)
    if staff:
        el(d, "staff", staff)
    if tempo:
        el(d, "sound", tempo=round(tempo * 1.5, 1))
    elif dyn:
        el(d, "sound", dynamics=round(DYN_VEL[dyn] * 100 / 90))


class Acc:
    def __init__(self):
        self.state = {}

    def need(self, step, octv, alter):
        cur = self.state.get((step, octv), -1 if step in KEY_FLATS else 0)
        self.state[(step, octv)] = alter
        return ACC_NAME[alter] if cur != alter else None


def write_note(m, n, acc):
    x = el(m, "note")
    if n["rest"]:
        el(x, "rest")
        el(x, "duration", n["dur"])
        el(x, "voice", n["voice"])
        typ, dots = TYPE[n["dur"]]
        el(x, "type", typ)
        for _ in range(dots):
            el(x, "dot")
        if n["part"] == "piano":
            el(x, "staff", n["staff"])
        return
    if n["chord"]:
        el(x, "chord")
    pt = el(x, "pitch")
    el(pt, "step", n["step"])
    if n["alter"]:
        el(pt, "alter", n["alter"])
    el(pt, "octave", n["octave"])
    el(x, "duration", n["dur"])
    el(x, "voice", n["voice"])
    typ, dots = TYPE[n["dur"]]
    el(x, "type", typ)
    for _ in range(dots):
        el(x, "dot")
    a = acc.need(n["step"], n["octave"], n["alter"])
    if a:
        el(x, "accidental", a)
    if n["part"] == "piano":
        el(x, "staff", n["staff"])
    if n["slur"] or n["fermata"] or n["arp"] or n["artic"]:
        nt = el(x, "notations")
        if n["slur"]:
            el(nt, "slur", type=n["slur"], number=1)
        if n["artic"]:
            ar = el(nt, "articulations")
            for a_ in n["artic"]:
                el(ar, a_)
        if n["fermata"]:
            el(nt, "fermata", type="upright")
        if n["arp"]:
            el(nt, "arpeggiate")


def chord_label(m, ch, staff):
    d = el(m, "direction", placement="above")
    el(el(d, "direction-type"), "words", CHORDS[ch][0], **{"font-weight": "bold", "font-size": "9"})
    el(d, "staff", staff)


def build_xml():
    root = etree.Element("score-partwise", version="4.0")
    work = el(root, "work")
    el(work, "work-title", TITLE)
    ident = el(root, "identification")
    el(ident, "creator", COMPOSER, type="composer")
    el(el(ident, "encoding"), "software", "generate_embers.py")
    ct = el(root, "credit", page=1)
    el(ct, "credit-type", "title")
    el(ct, "credit-words", TITLE, **{"default-x": 600, "default-y": 1480, "font-size": 24, "justify": "center",
                                     "valign": "top", "halign": "center"})
    cr = el(root, "credit", page=1)
    el(cr, "credit-type", "subtitle")
    el(cr, "credit-words", SUBTITLE, **{"default-x": 600, "default-y": 1380, "font-size": 12, "justify": "center",
                                        "valign": "top", "halign": "center"})
    pl_ = el(root, "part-list")
    for pid, name, abbr, ch, prog, pan in (("P1", "Violin", "Vln.", 1, 41, -30), ("P2", "Piano", "Pno.", 2, 1, 25)):
        sp = el(pl_, "score-part", id=pid)
        el(sp, "part-name", name)
        el(sp, "part-abbreviation", abbr)
        el(el(sp, "score-instrument", id=f"{pid}-I1"), "instrument-name", name)
        mi = el(sp, "midi-instrument", id=f"{pid}-I1")
        el(mi, "midi-channel", ch)
        el(mi, "midi-program", prog)
        el(mi, "pan", pan)
    wedge_start = {s: k for k, s, e in WEDGES}
    wedge_stop = {e for k, s, e in WEDGES}
    for pid, part in (("P1", "violin"), ("P2", "piano")):
        pe = el(root, "part", id=pid)
        pn = [n for n in NOTES if n["part"] == part]
        for bar in range(1, NBARS + 1):
            m = el(pe, "measure", number=bar)
            acc = {1: Acc(), 2: Acc()}
            base = (bar - 1) * BAR
            if bar == 1:
                a = el(m, "attributes")
                el(a, "divisions", DIV)
                k = el(a, "key")
                el(k, "fifths", KEY_FIFTHS)
                el(k, "mode", "major")
                t = el(a, "time")
                el(t, "beats", 6)
                el(t, "beat-type", 8)
                if part == "piano":
                    el(a, "staves", 2)
                    c1 = el(a, "clef", number=1)
                    el(c1, "sign", "G")
                    el(c1, "line", 2)
                    c2 = el(a, "clef", number=2)
                    el(c2, "sign", "F")
                    el(c2, "line", 4)
                else:
                    c = el(a, "clef")
                    el(c, "sign", "G")
                    el(c, "line", 2)
            if part == "violin" and bar in TEMPO:
                add_direction(m, placement="above", tempo=TEMPO[bar], metro=TEMPO[bar] if bar in TEMPO_VISIBLE else None)
            if (part, bar) in WORDS:
                add_direction(m, placement="above", words=WORDS[(part, bar)], staff=1 if part == "piano" else None)
            st = 2 if part == "piano" else None
            show = not (part == "violin" and bar < VIOLIN_FIRST_BAR)
            if bar in wedge_stop and show and not (part == "violin" and bar <= VIOLIN_FIRST_BAR):
                add_direction(m, staff=st, wedge="stop")
            if bar in DYNS and show:
                add_direction(m, staff=st, dyn=DYNS[bar])
            if part == "violin" and bar == VIOLIN_FIRST_BAR:
                add_direction(m, staff=st, dyn="p")
            if bar in wedge_start and show:
                add_direction(m, staff=st, wedge=wedge_start[bar])
            bn = sorted((n for n in pn if base <= n["start"] < base + BAR), key=lambda n: (n["staff"], n["start"]))
            if part == "violin":
                if len(bn) == 1 and bn[0]["rest"] and bn[0]["dur"] == BAR:
                    x = el(m, "note")
                    el(x, "rest", measure="yes")
                    el(x, "duration", BAR)
                    el(x, "voice", 1)
                else:
                    for n in bn:
                        write_note(m, n, acc[1])
            else:
                chord_at = {base + s * DU: c for c, s in HARM[bar]}
                done = set()
                for n in (n for n in bn if n["staff"] == 1):
                    if n["start"] in chord_at and n["start"] not in done and not n["chord"]:
                        chord_label(m, chord_at[n["start"]], 1)
                        done.add(n["start"])
                    write_note(m, n, acc[1])
                el(el(m, "backup"), "duration", BAR)
                for n in (n for n in bn if n["staff"] == 2):
                    write_note(m, n, acc[2])
            if bar == NBARS:
                el(el(m, "barline", location="right"), "bar-style", "light-heavy")
    return root


def main():
    compose()
    mid = build_midi()
    (OUT / f"{BASE}.mid").write_bytes(mid)
    body = etree.tostring(build_xml(), encoding="unicode", pretty_print=True)
    head = ('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
            '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
            '"http://www.musicxml.org/dtds/partwise.dtd">\n')
    (OUT / f"{BASE}.musicxml").write_text(head + body, encoding="utf-8")
    real = [n for n in NOTES if not n["rest"]]
    print(f"{len(real)} notes (violin {sum(n['part'] == 'violin' for n in real)}, "
          f"piano {sum(n['part'] == 'piano' for n in real)}); MIDI {len(mid)} bytes")


if __name__ == "__main__":
    main()
