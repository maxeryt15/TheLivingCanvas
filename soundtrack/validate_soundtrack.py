"""Independent validation: re-parses the written .mid and .musicxml from disk (does not reuse the generator's
note model) and checks structure, durations, ranges and that both files contain the same notes."""
import struct
import sys
from collections import Counter
from pathlib import Path

from lxml import etree

D = Path(__file__).parent
errors = []


def check(cond, msg):
    if not cond:
        errors.append(msg)
        print("FAIL:", msg)


# ------------------------------------------------------------ MIDI
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
    check(ln == 6 and fmt == 1, "MIDI format 1")
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
        check(ev[-1][1:3] == ("meta", 0x2F), "track ends with End-of-Track")
        tracks.append(ev)
    check(i == len(b), "no trailing bytes in MIDI")
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
    check(not open_, "hanging notes at end of MIDI")
    return sorted(out)


ppq, tracks = parse_midi(D / "the_garden_remembers.mid")
cond, vio, pno = tracks
tempos = [(t, 60_000_000 / int.from_bytes(d, "big")) for t, k, s, d in cond if k == "meta" and s == 0x51]
ts = [d for t, k, s, d in cond if k == "meta" and s == 0x58][0]
ks = [d for t, k, s, d in cond if k == "meta" and s == 0x59][0]
check(ts[0] == 4 and 2 ** ts[1] == 4, "time signature is 4/4")
check(struct.unpack("b", ks[:1])[0] == -5, "key signature = 5 flats")
vn_prog = [d for t, k, s, d in vio if k == "msg" and s >> 4 == 0xC]
pn_prog = [d for t, k, s, d in pno if k == "msg" and s >> 4 == 0xC]
check(vn_prog == [(40,)], "violin program (GM 41 = index 40)")
check(pn_prog == [(0,)], "piano program (GM 1 = index 0)")
vn, pn = midi_notes(vio), midi_notes(pno)
check(all(55 <= n[2] <= 103 for n in vn), "violin within G3..G7 (playable)")
check(all(21 <= n[2] <= 108 for n in pn), "piano within A0..C8")
# duration in seconds with the tempo map
def seconds(tick):
    s, prev_t, prev_bpm = 0.0, 0, tempos[0][1]
    for t, bpm in tempos:
        if t >= tick:
            break
        s += (t - prev_t) / ppq * 60 / prev_bpm
        prev_t, prev_bpm = t, bpm
    return s + (tick - prev_t) / ppq * 60 / prev_bpm
end = max(n[0] + n[1] for n in vn + pn)
dur = seconds(end)
print(f"MIDI: tracks={len(tracks)} ppq={ppq} violin notes={len(vn)} piano notes={len(pn)} length={dur:.1f}s "
      f"({int(dur // 60)}:{int(dur % 60):02d}) tempos={[(t // ppq // 4 + 1, round(b)) for t, b in tempos]}")
check(120 <= dur <= 180, "length between 2:00 and 3:00")

