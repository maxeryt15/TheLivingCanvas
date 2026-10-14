"""Generates 'The Garden Remembers' (violin + piano, 4/4, Db major / Bb minor)
as a Standard MIDI File (type 1) and a MusicXML 4.0 score from ONE note model,
so both files always agree.  Run:  python generate_soundtrack.py
"""
import random
import re
import struct
from pathlib import Path

from lxml import etree

OUT = Path(__file__).parent
TITLE = "The Garden Remembers"
COMPOSER = "Claude (original composition)"
PPQ = 480            # MIDI ticks per quarter
DIV = 4              # MusicXML divisions per quarter (1 division = 120 ticks)
TICK = PPQ // DIV
BAR = 16             # divisions per 4/4 bar
NBARS = 40
KEY_FIFTHS = -5      # Db major
KEY_FLATS = {"B", "E", "A", "D", "G"}

STEP_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def P(name):
    step, acc, octv = re.fullmatch(r"([A-G])(b|#)?(-?\d)", name).groups()
    alter = {None: 0, "b": -1, "#": 1}[acc]
    o = int(octv)
    return dict(step=step, alter=alter, octave=o, midi=12 * (o + 1) + STEP_PC[step] + alter)


def down_octave(name):
    p = P(name)
    return f"{p['step']}{'b' if p['alter'] == -1 else '#' if p['alter'] == 1 else ''}{p['octave'] - 1}"


# ---------------------------------------------------------------- harmony
# name: (chord label, LH notes, RH arpeggio tones)
CH = {
    "Dbadd9":    ("D♭add9",   ["Db2", "Ab2"], ["Ab3", "Db4", "Eb4", "F4"]),
    "Bbm9":      ("B♭m9",     ["Bb1", "F2"],  ["Ab3", "C4", "Db4", "F4"]),
    "Bbm7":      ("B♭m7",     ["Bb1", "F2"],  ["Ab3", "Db4", "F4", "Ab4"]),
    "Gbmaj7":    ("G♭maj7",   ["Gb2", "Db3"], ["Bb3", "Db4", "F4", "Bb4"]),
    "Ebm7":      ("E♭m7",     ["Eb2", "Bb2"], ["Gb3", "Bb3", "Db4", "Gb4"]),
    "Ebm9":      ("E♭m9",     ["Eb2", "Bb2"], ["Gb3", "Bb3", "Db4", "F4"]),
    "Ab7":       ("A♭7",      ["Ab2", "Eb3"], ["C4", "Eb4", "Gb4", "C5"]),
    "Ab7sus4":   ("A♭7sus4",  ["Ab2", "Eb3"], ["Db4", "Eb4", "Gb4", "Ab4"]),
    "Dbmaj7":    ("D♭maj7",   ["Db2", "Ab2"], ["Ab3", "C4", "F4", "Ab4"]),
    "Gbmaj7#11": ("G♭maj7(♯11)", ["Gb2", "Db3"], ["Bb3", "Db4", "F4", "C5"]),
    "Fm7":       ("Fm7",           ["F2", "C3"],   ["Ab3", "C4", "Eb4", "Ab4"]),
    "Dbmaj9/F":  ("D♭maj9/F", ["F2", "C3"],   ["Ab3", "Db4", "Eb4", "Ab4"]),
    "Cbmaj7":    ("C♭maj7",   ["Cb2", "Gb2"], ["Eb4", "Gb4", "Bb4", "Eb5"]),
}

