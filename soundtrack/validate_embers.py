"""Independent validation of embers_and_lamplight.mid / .musicxml: re-parses both files from disk and checks
structure, note durations, ranges, and that MIDI and MusicXML contain the same notes."""
import struct
import sys
from collections import Counter
from pathlib import Path

from lxml import etree

D = Path(__file__).parent
BASE = "embers_and_lamplight"
NB, BARDIV, DIVS = 80, 24, 8
errors = []


def check(c, msg):
    if not c:
        errors.append(msg)
        print("FAIL:", msg)


def read_vlq(b, i):
    v = 0
    while True:
        c = b[i]
        i += 1
        v = (v << 7) | (c & 0x7F)
        if not c & 0x80:
            return v, i


def parse_midi(path):
    b = path.read_bytes()
    check(b[:4] == b"MThd", "MIDI header")
    ln, fmt, ntr, ppq = struct.unpack(">IHHH", b[4:14])
    check(ln == 6 and fmt == 1, "MIDI type 1")
    i, tracks = 14, []
    for _ in range(ntr):
        check(b[i:i + 4] == b"MTrk", "MTrk chunk")
        size = struct.unpack(">I", b[i + 4:i + 8])[0]
        data, i = b[i + 8:i + 8 + size], i + 8 + size
        j, tick, status, ev = 0, 0, 0, []
        while j < len(data):
            dt, j = read_vlq(data, j)
            tick += dt
            if data[j] == 0xFF:
                typ = data[j + 1]
                l, j2 = read_vlq(data, j + 2)
                ev.append((tick, "meta", typ, data[j2:j2 + l]))
                j = j2 + l
            else:
                if data[j] & 0x80:
                    status = data[j]
                    j += 1
                n = 1 if status >> 4 in (0xC, 0xD) else 2
                ev.append((tick, "msg", status, tuple(data[j:j + n])))
                j += n
        check(ev[-1][1:3] == ("meta", 0x2F), "End-of-Track present")
        tracks.append(ev)
    check(i == len(b), "no trailing bytes")
    return ppq, tracks


def midi_notes(ev):
    open_, out = {}, []
    for t, k, s, d in ev:
        if k != "msg":
            continue
        typ, ch = s >> 4, s & 15
        if typ == 9 and d[1] > 0:
            check((ch, d[0]) not in open_, f"overlapping same pitch {d[0]} at tick {t}")
            open_[(ch, d[0])] = t
        elif typ == 8 or (typ == 9 and d[1] == 0):
            st = open_.pop((ch, d[0]), None)
            check(st is not None, f"note-off without note-on {d[0]} at {t}")
            if st is not None:
                out.append((st, t - st, d[0], ch))
    check(not open_, "hanging notes")
    return sorted(out)


ppq, tracks = parse_midi(D / f"{BASE}.mid")
cond, vio, pno = tracks
tempos = [(t, 60_000_000 / int.from_bytes(d, "big")) for t, k, s, d in cond if k == "meta" and s == 0x51]
ts = [d for t, k, s, d in cond if k == "meta" and s == 0x58][0]
ks = [d for t, k, s, d in cond if k == "meta" and s == 0x59][0]
check(ts[0] == 6 and 2 ** ts[1] == 8, "time signature 6/8")
check(struct.unpack("b", ks[:1])[0] == -4, "key signature 4 flats")
vn, pn = midi_notes(vio), midi_notes(pno)
check(all(55 <= n[2] <= 103 for n in vn), "violin range G3..G7")
check(all(21 <= n[2] <= 108 for n in pn), "piano range A0..C8")
check(all(1 <= e[3][1] <= 127 for e in pno + vio if e[1] == "msg" and e[2] >> 4 == 9), "velocities in range")


def seconds(tick):
    s, pt, pb = 0.0, 0, tempos[0][1]
    for t, bpm in tempos:
        if t >= tick:
            break
        s += (t - pt) / ppq * 60 / pb
        pt, pb = t, bpm
    return s + (tick - pt) / ppq * 60 / pb


end = max(n[0] + n[1] for n in vn + pn)
dur = seconds(end)
print(f"MIDI: ppq={ppq} violin={len(vn)} piano={len(pn)} length={dur:.1f}s ({int(dur // 60)}:{int(dur % 60):02d}), "
      f"{len(tempos)} tempo events, bars={end / (ppq * 3):.1f}")
check(120 <= dur <= 210, "length 2:00-3:30")