# ------------------------------------------------------------ MusicXML
tree = etree.parse(str(D / "the_garden_remembers.musicxml"))
root = tree.getroot()
check(root.tag == "score-partwise" and root.get("version") == "4.0", "score-partwise 4.0")
parts = root.findall("part")
check([p.get("id") for p in parts] == ["P1", "P2"], "two parts")
check({s.get("id") for s in root.findall("part-list/score-part")} == {"P1", "P2"}, "part-list ids")
TYPE_DIV = {"whole": 16, "half": 8, "quarter": 4, "eighth": 2, "16th": 1}
STEP_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
xml_notes = {"P1": [], "P2": []}
for p in parts:
    pid = p.get("id")
    ms = p.findall("measure")
    check([int(m.get("number")) for m in ms] == list(range(1, 41)), f"{pid}: 40 consecutive measures")
    divisions = int(p.find("measure/attributes/divisions").text)
    check(divisions == 4, "divisions=4")
    for m in ms:
        n_ = int(m.get("number"))
        base = (n_ - 1) * 16
        pos = {}                      # voice -> cursor
        last_start = {}
        for e in m:
            if e.tag == "note":
                v = int(e.find("voice").text)
                d = int(e.find("duration").text)
                if e.find("rest") is not None:
                    check(d == 16, f"{pid} m{n_} measure rest = 16")
                    pos[v] = pos.get(v, 0) + d
                    continue
                typ = e.find("type").text
                dots = len(e.findall("dot"))
                expect = TYPE_DIV[typ] * (2 - 0.5 ** dots)
                check(expect == d, f"{pid} m{n_}: type/dots ({typ},{dots}) != duration {d}")
                is_chord = e.find("chord") is not None
                st = last_start[v] if is_chord else pos.get(v, 0)
                if not is_chord:
                    last_start[v] = st
                    pos[v] = st + d
                pc = STEP_PC[e.findtext("pitch/step")] + int(e.findtext("pitch/alter") or 0)
                midi = 12 * (int(e.findtext("pitch/octave")) + 1) + pc
                xml_notes[pid].append((base + st, d, midi))
            elif e.tag == "backup":
                d = int(e.find("duration").text)
                for v in pos:
                    pos[v] = pos[v]
                # backup applies to the current voice cursor: staff 2 restarts at the bar start
                pos = {}
        if pid == "P1":
            check(pos.get(1) == 16, f"P1 m{n_}: bar length {pos.get(1)} != 16")
    # slurs balanced
    st = Counter(s.get("type") for s in p.iter("slur"))
    check(st["start"] == st["stop"], f"{pid} slurs balanced {dict(st)}")
# piano voices each sum to 16 per measure (checked separately because backup resets cursors)
for m in parts[1].findall("measure"):
    tot = Counter()
    for e in m.findall("note"):
        if e.find("chord") is None:
            tot[int(e.find("voice").text)] += int(e.find("duration").text)
    check(tot[1] == 16 and tot[5] == 16, f"P2 m{m.get('number')}: voices {dict(tot)}")
check(len(list(parts[0].iter("dynamics"))) > 0 and len(list(parts[1].iter("dynamics"))) > 0, "dynamics present")
check(len([w for w in root.iter("words") if "maj7" in (w.text or "") or "m7" in (w.text or "")]) > 20, "chord labels present")
check(len(list(root.iter("articulations"))) > 0, "articulations present")
check(len(list(root.iter("sound"))) >= 4, "tempo marks present")

# ------------------------------------------------------------ MIDI == MusicXML (pitch + onset in quarter notes)
def key_midi(ns):
    return sorted((round(t / ppq, 3), n) for t, d, n, c in ns)

def key_xml(ns):
    return sorted((round(t / 4, 3), n) for t, d, n in ns)

def dropoff(lst):  # remove ms-level midi humanization of the rolled final chord for comparison
    return lst

vm = [(round(t / ppq * 4) / 4, n) for t, d, n, c in vn]
vx = [(t / 4, n) for t, d, n in xml_notes["P1"]]
check(sorted(vm) == sorted(vx), "violin: MIDI pitches/onsets == MusicXML")
FINAL = 39 * 4   # the last chord is deliberately rolled (arpeggiato): compare its onsets on the beat only
def norm(t):
    q = t / ppq
    return float(FINAL) if q >= FINAL else round(q * 4) / 4
pm = Counter((norm(t), n) for t, d, n, c in pn)
px = Counter((float(FINAL) if t / 4 >= FINAL else t / 4, n) for t, d, n in xml_notes["P2"])
check(pm == px, "piano: MIDI pitches/onsets == MusicXML")
print(f"MusicXML: violin notes={len(xml_notes['P1'])} piano notes={len(xml_notes['P2'])}")
print("RESULT:", "ALL CHECKS PASSED" if not errors else f"{len(errors)} PROBLEM(S)")
sys.exit(1 if errors else 0)