# per bar (1-based): chords as [(name, start beat)]
PROG = {b: [(c, 0)] for b, c in {
    1: "Dbadd9", 2: "Bbm9", 3: "Gbmaj7", 4: "Ab7sus4",
    5: "Bbm7", 6: "Gbmaj7", 7: "Ebm7", 8: "Ab7", 9: "Dbmaj7", 10: "Gbmaj7", 11: "Ebm7", 12: "Ab7",
    13: "Gbmaj7#11", 14: "Fm7", 15: "Ebm9", 16: "Dbmaj9/F", 17: "Bbm7", 18: "Cbmaj7", 19: "Ebm7", 20: "Ab7",
    21: "Dbmaj7", 22: "Gbmaj7", 23: "Bbm7", 24: "Ebm7", 25: "Gbmaj7", 26: "Ab7", 27: "Dbmaj7",
    29: "Bbm7", 30: "Gbmaj7", 31: "Ebm7", 32: "Ab7", 33: "Dbmaj7", 34: "Gbmaj7", 35: "Ebm9", 36: "Ab7",
    37: "Dbadd9", 38: "Gbmaj7", 40: "Dbadd9",
}.items()}
PROG[28] = [("Gbmaj7", 0), ("Ab7", 2)]
PROG[39] = [("Ebm7", 0), ("Ab7", 2)]

# ---------------------------------------------------------------- violin melody: (pitch, beats)
VN = {
    5:  [("F5", 3), ("Eb5", 1)],
    6:  [("Db5", 2), ("Bb4", 1), ("Db5", 1)],
    7:  [("Gb5", 3), ("F5", .5), ("Eb5", .5)],
    8:  [("Eb5", 2), ("Db5", 1), ("C5", 1)],
    9:  [("Db5", 1), ("F5", 1), ("Ab5", 2)],
    10: [("Bb5", 3), ("Ab5", 1)],
    11: [("Gb5", 1.5), ("F5", .5), ("Eb5", 1), ("Gb5", 1)],
    12: [("C5", 1), ("Eb5", 3)],
    13: [("Bb5", 2), ("C6", 1), ("Bb5", 1)],
    14: [("Ab5", 2), ("C6", 1), ("Eb6", 1)],
    15: [("Db6", 3), ("Bb5", 1)],
    16: [("Ab5", 2), ("F5", 1), ("Ab5", 1)],
    17: [("Db6", 2), ("C6", 1), ("Bb5", 1)],
    18: [("Eb6", 2), ("Gb6", 2)],
    19: [("F6", 3), ("Eb6", 1)],
    20: [("Eb6", 2), ("Db6", 1), ("C6", 1)],
    21: [("F5", 1), ("Ab5", 1), ("Db6", 2)],
    22: [("Db6", 3), ("Bb5", 1)],
    23: [("Ab6", 3), ("F6", .5), ("Eb6", .5)],
    24: [("Gb6", 2), ("F6", 1), ("Eb6", 1)],
    25: [("Db6", 2), ("Bb5", 1), ("Gb5", 1)],
    26: [("Ab5", 2), ("Gb5", 1), ("Eb5", 1)],
    27: [("Ab5", 2), ("F5", 2)],
    28: [("Bb5", 2), ("C6", 2)],
    29: [("F5", 3), ("Eb5", 1)],
    30: [("Db5", 2), ("Bb4", 1), ("Db5", 1)],
    31: [("Gb5", 3), ("F5", 1)],
    32: [("Eb5", 2), ("Db5", 1), ("C5", 1)],
    33: [("F5", 2), ("Ab5", 2)],
    34: [("Bb5", 2), ("Ab5", 1), ("Gb5", 1)],
    35: [("F5", 2), ("Eb5", 2)],
    36: [("C5", 2), ("Eb5", 2)],
    37: [("Ab5", 3), ("F5", 1)],
    38: [("Bb5", 2), ("Ab5", 2)],
    39: [("Gb5", 2), ("Eb5", 2)],
    40: [("Db5", 4)],
}
SLUR_PAIRS = [(b, b + 1) for b in range(5, 40, 2)]          # (5,6) ... (39,40)

# ---------------------------------------------------------------- expression
DYN_VEL = {"pp": 40, "p": 52, "mp": 64, "mf": 76, "f": 92}
DYNS = {1: "pp", 5: "p", 9: "mp", 15: "mf", 21: "f", 27: "mp", 29: "p", 33: "pp"}
VIOLIN_DYN_FROM = 5
WEDGES = [("crescendo", 19, 21), ("diminuendo", 25, 27)]    # (kind, start bar, bar that holds the target dynamic)
WORDS = {
    ("violin", 5): "dolce, espressivo", ("violin", 13): "più intenso", ("violin", 21): "con passione",
    ("violin", 29): "dolce, come un ricordo", ("violin", 37): "rit.", ("piano", 37): "rit.",
    ("piano", 1): "con Ped.", ("piano", 40): "morendo",
}
TEMPOS = {1: 60, 37: 56, 39: 50, 40: 44}                     # bar -> quarter-note bpm
FERMATA_STRETCH = 1.5