root = etree.parse(str(D / f"{BASE}.musicxml")).getroot()
check(root.tag == "score-partwise" and root.get("version") == "4.0", "score-partwise 4.0")
parts = root.findall("part")
check(len(parts) == 2, "two parts")
TYPE_DIV = {"whole": 32, "half": 16, "quarter": 8, "eighth": 4, "16th": 2, "32nd": 1}
STEP_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
xml_notes = {"P1": [], "P2": []}
for p in parts:
    pid = p.get("id")
    ms = p.findall("measure")
    check([int(m.get("number")) for m in ms] == list(range(1, NB + 1)), f"{pid}: {NB} consecutive measures")
    check(int(p.find("measure/attributes/divisions").text) == DIVS, "divisions")
    check(p.find("measure/attributes/time/beats").text == "6" and p.find("measure/attributes/time/beat-type").text == "8",
          "XML time 6/8")
    check(p.find("measure/attributes/key/fifths").text == "-4", "XML key -4")
    for m in ms:
        n_ = int(m.get("number"))
        base = (n_ - 1) * BARDIV
        cur = {}        # (staff-voice) -> cursor, reset at <backup>
        last = {}
        tot = Counter()
        for e in m:
            if e.tag == "backup":
                cur = {}
                continue
            if e.tag != "note":
                continue
            v = int(e.find("voice").text)
            d = int(e.find("duration").text)
            if e.find("chord") is None:
                tot[v] += d
            if e.find("rest") is not None:
                if e.find("rest").get("measure") == "yes":
                    check(d == BARDIV, f"{pid} m{n_} measure-rest length")
                cur[v] = cur.get(v, 0) + d
                continue
            typ, dots = e.find("type").text, len(e.findall("dot"))
            check(TYPE_DIV[typ] * (2 - 0.5 ** dots) == d, f"{pid} m{n_}: type {typ}/{dots} dots != dur {d}")
            is_chord = e.find("chord") is not None
            st = last[v] if is_chord else cur.get(v, 0)
            if not is_chord:
                last[v] = st
                cur[v] = st + d
            else:
                check(d == last.get("d" + str(v)), f"{pid} m{n_}: chord note duration differs")
            if not is_chord:
                last["d" + str(v)] = d
            midi = 12 * (int(e.findtext("pitch/octave")) + 1) + STEP_PC[e.findtext("pitch/step")] + int(e.findtext("pitch/alter") or 0)
            xml_notes[pid].append((base + st, d, midi))
        for v, t in tot.items():
            check(t == BARDIV, f"{pid} m{n_} voice {v} sums to {t}, expected {BARDIV}")
    sl = Counter(s.get("type") for s in p.iter("slur"))
    check(sl["start"] == sl["stop"], f"{pid} slurs balanced {dict(sl)}")
art = Counter(a.tag for a in root.iter("articulations") for a in a)
print("articulations:", dict(art), "| dynamics:", len(list(root.iter("dynamics"))),
      "| wedges:", len(list(root.iter("wedge"))), "| tempo marks:", len(list(root.iter("sound"))))
check(art["staccato"] > 100 and art["accent"] > 5 and art["tenuto"] > 5, "staccato/accent/tenuto present")
check(len([w for w in root.iter("wedge") if w.get("type") == "crescendo"]) >= 8, "crescendi present")

FINAL = 79 * 3          # last bar start (quarters): the final chord is deliberately rolled


def norm(t):
    q = t / ppq
    return float(FINAL) if q >= FINAL else round(q * DIVS) / DIVS


vm = Counter((norm(t), n) for t, d, n, c in vn)
vx = Counter((float(FINAL) if t / DIVS >= FINAL else t / DIVS, n) for t, d, n in xml_notes["P1"])
check(vm == vx, "violin: MIDI pitches/onsets == MusicXML")
pm = Counter((norm(t), n) for t, d, n, c in pn)
px = Counter((float(FINAL) if t / DIVS >= FINAL else t / DIVS, n) for t, d, n in xml_notes["P2"])
check(pm == px, "piano: MIDI pitches/onsets == MusicXML")
if pm != px:
    print(list((pm - px).items())[:5], list((px - pm).items())[:5])
print(f"MusicXML: violin={len(xml_notes['P1'])} piano={len(xml_notes['P2'])}")
print("RESULT:", "ALL CHECKS PASSED" if not errors else f"{len(errors)} PROBLEM(S)")
sys.exit(1 if errors else 0)