def dyn_at(bar):
    d = "pp"
    for b in sorted(DYNS):
        if b <= bar:
            d = DYNS[b]
    return DYN_VEL[d]


def vel_at(q):
    """Base velocity at absolute position q (quarter notes from the start), honouring hairpins."""
    bar = int(q // 4) + 1
    for _, s, e in WEDGES:
        if s <= bar < e:
            v0, v1 = dyn_at(s), dyn_at(e)
            return v0 + (v1 - v0) * (q - (s - 1) * 4) / ((e - s) * 4)
    return dyn_at(bar)


# ---------------------------------------------------------------- note model
def mk(part, staff, voice, bar, start, dur, pitch, **kw):
    n = dict(part=part, staff=staff, voice=voice, bar=bar, start=start, dur=dur,
             artic=[], slur=None, fermata=False, arp=False, chord=False, **P(pitch))
    n.update(kw)
    return n


def build_notes():
    notes, vn = [], []
    for bar in sorted(VN):
        pos = 0
        for p, beats in VN[bar]:
            d = int(round(beats * DIV))
            n = mk("violin", 1, 1, bar, (bar - 1) * BAR + pos, d, p)
            if d >= 12:
                n["artic"].append("tenuto")
            vn.append(n)
            pos += d
        assert pos == BAR, f"violin bar {bar} sums to {pos}"
    next(n for n in vn if n["bar"] == 23)["artic"].append("accent")      # the Ab6 peak
    for s, e in SLUR_PAIRS:
        next(n for n in vn if n["bar"] == s)["slur"] = "start"
        [n for n in vn if n["bar"] == e][-1]["slur"] = "stop"
    vn[-1]["fermata"] = True
    notes += vn

    pat8 = [0, 1, 2, 3, 2, 1, 2, 1]
    pat16 = [0, 1, 2, 3, 2, 1, 2, 3, 2, 3, 2, 1, 2, 1, 0, 1]
    for bar in range(1, NBARS + 1):
        base = (bar - 1) * BAR
        chords = PROG[bar]
        if bar == NBARS:                                                   # final rolled chord
            _, lh, rh = CH[chords[0][0]]
            for i, p in enumerate(rh):
                notes.append(mk("piano", 1, 1, bar, base, BAR, p, chord=i > 0, fermata=True, arp=True))
            for i, p in enumerate(lh):
                notes.append(mk("piano", 2, 5, bar, base, BAR, p, chord=i > 0, fermata=True, arp=True))
            continue
        climax = 21 <= bar <= 28
        step = 1 if climax else 2                                          # 16ths in the climax, 8ths elsewhere
        for ci, (cname, beat) in enumerate(chords):
            _, lh, rh = CH[cname]
            start = base + beat * DIV
            if len(chords) == 1:
                seq = pat16 if climax else pat8
            else:
                half8 = [0, 1, 2, 3] if ci == 0 else [0, 1, 2, 1]
                seq = [0, 1, 2, 3, 2, 1, 2, 3] if climax else half8
            for k, ix in enumerate(seq):
                notes.append(mk("piano", 1, 1, bar, start + k * step, step, rh[ix]))
            bass = [(0, lh[0]), (8, lh[1])] if len(chords) == 1 else [(0, lh[0])]
            for off, p in bass:
                notes.append(mk("piano", 2, 5, bar, start + off, 8, p))
                if climax and off == 0:                                    # octave-doubled bass
                    notes.append(mk("piano", 2, 5, bar, start, 8, down_octave(p), chord=True))
    return notes


# ---------------------------------------------------------------- MIDI
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
    events.sort(key=lambda e: (e[0], e[1]))      # order 2 = note off, 3 = note on (offs first)
    out, last = b"", 0
    for t, _, data in events:
        out += vlq(t - last) + data
        last = t
    out += vlq(0) + b"\xff\x2f\x00"
    return b"MTrk" + struct.pack(">I", len(out)) + out


def build_midi(notes):
    rng = random.Random(7)
    cond = [meta(0, 0x03, TITLE.encode()),
            meta(0, 0x02, f"(c) {COMPOSER}".encode()),
            meta(0, 0x58, bytes([4, 2, 24, 8])),                           # 4/4
            meta(0, 0x59, struct.pack("bB", KEY_FIFTHS, 0))]               # Db major
    for bar, bpm in TEMPOS.items():
        cond.append(meta((bar - 1) * 4 * PPQ, 0x51, struct.pack(">I", 60_000_000 // bpm)[1:]))

    def setup(ch, prog, name, pan, reverb):
        return [meta(0, 0x03, name.encode()), (0, 0, bytes([0xC0 | ch, prog])),
                (0, 0, bytes([0xB0 | ch, 7, 100])), (0, 0, bytes([0xB0 | ch, 10, pan])),
                (0, 0, bytes([0xB0 | ch, 91, reverb]))]

    vio = setup(0, 40, "Violin", 52, 55) + [(0, 0, bytes([0xB0, 1, 38]))]    # light vibrato (CC1)
    pno = setup(1, 0, "Piano", 70, 45)
    violin_bars = {n["bar"] for n in notes if n["part"] == "violin"}

    for n in notes:
        ch = 0 if n["part"] == "violin" else 1
        ev = vio if ch == 0 else pno
        on, dur = n["start"] * TICK, n["dur"] * TICK
        if n["fermata"]:
            dur = int(dur * FERMATA_STRETCH)
        base = vel_at(n["start"] / DIV)
        if ch == 0:
            vel = base + 4
        else:
            vel = base + (-8 if n["bar"] in violin_bars else 4) + (4 if n["staff"] == 2 else 0)
            if n["staff"] == 1 and n["start"] % 4 == 0:
                vel += 3                                                    # soft beat accents in the arpeggio
        vel = max(20, min(120, int(round(vel + rng.uniform(-2, 2)))))
        if n["arp"]:
            on += 55 * (n["midi"] % 4)                                      # rolled final chord
        off = on + (int(dur * 0.985) if ch == 0 or n["dur"] >= 8 else int(dur * 0.95))
        ev.append((on, 3, bytes([0x90 | ch, n["midi"], vel])))
        ev.append((off, 2, bytes([0x80 | ch, n["midi"], 0])))

    for half_q in range(NBARS * 8):                                         # expression follows the dynamics
        q = half_q / 2
        vio.append((int(q * PPQ), 1, bytes([0xB0, 11, int(max(40, min(120, vel_at(q) * 1.15 + 18)))])))
    for bar in range(1, NBARS + 1):                                         # re-pedal at each harmonic change
        for _, beat in PROG[bar]:
            t = (bar - 1) * 4 * PPQ + beat * PPQ
            if t:
                pno.append((t - 10, 1, bytes([0xB1, 64, 0])))
            pno.append((t + 4, 1, bytes([0xB1, 64, 127])))
    last_off = max(e[0] for e in vio + pno)
    pno.append((last_off, 1, bytes([0xB1, 64, 0])))

    header = b"MThd" + struct.pack(">IHHH", 6, 1, 3, PPQ)
    return header + track_bytes(cond) + track_bytes(vio) + track_bytes(pno)


# ---------------------------------------------------------------- MusicXML
TYPE = {16: ("whole", 0), 12: ("half", 1), 8: ("half", 0), 6: ("quarter", 1), 4: ("quarter", 0),
        3: ("eighth", 1), 2: ("eighth", 0), 1: ("16th", 0)}
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
        el(mt, "per-minute", metro)
    if staff:
        el(d, "staff", staff)
    if tempo:
        el(d, "sound", tempo=tempo)
    elif dyn:
        el(d, "sound", dynamics=round(DYN_VEL[dyn] * 100 / 90))


class Acc:
    """Tracks accidentals within a measure so <accidental> is written only when needed."""
    def __init__(self):
        self.state = {}

    def need(self, step, octv, alter):
        cur = self.state.get((step, octv), -1 if step in KEY_FLATS else 0)
        self.state[(step, octv)] = alter
        return ACC_NAME[alter] if cur != alter else None


def write_note(m, n, acc, staff=None):
    x = el(m, "note")
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
    if staff:
        el(x, "staff", staff)
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


def write_chord_label(m, cname, staff):
    """Chord label as text, not <harmony>: MuseScore would otherwise realise <harmony> as extra playback notes."""
    d = el(m, "direction", placement="above")
    el(el(d, "direction-type"), "words", CH[cname][0], **{"font-weight": "bold", "font-size": "9"})
    el(d, "staff", staff)


def build_xml(notes):
    root = etree.Element("score-partwise", version="4.0")
    el(el(root, "work"), "work-title", TITLE)
    ident = el(root, "identification")
    el(ident, "creator", COMPOSER, type="composer")
    el(el(ident, "encoding"), "software", "generate_soundtrack.py")
    pl = el(root, "part-list")
    for pid, name, abbr, ch, prog, pan in (("P1", "Violin", "Vln.", 1, 41, -15), ("P2", "Piano", "Pno.", 2, 1, 15)):
        sp = el(pl, "score-part", id=pid)
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
        pn = [n for n in notes if n["part"] == part]
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
                el(t, "beats", 4)
                el(t, "beat-type", 4)
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
                    add_direction(m, placement="above", words="Lento, con espressione", metro=60, tempo=60)
            elif bar in TEMPOS and part == "violin":
                add_direction(m, placement="above", tempo=TEMPOS[bar])
            st = 2 if part == "piano" else None                            # dynamics sit between the staves
            if (part, bar) in WORDS:
                add_direction(m, placement="above", words=WORDS[(part, bar)], staff=1 if part == "piano" else None)
            shown = not (part == "violin" and bar < VIOLIN_DYN_FROM)
            if bar in wedge_stop and shown:
                add_direction(m, staff=st, wedge="stop")
            if bar in DYNS and shown:
                add_direction(m, staff=st, dyn=DYNS[bar])
            if bar in wedge_start:
                add_direction(m, staff=st, wedge=wedge_start[bar])
            bn = sorted((n for n in pn if base <= n["start"] < base + BAR), key=lambda n: (n["staff"], n["start"]))
            if part == "violin":
                if not bn:
                    x = el(m, "note")
                    el(x, "rest", measure="yes")
                    el(x, "duration", BAR)
                    el(x, "voice", 1)
                for n in bn:
                    write_note(m, n, acc[1])
            else:
                chord_at = {base + b * DIV: c for c, b in PROG[bar]}
                done = set()
                for n in (n for n in bn if n["staff"] == 1):
                    if n["start"] in chord_at and n["start"] not in done:
                        write_chord_label(m, chord_at[n["start"]], 1)
                        done.add(n["start"])
                    write_note(m, n, acc[1], staff=1)
                el(el(m, "backup"), "duration", BAR)
                for n in (n for n in bn if n["staff"] == 2):
                    write_note(m, n, acc[2], staff=2)
            if bar == NBARS:
                bl = el(m, "barline", location="right")
                el(bl, "bar-style", "light-heavy")
    return root


def main():
    notes = build_notes()
    mid = build_midi(notes)
    (OUT / "the_garden_remembers.mid").write_bytes(mid)
    body = etree.tostring(build_xml(notes), encoding="unicode", pretty_print=True)
    head = ('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
            '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
            '"http://www.musicxml.org/dtds/partwise.dtd">\n')
    (OUT / "the_garden_remembers.musicxml").write_text(head + body, encoding="utf-8")
    print(f"{len(notes)} notes; MIDI {len(mid)} bytes")


if __name__ == "__main__":
    main()
