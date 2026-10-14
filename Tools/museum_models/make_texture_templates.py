"""Genera el PACK DE PLANTILLAS DE TEXTURA (estilo libro para colorear) del museo de The Living Canvas.

Uso (desde la raiz del proyecto):  python Tools/museum_models/make_texture_templates.py

Salida (se borra y recrea en cada ejecucion):
  ArtSource/Museum/TextureTemplates/{krita,colorear,blender,preview,lienzos}  + README.md + inventario.csv
  ArtSource/Museum/TheLivingCanvas_Museum_TexturePack.zip   (rutas internas "TextureTemplates/...")

Los lienzos (cuadros) se leen como TEXTO de museum_int.py (art_slot(...) y WING_ART), sin importar Blender.
"""
import csv
import math
import os
import re
import shutil
import sys
import textwrap
import zipfile
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "Tools"))
from make_prototype_textures import FONT, FONT_S, new_layer, arrow, guide_common, write_ora  # noqa: E402

OUT = os.path.join(ROOT, "ArtSource", "Museum", "TextureTemplates")
ZIP = os.path.join(ROOT, "ArtSource", "Museum", "TheLivingCanvas_Museum_TexturePack.zip")
INT_PY = os.path.join(HERE, "museum_int.py")
EXPORT_DIR = "Assets/_TheLivingCanvas/Art/Textures/Painted/Museum/"
PAINT_DIR = "Assets/_TheLivingCanvas/Art/Textures/Paintings/"
LAYER_GUIDE = "GUIDE (ocultar al exportar)"
LAYER_LINE = "LINEART (libro para colorear)"
NEUTRAL = "#DDD6CA"
UV_FACTS = ("UVs reales por proyeccion de caja: arquitectura 1 rep = 2 m; props y mobiliario 1 rep = 1 m; "
            "terreno exterior 1 rep = 4 m.")
ART_NOTE = ("Pintura: trazos del MISMO tono del material (varia luz/saturacion, no el tono), solapados sin huecos, "
            "sin remolinos tipo Van Gogh; siguen la forma.")


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------- dibujo de lineas con wrap
class D:
    """Lienzo L (255 blanco, 0 tinta). Si tile=True, todo lo que cruza un borde se repite en el opuesto."""

    def __init__(self, w, h, tile):
        self.w, self.h, self.tile = w, h, tile
        self.img = Image.new("L", (w, h), 255)
        self.d = ImageDraw.Draw(self.img)

    def _offs(self, pts):
        if not self.tile:
            return [(0, 0)]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        res = []
        for dx in (-self.w, 0, self.w):
            for dy in (-self.h, 0, self.h):
                if max(xs) + dx >= -4 and min(xs) + dx <= self.w + 4 and max(ys) + dy >= -4 and min(ys) + dy <= self.h + 4:
                    res.append((dx, dy))
        return res

    def line(self, pts, wd=2, closed=False):
        pts = [(float(x), float(y)) for x, y in pts]
        if closed:
            pts = pts + [pts[0]]
        for dx, dy in self._offs(pts):
            self.d.line([(x + dx, y + dy) for x, y in pts], fill=0, width=wd, joint="curve")

    def dashed(self, pts, on=12, off=8, wd=2):
        """Linea discontinua a lo largo de una polilinea."""
        acc, drawing, cur = 0.0, True, [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            seg = math.hypot(b[0] - a[0], b[1] - a[1])
            t = 0.0
            while t < seg:
                lim = (on if drawing else off) - acc
                step = min(lim, seg - t)
                t += step
                acc += step
                p = (a[0] + (b[0] - a[0]) * t / seg, a[1] + (b[1] - a[1]) * t / seg)
                if drawing:
                    cur.append(p)
                if acc >= (on if drawing else off) - 1e-6:
                    if drawing and len(cur) > 1:
                        self.line(cur, wd)
                    drawing = not drawing
                    acc = 0.0
                    cur = [p]
        if drawing and len(cur) > 1:
            self.line(cur, wd)

    def dot(self, x, y, r, wd=1):
        self.line(circle(x, y, r, r, n=10), wd, closed=True)


def circle(cx, cy, rx, ry, rot=0.0, n=28):
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out


def chaikin(pts, it=2, closed=True):
    for _ in range(it):
        new, n = [], len(pts)
        for i in range(n if closed else n - 1):
            p, q = pts[i], pts[(i + 1) % n]
            new += [(0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]), (0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1])]
        pts = new if closed else [pts[0]] + new + [pts[-1]]
    return pts


def blob(rng, cx, cy, rx, ry, n=7, jit=0.25, rot=0.0):
    """Contorno cerrado irregular y redondeado (n=4 -> cuadrilatero redondeado)."""
    c, s = math.cos(rot), math.sin(rot)
    base = rng.uniform(0, 6.283)
    pts = []
    for i in range(n):
        a = base + 2 * math.pi * i / n
        k = 1 + rng.uniform(-jit, jit)
        x, y = rx * k * math.cos(a), ry * k * math.sin(a)
        pts.append((cx + x * c - y * s, cy + x * s + y * c))
    return chaikin(pts, 3, True)


def wobble(rng, p0, p1, amp=2.0, step=24):
    n = max(2, int(math.hypot(p1[0] - p0[0], p1[1] - p0[1]) / step))
    nx, ny = -(p1[1] - p0[1]), p1[0] - p0[0]
    L = math.hypot(nx, ny) or 1
    nx, ny = nx / L, ny / L
    pts = []
    for i in range(n + 1):
        t = i / n
        o = rng.uniform(-amp, amp) if 0 < i < n else 0
        pts.append((p0[0] + (p1[0] - p0[0]) * t + nx * o, p0[1] + (p1[1] - p0[1]) * t + ny * o))
    return pts


def curve(p0, ang, length, bend, n=14):
    """Trazo curvo desde p0 con angulo ang (rad), longitud y curvatura lateral."""
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for i in range(n + 1):
        t = i / n
        u, v = t * length, bend * math.sin(math.pi * t) * length
        out.append((p0[0] + u * ca - v * sa, p0[1] + u * sa + v * ca))
    return out


def half_leaf(v):
    return math.sin(math.pi * min(max(v, 0), 1) ** 0.8) ** 0.8


def leaf_pts(cx, cy, ang, L, Wd, n=22):
    ca, sa = math.cos(ang), math.sin(ang)
    side_a, side_b = [], []
    for i in range(n + 1):
        v = i / n
        u, h = v * L, half_leaf(v) * Wd / 2
        side_a.append((cx + u * ca - h * sa, cy + u * sa + h * ca))
        side_b.append((cx + u * ca + h * sa, cy + u * sa - h * ca))
    return side_a + side_b[::-1][1:]


def leaf_fishbone(g, cx, cy, ang, L, Wd, nv=5, wd=2):
    g.line(leaf_pts(cx, cy, ang, L, Wd), wd, closed=True)
    ca, sa = math.cos(ang), math.sin(ang)
    g.line([(cx, cy), (cx + L * 0.97 * ca, cy + L * 0.97 * sa)], wd)
    for k in range(nv):
        v = 0.15 + 0.7 * k / max(nv - 1, 1)
        for sgn in (1, -1):
            v2 = min(v + 0.2, 0.97)
            u1, u2 = v * L, v2 * L
            h2 = half_leaf(v2) * Wd / 2 * 0.85 * sgn
            g.line([(cx + u1 * ca, cy + u1 * sa), (cx + u2 * ca - h2 * sa, cy + u2 * sa + h2 * ca)], 1)


# ---------------------------------------------------------------- familias (line art)
def f_plaster(g, rng, px, ppm):
    for _ in range(46):
        r = rng.uniform(0.075, 0.15) * ppm
        g.line(blob(rng, rng.uniform(0, px), rng.uniform(0, px), r * rng.uniform(0.9, 1.3), r * rng.uniform(0.7, 1.0), 4, 0.18, rng.uniform(0, 6.28)), 2, True)
    for _ in range(30):
        ang = math.radians(75 + rng.uniform(-12, 12))
        L = rng.uniform(0.15, 0.3) * ppm
        g.dashed(curve((rng.uniform(0, px), rng.uniform(0, px)), ang, L, rng.uniform(-0.1, 0.1)), 14, 9, 2)


def f_stone(g, rng, px, ppm):
    rows = 7
    rh = px / rows
    for r in range(rows):
        y0 = r * rh
        g.line(wobble(rng, (0, y0), (px, y0), 2, 40), 3)
        start = rng.uniform(0, 0.5 * ppm)
        cuts = [start]
        while cuts[-1] - start < px - 0.4 * ppm:
            cuts.append(cuts[-1] + rng.uniform(0.4, 0.7) * ppm)
        cuts[-1] = start + px  # cierra la hilada exactamente
        for i, x in enumerate(cuts[:-1]):
            g.line(wobble(rng, (x, y0), (x + rng.uniform(-3, 3), y0 + rh), 2, 30), 3)
            if rng.random() < 0.3:
                xm = (x + cuts[i + 1]) / 2
                for k in range(rng.integers(5, 9)):
                    g.line([(xm - 30 + k * 9, y0 + rh * 0.65), (xm - 10 + k * 9, y0 + rh * 0.3)], 1)


def f_roof(g, rng, px, ppm):
    cols, rows = 8, 6
    tw, th = px / cols, px / rows
    for r in range(rows):
        off = (r % 2) * tw / 2
        for c in range(cols):
            x0, y0 = c * tw + off, r * th
            s = tw * 0.25
            arc = [(x0 + tw / 2 - tw / 2 * math.cos(a), y0 + th - s + s * math.sin(a) * 1.0) for a in np.linspace(0, math.pi, 14)]
            g.line([(x0, y0), (x0, y0 + th - s)] + arc + [(x0 + tw, y0 + th - s), (x0 + tw, y0)], 3)
            for fx in (0.3, 0.5, 0.7):
                g.line(curve((x0 + tw * fx, y0 + th * 0.2), math.pi / 2, th * 0.55, rng.uniform(-0.03, 0.03), 6), 1)


def f_planks(g, rng, px, ppm):
    n = 10
    bh = px / n
    for i in range(n):
        y0 = i * bh
        g.line(wobble(rng, (0, y0), (px, y0), 1.5, 40), 3)
        for _ in range(rng.integers(1, 3)):
            x = rng.uniform(0, px)
            g.line([(x, y0), (x + rng.uniform(-2, 2), y0 + bh)], 3)
        for k in range(5):
            yy = y0 + bh * (k + 1) / 6
            amp, nn, ph = rng.uniform(1, 4), int(rng.integers(1, 4)), rng.uniform(0, 6.28)
            g.line([(x, yy + amp * math.sin(2 * math.pi * nn * x / px + ph)) for x in np.linspace(0, px, 70)], 1)
    for _ in range(4):
        cx, cy = rng.uniform(0, px), (int(rng.integers(0, n)) + 0.5) * bh
        for k in (1.0, 0.65, 0.35):
            g.line(circle(cx, cy, 22 * k, 12 * k), 2, True)


def f_grain(g, rng, px, ppm):
    for i in range(44):
        y = (i + rng.uniform(0, 1)) * px / 44
        a1, a2 = rng.uniform(2, 9), rng.uniform(1, 4)
        n1, n2 = int(rng.integers(1, 3)), int(rng.integers(2, 5))
        p1, p2 = rng.uniform(0, 6.28, 2)
        x0 = rng.uniform(0, px)
        ln = rng.uniform(0.5, 1.0) * px
        g.line([(x0 + t, y + a1 * math.sin(2 * math.pi * n1 * (x0 + t) / px + p1) + a2 * math.sin(2 * math.pi * n2 * (x0 + t) / px + p2)) for t in np.linspace(0, ln, 90)], 2)
    for _ in range(5):  # arcos de catedral
        cx, cy = rng.uniform(0, px), rng.uniform(0, px)
        for k in range(6):
            w, a = 70 + k * 28, 46 - k * 3
            g.line([(cx + t, cy + k * 15 - a * (1 - (t / w) ** 2)) for t in np.linspace(-w, w, 40)], 2)
    for _ in range(3):  # nudos
        cx, cy = rng.uniform(0, px), rng.uniform(0, px)
        for k in (1.0, 0.7, 0.4):
            g.line(circle(cx, cy, 38 * k, 17 * k), 2, True)


def f_painted(g, rng, px, ppm):
    n = 8
    bw = px / n
    for i in range(n):
        x = i * bw
        g.line([(x - 2, 0), (x - 2, px)], 3)
        g.line([(x + 3, 0), (x + 3, px)], 2)
        for k in range(3):
            xx, y0 = x + bw * (k + 1) / 4, rng.uniform(0, px)
            g.line([(xx + 2.5 * math.sin(t / 60.0 + k), y0 + t) for t in np.linspace(0, rng.uniform(200, 520), 40)], 2)
    for _ in range(14):
        x = (int(rng.integers(0, n)) + rng.choice([0.08, 0.92])) * bw
        r = rng.uniform(8, 18)
        g.line(blob(rng, x, rng.uniform(0, px), r, r * rng.uniform(0.6, 1.2), 6, 0.35), 2, True)


def f_hall(g, rng, px, ppm):
    n = 5
    ts = px / n
    for i in range(n):
        g.line([(0, i * ts), (px, i * ts)], 3)
        g.line([(i * ts, 0), (i * ts, px)], 3)
    for i in range(n):
        for j in range(n):
            cx, cy = i * ts, j * ts
            for r in (36, 24):
                g.line([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], 2, True)
            for k in range(3):
                g.line(curve((cx + ts * 0.3, cy + ts * (0.3 + 0.15 * k)), -0.5, ts * 0.3, 0.1, 8), 1)


def f_flag(g, rng, px, ppm):
    for _ in range(30):
        r = rng.uniform(0.15, 0.35) * ppm
        g.line(blob(rng, rng.uniform(0, px), rng.uniform(0, px), r, r * rng.uniform(0.5, 0.9), 7, 0.3, rng.uniform(0, 6.28)), 2, True)
    for _ in range(220):
        g.dot(rng.uniform(0, px), rng.uniform(0, px), rng.uniform(1.5, 4))
    for _ in range(30):
        g.line(curve((rng.uniform(0, px), rng.uniform(0, px)), rng.uniform(0, 6.28), rng.uniform(15, 40), 0.1, 6), 1)


def f_concrete(g, rng, px, ppm):
    for _ in range(22):
        cx, cy, r = rng.uniform(0, px), rng.uniform(0, px), rng.uniform(0.3, 0.8) * ppm
        a0, sp = rng.uniform(0, 6.28), math.radians(rng.uniform(60, 120))
        g.line([(cx + r * math.cos(a0 + sp * t), cy + r * math.sin(a0 + sp * t)) for t in np.linspace(0, 1, 24)], 2)
    for _ in range(5):
        x, y, a = rng.uniform(0, px), rng.uniform(0, px), rng.uniform(0, 6.28)
        pts = [(x, y)]
        for _ in range(20):
            a += rng.uniform(-0.5, 0.5)
            x, y = x + 11 * math.cos(a), y + 11 * math.sin(a)
            pts.append((x, y))
        g.line(pts, 1)


def f_ceramic(g, rng, px, ppm):
    for _ in range(6):
        L, W = rng.uniform(200, 350), rng.uniform(10, 22)
        g.line(leaf_pts(rng.uniform(0, px), rng.uniform(0, px), math.radians(-20 + rng.uniform(-8, 8)), L, W), 2, True)
    for _ in range(5):
        x, y, L = rng.uniform(0, px), rng.uniform(0, px), rng.uniform(40, 110)
        g.line([(x, y), (x, y + L)], 2)
        g.line(circle(x, y + L + 6, 5, 8), 2, True)


def f_metal(g, rng, px, ppm):
    for _ in range(100):
        x, y, L = rng.uniform(0, px), rng.uniform(0, px), rng.uniform(60, 240)
        g.line([(x, y), (x + L, y + rng.uniform(-1, 1))], 1)
    for _ in range(6):
        cx, cy = rng.uniform(0, px), rng.uniform(0, px)
        for k in (1.0, 0.55):
            g.line(circle(cx, cy, 30 * k, 20 * k, rng.uniform(0, 3)), 2, True)
    for _ in range(7):
        cx, cy, r = rng.uniform(0, px), rng.uniform(0, px), rng.uniform(10, 22)
        g.line(blob(rng, cx, cy, r, r * 0.8, 7, 0.35), 2, True)
        for _ in range(4):
            g.dot(cx + rng.uniform(-r, r) * 1.6, cy + rng.uniform(-r, r) * 1.6, 2)


def f_gilded(g, rng, px, ppm):
    cell = 32
    for i in range(px // cell):
        for j in range(px // cell):
            cx, cy = (i + 0.5) * cell + rng.uniform(-3, 3), (j + 0.5) * cell + rng.uniform(-3, 3)
            g.line(circle(cx, cy, 17, 17, math.radians(45 + rng.uniform(-6, 6)), 4), 1, True)
    for _ in range(14):
        x, y = rng.uniform(0, px), rng.uniform(0, px)
        g.line(wobble(rng, (x, y), (x + rng.uniform(150, 300), y + rng.uniform(-3, 3)), 1.5, 30), 1)


def f_fabric(g, rng, px, ppm):
    sp = 16
    for i in range(px // sp):
        ph = (i % 2) * 8
        g.dashed([(-ph, i * sp + 8), (px + 20, i * sp + 8)], 12, 4, 1)
        g.dashed([(i * sp + 8, -ph), (i * sp + 8, px + 20)], 12, 4, 1)
    for _ in range(4):
        x, n, ph = rng.uniform(0, px), int(rng.integers(1, 3)), rng.uniform(0, 6.28)
        g.line([(x + 6 * math.sin(2 * math.pi * n * y / px + ph), y) for y in np.linspace(0, px, 60)], 3)


def f_rug(g, rng, px, ppm):
    c = px / 2
    for r in (500, 470, 400, 392, 330, 300, 200):
        g.line(circle(c, c, r, r, n=120), 3, True)
    for i in range(28):  # motivo de hoja / voluta del borde
        a = 2 * math.pi * i / 28
        ca, sa = math.cos(a), math.sin(a)
        g.line(leaf_pts(c + 408 * ca, c + 408 * sa, a, 56, 24), 2, True)
        g.line([(c + 410 * ca, c + 410 * sa), (c + 460 * ca, c + 460 * sa)], 1)
        b = a + math.pi / 28
        g.line(circle(c + 436 * math.cos(b), c + 436 * math.sin(b), 7, 7, n=12), 2, True)
    for i in range(16):
        a = 2 * math.pi * i / 16
        g.line(leaf_pts(c + 230 * math.cos(a), c + 230 * math.sin(a), a, 60, 22), 2, True)
    for n, L, W, r0 in ((12, 150, 50, 20), (12, 100, 30, 20)):
        off = 0 if L == 150 else math.pi / 12
        for i in range(n):
            a = 2 * math.pi * i / n + off
            g.line(leaf_pts(c + r0 * math.cos(a), c + r0 * math.sin(a), a, L, W), 2, True)
    g.line(circle(c, c, 22, 22), 2, True)
    g.line(circle(c, c, 11, 11), 2, True)


def f_leaves(g, rng, px, ppm):
    for i in range(3):
        for j in range(3):
            if (i + j) % 4 == 3:
                continue
            leaf_fishbone(g, (i + 0.2) * px / 3 + rng.uniform(-20, 20), (j + 0.3) * px / 3 + rng.uniform(-20, 20),
                          rng.uniform(0, 6.28), rng.uniform(160, 200), rng.uniform(60, 80))


def f_petals(g, rng, px, ppm):
    for i in range(3):
        for j in range(2):
            cx, cy = (i + 0.5) * px / 3 + rng.uniform(-25, 25), (j + 0.5) * px / 2 + rng.uniform(-20, 20) + (i % 2) * 40
            off = rng.uniform(0, 6.28)
            for k in range(11):
                a = off + 2 * math.pi * k / 11
                g.line(leaf_pts(cx + 9 * math.cos(a), cy + 9 * math.sin(a), a, 62, 26), 2, True)
                g.line([(cx + 12 * math.cos(a), cy + 12 * math.sin(a)), (cx + 60 * math.cos(a), cy + 60 * math.sin(a))], 1)
            g.line(circle(cx, cy, 8, 8, n=14), 2, True)


def f_grass(g, rng, px, ppm):
    for _ in range(42):
        bx, by = rng.uniform(0, px), rng.uniform(0, px)
        for _ in range(int(rng.integers(9, 17))):
            g.line(curve((bx + rng.uniform(-8, 8), by), math.radians(-90 + rng.uniform(-38, 38)), rng.uniform(30, 70), rng.uniform(-0.18, 0.18), 8), 2)
    for _ in range(6):
        cx, cy, r = rng.uniform(0, px), rng.uniform(0, px), rng.uniform(50, 90)
        g.line(blob(rng, cx, cy, r, r * 0.6, 7, 0.25, rng.uniform(0, 3)), 2, True)
        for _ in range(8):
            g.dot(cx + rng.uniform(-r, r) * 0.7, cy + rng.uniform(-r, r) * 0.4, 2.5)


def f_path(g, rng, px, ppm):
    n = 6
    pts = [((i + 0.5 + rng.uniform(-0.35, 0.35)) * px / n, (j + 0.5 + rng.uniform(-0.35, 0.35)) * px / n) for i in range(n) for j in range(n)]
    ys, xs = np.mgrid[0:px, 0:px].astype(np.float32)
    best = np.full((px, px), 1e9, np.float32)
    lab = np.zeros((px, px), np.int32)
    for k, (cx, cy) in enumerate(pts):
        dx = np.abs(xs - cx)
        dx = np.minimum(dx, px - dx)
        dy = np.abs(ys - cy)
        dy = np.minimum(dy, px - dy)
        dd = dx * dx + dy * dy
        m = dd < best
        best[m] = dd[m]
        lab[m] = k
    edge = (lab != np.roll(lab, -1, 0)) | (lab != np.roll(lab, -1, 1))
    im = Image.fromarray(np.where(edge, 0, 255).astype(np.uint8), "L").filter(ImageFilter.MinFilter(3))
    g.img.paste(im, (0, 0))
    g.d = ImageDraw.Draw(g.img)
    for _ in range(40):
        g.dot(rng.uniform(0, px), rng.uniform(0, px), rng.uniform(1.5, 3))


def f_bark(g, rng, px, ppm):
    for _ in range(18):
        x, y = rng.uniform(0, px), rng.uniform(0, px)
        pts = [(x, y)]
        for _ in range(int(rng.uniform(150, 380) / 14)):
            x += rng.uniform(-3, 3)
            y += 14
            pts.append((x, y))
        g.line(pts, 2)
        if rng.random() < 0.5:
            k = int(rng.integers(1, len(pts)))
            g.line([pts[k], (pts[k][0] + rng.choice([-1, 1]) * 18, pts[k][1] + 30)], 1)
    for _ in range(26):
        x, y = rng.uniform(0, px), rng.uniform(0, px)
        g.line([(x + 2.5 * math.sin(t / 40.0 + x), y + t) for t in np.linspace(0, rng.uniform(120, 300), 30)], 1)


def f_glass(g, rng, px, ppm):
    for x0, w in ((60, 80), (230, 50), (400, 34)):  # bandas diagonales a 45 grados (encajan al repetir)
        for off in (0, w):
            g.line([(x0 + off - px, -px), (x0 + off + 2 * px, 2 * px)], 2)
        g.line([(x0 + w / 2 - px, -px), (x0 + w / 2 + 2 * px, 2 * px)], 1)


def f_paper(g, rng, px, ppm):
    sp = 12
    for i in range(px // sp):
        ph = (i % 2) * 6
        g.dashed([(-ph, i * sp + 6), (px + 12, i * sp + 6)], 9, 3, 1)
        g.dashed([(i * sp + 6, -ph), (i * sp + 6, px + 12)], 9, 3, 1)


# nombre, px, tile, m/rep, materiales, donde, trazo, base, tenida, flechas(grados, 0=derecha 90=abajo), fn
FAMILIES = [
    ("Plaster", 1024, True, 2, "M_Museum_Plaster, M_Interior_Wallpaper, M_Interior_Ceiling, M_Wall_Ochre, M_Wall_Cerulean, M_Wall_Terracotta, M_Wall_Olive, M_Wall_Grey, M_Wall_White, M_Wall_Mint, M_Wall_Rose, M_Wall_Coral",
     "fachada, todas las paredes y techos interiores, volumenes de galeria de color",
     "parches suaves de llana que se solapan (15-30 cm), flechas discontinuas casi diagonales (~75 grados)", None, True, [75, 75, 75], f_plaster),
    ("Stone_Blocks", 1024, True, 2, "M_Museum_Stone", "zocalo, dovelas/claves de ventanas, piedra de puerta, escultura del gato",
     "hiladas de sillares: filas de 0.3 m, bloques de 0.4-0.7 m a soga y tizon; trazos de cincel en algunos bloques", "#747983", False, [0, 0, 0], f_stone),
    ("Roof_Tiles", 1024, True, 2, "M_Museum_Roof, M_Museum_AwningA", "tejado, buhardillas, toldos",
     "hileras de tejas de barro con festoneado (0.25 m x 0.33 m), al tresbolillo; los trazos bajan por cada teja", "#A85F47", False, [90, 90, 90], f_roof),
    ("Wood_Planks", 1024, True, 2, "M_Interior_FloorWood", "suelos de las galerias",
     "tablas de 0.2 m en una sola direccion, juntas a tope alternadas; vetas a lo largo, un par de nudos", "#9A6E4A", False, [0, 0, 0], f_planks),
    ("Wood_Grain", 1024, True, 1, "M_Museum_Wood, M_Museum_WoodDark", "muebles, marcos de ventanas/puertas, bancos, peldanos, zocalos de pedestal, caballetes",
     "vetas largas y onduladas en un solo eje, con arcos de catedral y nudos ocasionales (clara y calida: TENIDA)", None, True, [0, 0, 0], f_grain),
    ("Painted_Boards", 1024, True, 1, "M_Museum_Shutter, M_Museum_Door, M_Interior_Wainscot, M_Sign_Board", "contraventanas, puerta principal, paneles de friso, carteles",
     "tablas verticales de 0.12 m con ranura en V; trazos largos verticales; unos pocos descascarillados", "#65785A", False, [90, 90, 90], f_painted),
    ("Floor_Tiles_Hall", 1024, True, 2, "M_Interior_FloorTile", "suelos de hall, hueco de escalera, aseos y vestibulo",
     "baldosas cuadradas de 0.4 m con juntas de 4 mm y un rombo pequeno en cada esquina de 4 baldosas; trazos de esmalte dentro", "#8FA3A8", False, [-30, -30, -30], f_hall),
    ("Flagstones", 1024, True, 2, "M_Floor_StoneA, M_Floor_StoneB", "suelo de la Galeria VII (la geometria ya trae losas de 0.8 x 0.5 m)",
     "piedra moteada sutil: manchas suaves irregulares y poros finos. SIN juntas (ya las pone la geometria)", "#CDBDA3", False, [20, 20, 20], f_flag),
    ("Concrete", 512, True, 2, "M_Interior_Concrete, M_Floor_Dark", "sala de mantenimiento, losas, huecos de sombra",
     "arcos de llana y alguna grieta fina", "#7B7D82", False, [30, 30, 30], f_concrete),
    ("Ceramic_Glaze", 512, True, 1, "M_Ceramic", "inodoros, lavabos, azulejos de aseos, jarrones",
     "esmalte liso: unos pocos brillos largos y gotas; clara", "#F0E8D8", False, [-20, -20, -20], f_ceramic),
    ("Metal", 512, True, 1, "M_Museum_Metal, M_Iron, M_Hatch_Metal, M_Track_White, M_Frame_Silver", "radiadores, barandillas, escotilla, railes de luz, taquillas, marcos plateados",
     "cepillado en horizontal con alguna abolladura o mancha de oxido", "#4A4F5A", False, [0, 0, 0], f_metal),
    ("Gilded", 512, True, 1, "M_Museum_Brass, M_Frame_Gold", "marcos dorados, tiradores de laton, bisagras, postes, arana de luces",
     "hojas de oro cuadradas (6 cm) algo solapadas, con trazos de bruñido a lo largo", "#C49A3A", False, [0, 0, 0], f_gilded),
    ("Fabric", 512, True, 1, "M_Fabric_Blue, M_Fabric_Olive, M_Fabric_Mustard, M_Rug_Terracotta, cortinas (M_Paper, M_Flower_White como color)", "cojines de banco, cortinas, cuerda de poste, anillos de alfombra",
     "tejido en cuadricula cruzada + pliegues verticales", None, True, [90, 90, 90], f_fabric),
    ("Rug_Hall", 1024, False, 0, "alfombra del hall (ahora M_Fabric_Blue / M_Rug_Terracotta / M_Fabric_Mustard en anillos)", "hall",
     "medallon circular: anillo-borde con motivo repetido de hojas/volutas, campo medio y roseta central", "#A85F47", False, [], f_rug),
    ("Leaves", 512, True, 1, "M_Plant_Leaf, M_Plant_LeafLight, M_Leaf_Dark, M_Ivy_Light, M_Leaf_Sage", "plantas de interior, hiedra, follaje del jardin",
     "patron repetido de hojas con nervios en espina de pez; los trazos siguen los nervios", "#65785A", False, [-45, -45, -45], f_leaves),
    ("Petals", 512, True, 1, "M_Flower_Yellow, M_Flower_Rose, M_Flower_Iris, M_Flower_White, M_Flower_Lavender, M_Flower_Geranium, M_Sunflower_Disc", "flores del jardin, girasoles",
     "trazos de petalos radiales desde pequenos centros repartidos", "#D4A72C", False, [-30, 40, 110], f_petals),
    ("Grass_Ground", 1024, True, 4, "M_Ground_Grass, M_Ground_Earth, M_Soil", "cesped del jardin, parterres, tierra de macetas",
     "matas de trazos cortos direccionales de hierba y algun parche de tierra", "#6E8157", False, [-90, -75, -105], f_grass),
    ("Path_Stone", 1024, True, 2, "M_Path_Stone, M_Path_StoneWarm", "caminos del jardin, escalones",
     "adoquines/losas irregulares (poligonos) con juntas", "#9A9A98", False, [20, 20, 20], f_path),
    ("Bark", 512, True, 1, "M_Bark", "troncos de cipres y del ficus",
     "fisuras y crestas verticales", "#5B4030", False, [90, 90, 90], f_bark),
    ("Glass", 512, True, 1, "M_Museum_Glass, M_Vitrine_Glass, M_Glass_Mirror", "ventanas, vitrinas, espejos",
     "2-3 bandas de reflejo diagonales (paralelogramos suaves). Nota: degradado de cielo, mas claro arriba y calido abajo", "#456F88", False, [45, 45, 45], f_glass),
    ("Paper_Canvas", 512, True, 1, "M_Paper, M_Canvas_Slot, M_Museum_AwningB, M_Picket", "etiquetas, passe-partout, lienzos en blanco, rayas de toldo, valla",
     "trama fina de lienzo en cuadricula, suave", "#EFE6CF", False, [0, 0, 0], f_paper),
]


# ---------------------------------------------------------------- guias
def fit_lines(w, header, prio):
    """header: lineas fijas; prio: lineas opcionales por prioridad. Envuelve al ancho y limita a 9 lineas."""
    width = max(20, int((w - 30) / 9.8))
    out = []
    for t in header + prio:
        out.append(textwrap.wrap(t, width) or [""])
    flat = [l for blk in out for l in blk]
    while len(flat) > 9 and len(out) > len(header):
        out.pop()
        flat = [l for blk in out for l in blk]
    return flat[:9]


def scale_bar(d, w, h, ppm):
    y = h - 34
    x = 20
    for cm, lab in ((10, "10 cm"), (50, "50 cm")):
        L = ppm * cm / 100.0
        d.rectangle([x, y, x + L, y + 8], fill=(255, 255, 0, 255), outline=(0, 0, 0, 255))
        d.text((x, y - 24), lab, fill=(255, 255, 255, 255), font=FONT_S, stroke_width=2, stroke_fill=(0, 0, 0, 255))
        x += L + 30


def make_guide(fam, px, ppm):
    name, _, tile, mpr, mats, where, stroke, base, tenida, arrows, _ = fam
    g = new_layer(px, px)
    ppm_txt = "" if not tile else " (%d px por metro)" % round(ppm)
    head = ["%dx%d px  |  %s  |  %s" % (px, px, "REPETIBLE (tecla W)" if tile else "NO repetible (diseno completo)",
                                         ("1 repeticion = %g m%s" % (mpr, ppm_txt)) if tile else "ocupa toda la alfombra")]
    exp = "Exportar: T_%s.png en %s" % (name, EXPORT_DIR)
    prio = ["Se ve en: " + where, "Trazo: " + stroke]
    # materiales: se acortan si no caben
    ml = [m.strip() for m in mats.split(",")]
    k = len(ml)
    while True:
        mt = "Materiales: " + ", ".join(ml[:k]) + (" ..." if k < len(ml) else "")
        lines = fit_lines(px, head, [mt] + prio + [exp, UV_FACTS, ART_NOTE] + (["TENIDA: pinta en gris/crema CLARO; Unity la tine con el color de cada material."] if tenida else []))
        if len(lines) <= 9 and any(l.startswith("Exportar") for l in lines) or k <= 1:
            break
        k -= 1
    # garantiza que 'Exportar' siempre aparezca: si se perdio, se reemplaza la ultima linea
    if not any("Exportar" in l for l in lines):
        lines = (lines[:8] + [exp[:int((px - 30) / 9.8)]])
    title = "T_%s  -  %s" % (name, "TILEABLE" if tile else "NO tileable")
    d = guide_common(g, px, px, title, lines)
    if name == "Rug_Hall":
        d.line([(0, px / 2), (px, px / 2)], fill=(255, 255, 0, 150), width=1)
        d.line([(px / 2, 0), (px / 2, px)], fill=(255, 255, 0, 150), width=1)
        d.text((px / 2 - 330, px - 90), "Necesita cambio de UV en el modelo para mapear como una pieza (lo hace Claude).", fill=(255, 255, 255, 255), font=FONT_S, stroke_width=2, stroke_fill=(0, 0, 0, 255))
        for a in range(0, 360, 90):
            arrow(d, px / 2 + 60 * math.cos(math.radians(a)), px / 2 + 60 * math.sin(math.radians(a)), px / 2 + 230 * math.cos(math.radians(a)), px / 2 + 230 * math.sin(math.radians(a)), (255, 255, 0, 255))
    else:
        for i, a in enumerate(arrows[:3]):
            ar = math.radians(a)
            cx, cy = px * (0.25 + 0.25 * i), px * 0.72
            arrow(d, cx - 45 * math.cos(ar), cy - 45 * math.sin(ar), cx + 45 * math.cos(ar), cy + 45 * math.sin(ar), (255, 255, 0, 255))
        scale_bar(d, px, px, ppm)
    return g


# ---------------------------------------------------------------- salidas por plantilla
def emit(out_root, sub, fname, size, base_hex, lineL, guide, title):
    """Escribe las 4 salidas de una plantilla. lineL: imagen L (255 blanco, 0 tinta)."""
    w, h = size
    base = Image.new("RGBA", size, hex2rgb(base_hex) + (255,))
    alpha = lineL.point(lambda v: 255 - v)
    lineart = Image.new("RGBA", size, (0, 0, 0, 0))
    lineart.putalpha(alpha)
    write_ora(os.path.join(out_root, sub, "krita", fname + ".ora"), size,
              [(LAYER_GUIDE, guide), (LAYER_LINE, lineart), ("paint_here", new_layer(w, h)), ("base_flat_color", base)])
    # colorear: negro sobre blanco + titulo pequeno
    col = lineL.convert("RGB")
    dd = ImageDraw.Draw(col)
    dd.rectangle([6, 6, 8 + len(title) * 10, 32], fill=(255, 255, 255), outline=(0, 0, 0))
    dd.text((10, 8), title, fill=(0, 0, 0), font=FONT_S)
    col.save(os.path.join(out_root, sub, "colorear", fname + "_colorear.png"))
    # blender: base con line art al 35 %
    bl = base.copy()
    a35 = alpha.point(lambda v: int(v * 0.35))
    ink = Image.new("RGBA", size, (0, 0, 0, 0))
    ink.putalpha(a35)
    Image.alpha_composite(bl, ink).convert("RGB").save(os.path.join(out_root, sub, "blender", fname + ".png"))
    # preview
    pv = Image.alpha_composite(Image.alpha_composite(base, lineart), guide).convert("RGB")
    pv.save(os.path.join(out_root, sub, "preview", fname + "_guia.png"))


# ---------------------------------------------------------------- lienzos: lectura de museum_int.py
def split_args(s):
    out, depth, cur, q = [], 0, "", None
    for ch in s:
        if q:
            cur += ch
            if ch == q:
                q = None
            continue
        if ch in "\"'":
            q = ch
            cur += ch
        elif ch in "([{":
            depth += 1
            cur += ch
        elif ch in ")]}":
            depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def balanced(src, i):
    """src[i] == '(' -> devuelve el texto interior hasta el parentesis que cierra."""
    depth, q, j = 0, None, i
    while j < len(src):
        ch = src[j]
        if q:
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return src[i + 1:j]
        j += 1
    return ""


def parse_slots():
    src = open(INT_PY, encoding="utf-8").read()
    slots = []
    for m in re.finditer(r"art_slot\(", src):
        if src[max(0, m.start() - 4):m.start()] == "def ":
            continue
        args = split_args(balanced(src, m.end() - 1))
        if len(args) < 8:
            continue
        try:
            w, h = float(args[6]), float(args[7])
        except ValueError:
            continue  # llamadas con variables (p.ej. el bucle de WING_ART)
        nm = re.match(r'^"([^"]*)"\s*(?:%\s*(.*))?$', args[0])
        if not nm:
            continue
        name, fmt = nm.group(1), nm.group(2)
        names = [name]
        if fmt and "%d" in name:
            names = [name % n for n in (1, 2)]
        elif fmt and "%s" in name:
            vals = re.findall(r'"([^"]+)"', fmt)
            names = [name % v for v in vals] if vals else [name]
        for n in names:
            slots.append((n, w, h))
    # WING_ART
    mm = re.search(r"WING_ART\s*=\s*\[(.*?)\n\]", src, re.S)
    if mm:
        for t in re.finditer(r"\(([^()]*)\)", mm.group(1)):
            a = split_args(t.group(1))
            if len(a) >= 9 and a[0].startswith('"'):
                slots.append(("GalleryVII_" + a[0].strip('"'), float(a[6]), float(a[7])))
    seen, uniq = set(), []
    for s in slots:
        if s[0] not in seen:
            seen.add(s[0])
            uniq.append(s)
    return uniq


CANVAS_TYPES = [  # clave, etiqueta, razon aspecto w/h, px (w,h)
    ("Paisaje_3x2", "Paisaje 3:2", 3 / 2, (1536, 1024)),
    ("Paisaje_4x3", "Paisaje 4:3", 4 / 3, (1536, 1152)),
    ("Retrato_3x4", "Retrato 3:4", 3 / 4, (1152, 1536)),
    ("Retrato_2x3", "Retrato 2:3", 2 / 3, (1024, 1536)),
    ("Cuadrado_1x1", "Cuadrado 1:1", 1.0, (1536, 1536)),
    ("Apaisado_2x1", "Apaisado 2:1", 2.0, (1536, 768)),
]
FEATURED = "GalleryV_Featured_GreyField"
FEATURED_KEY = "Lienzo_Destacado_CampoGris"


def nearest_type(w, h):
    r = w / h
    return min(CANVAS_TYPES, key=lambda t: abs(math.log(r / t[2])))


# ---------------------------------------------------------------- line art de lienzos
def hills(g, rng, W, H, y0, amp, layers):
    for k in range(layers):
        ph, n = rng.uniform(0, 6.28), rng.uniform(1.0, 2.5)
        base = y0 + k * H * 0.08
        g.line([(x, base - amp * math.sin(n * x / W * 6.283 + ph) * (1 - 0.2 * k)) for x in np.linspace(0, W, 80)], 3)


def cloud(g, rng, cx, cy, s):
    for dx, dy, r in ((-0.6, 0.1, 0.5), (0, -0.2, 0.7), (0.65, 0.1, 0.55)):
        g.line(circle(cx + dx * s, cy + dy * s, r * s, r * s * 0.7), 3, True)


def lineart_canvas(key, W, H, rng):
    g = D(W, H, False)
    if key.startswith("Paisaje"):
        hills(g, rng, W, H, H * 0.62, H * 0.07, 3)
        g.line(circle(W * 0.75, H * 0.2, H * 0.09, H * 0.09, n=40), 3, True)
        cloud(g, rng, W * 0.3, H * 0.22, H * 0.1)
        g.line([(W * 0.2, H * 0.7), (W * 0.2, H * 0.52)], 4)
        g.line(circle(W * 0.2, H * 0.46, H * 0.09, H * 0.08), 3, True)
    elif key.startswith("Retrato"):
        g.line(circle(W * 0.5, H * 0.36, W * 0.17, H * 0.14, n=40), 3, True)
        g.line([(W * 0.45, H * 0.49), (W * 0.44, H * 0.58)], 3)
        g.line([(W * 0.55, H * 0.49), (W * 0.56, H * 0.58)], 3)
        g.line([(W * 0.2, H * 0.95), (W * 0.24, H * 0.72), (W * 0.44, H * 0.58), (W * 0.56, H * 0.58), (W * 0.76, H * 0.72), (W * 0.8, H * 0.95)], 3)
        g.line(circle(W * 0.5, H * 0.3, W * 0.2, H * 0.2, n=40)[:22], 3)
    elif key.startswith("Cuadrado"):
        g.line([(W * 0.4, H * 0.45), (W * 0.35, H * 0.6), (W * 0.4, H * 0.82), (W * 0.6, H * 0.82), (W * 0.65, H * 0.6), (W * 0.6, H * 0.45)], 3, True)
        for a in (-35, 0, 35):
            ar = math.radians(a - 90)
            g.line(curve((W * 0.5, H * 0.45), ar, H * 0.25, 0.05), 3)
            tip = (W * 0.5 + H * 0.25 * math.cos(ar), H * 0.45 + H * 0.25 * math.sin(ar))
            g.line(circle(tip[0], tip[1], H * 0.05, H * 0.05, n=20), 3, True)
        g.line([(W * 0.1, H * 0.82), (W * 0.9, H * 0.82)], 3)
    else:  # Apaisado
        hills(g, rng, W, H, H * 0.55, H * 0.1, 4)
        g.line(circle(W * 0.8, H * 0.22, H * 0.1, H * 0.1, n=40), 3, True)
    return g.img


def lineart_featured(W, H, rng):
    g = D(W, H, False)
    hor = H * 0.6
    g.line(wobble(rng, (0, hor), (W, hor), 3, 60), 3)
    for _ in range(4):
        cloud(g, rng, rng.uniform(0.1, 0.9) * W, rng.uniform(0.1, 0.4) * H, H * 0.07)
    for _ in range(12):
        x, y = rng.uniform(0, W), rng.uniform(hor + 20, H)
        g.line(curve((x, y), rng.uniform(-0.1, 0.1), rng.uniform(80, 180), 0.04), 2)
    fx, fy = W * 2 / 3, H * 2 / 3
    g.line([(fx, fy + 20), (fx - 3, fy + 100)], 4)
    for k in range(10):
        a = 2 * math.pi * k / 10
        g.line(leaf_pts(fx + 12 * math.cos(a), fy + 12 * math.sin(a), a, 46, 22), 2, True)
    g.line(circle(fx, fy, 10, 10, n=14), 2, True)
    return g.img


def guide_canvas(W, H, title, lines, featured=False):
    g = new_layer(W, H)
    d = guide_common(g, W, H, title, lines)
    for f in (1 / 3, 2 / 3):
        d.line([(W * f, 0), (W * f, H)], fill=(0, 255, 255, 170), width=2)
        d.line([(0, H * f), (W, H * f)], fill=(0, 255, 255, 170), width=2)
    mx, my = W * 0.05, H * 0.05
    rect = [(mx, my), (W - mx, my), (W - mx, H - my), (mx, H - my), (mx, my)]
    segs = list(zip(rect[:-1], rect[1:]))
    for a, b in segs:  # margen de seguridad discontinuo
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        for i in range(0, int(L), 28):
            t0, t1 = i / L, min(i + 16, L) / L
            d.line([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0), (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)], fill=(255, 128, 255, 255), width=3)
    d.text((mx + 6, H - my - 28), "margen de seguridad 5 %", fill=(255, 255, 255, 255), font=FONT_S, stroke_width=2, stroke_fill=(0, 0, 0, 255))
    if featured:
        hy = H * 0.6
        d.line([(0, hy), (W, hy)], fill=(255, 128, 255, 255), width=4)
        d.text((W - 480, hy + 6), "horizonte: 40 % desde abajo", fill=(255, 255, 255, 255), font=FONT_S, stroke_width=2, stroke_fill=(0, 0, 0, 255))
        d.rectangle([mx + 4, H * 0.3, W - mx - 4, hy - 6], outline=(150, 200, 255, 255), width=3)
        d.text((mx + 14, H * 0.3 + 6), "cielo casi gris, arremolinado", fill=(255, 255, 255, 255), font=FONT_S, stroke_width=2, stroke_fill=(0, 0, 0, 255))
        fx, fy = W * 2 / 3, H * 2 / 3
        d.line([(fx - 40, fy), (fx + 40, fy)], fill=(255, 255, 0, 255), width=4)
        d.line([(fx, fy - 40), (fx, fy + 40)], fill=(255, 255, 0, 255), width=4)
        d.ellipse([fx - 26, fy - 26, fx + 26, fy + 26], outline=(255, 255, 0, 255), width=3)
        d.text((fx + 50, fy - 12), "flor amarilla (tercio inferior derecho)", fill=(255, 255, 255, 255), font=FONT_S, stroke_width=2, stroke_fill=(0, 0, 0, 255))
    return g


def slots_text(names, n=6):
    s = ", ".join(names[:n])
    return s + (" ... (+%d, ver README)" % (len(names) - n) if len(names) > n else "")


# ---------------------------------------------------------------- main
def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for top in ("", "lienzos"):
        for sub in ("krita", "colorear", "blender", "preview"):
            os.makedirs(os.path.join(OUT, top, sub), exist_ok=True)
    rows = []
    # ---- familias
    for fam in FAMILIES:
        name, px, tile, mpr, mats, where, stroke, base, tenida, arrows, fn = fam
        rng = np.random.default_rng(zlib.crc32(name.encode()))
        ppm = px / mpr if mpr else px
        g = D(px, px, tile)
        fn(g, rng, px, ppm)
        base_hex = NEUTRAL if tenida else base
        guide = make_guide(fam, px, ppm)
        emit(OUT, "", "T_" + name, (px, px), base_hex, g.img, guide, "T_%s" % name)
        rows.append(["familia", name, "krita/T_%s.ora" % name, "%dx%d" % (px, px), "si" if tile else "no", mpr if tile else "-",
                     mats, where, EXPORT_DIR + "T_%s.png" % name, "TENIDA" if tenida else ""])
        print("familia:", name)
    # ---- lienzos
    slots = parse_slots()
    groups = {t[0]: [] for t in CANVAS_TYPES}
    feat = None
    for n, w, h in slots:
        if n == FEATURED:
            feat = (n, w, h)
            continue
        groups[nearest_type(w, h)[0]].append((n, w, h))
    canv = []
    for key, label, asp, (W, H) in CANVAS_TYPES:
        sl = groups[key]
        if not sl:
            continue
        names = [s[0] for s in sl]
        wm = [s[1] for s in sl]
        hm = [s[2] for s in sl]
        head = ["%dx%d px  |  NO repetible (cuadro)  |  aspecto %s" % (W, H, label),
                "Tamano real de los cuadros: %.2f-%.2f m x %.2f-%.2f m (ancho x alto)" % (min(wm), max(wm), min(hm), max(hm))]
        lines = fit_lines(W, head, ["Cuadros que lo usan (%d): %s" % (len(sl), slots_text(names)),
                                   "Exportar: un PNG por cuadro en " + PAINT_DIR + " con nombre T_Painting_<Slot>.png",
                                   "Regla de tercios (cian); margen de seguridad 5 % (magenta). Evita caras/detalles fuera del margen."])
        rng = np.random.default_rng(zlib.crc32(key.encode()))
        emit(OUT, "lienzos", "Lienzo_" + key, (W, H), "#D8D2C4", lineart_canvas(key, W, H, rng),
             guide_canvas(W, H, "Lienzo_%s" % key + "  -  %s" % label, lines), "Lienzo_%s" % key)
        canv.append((key, label, W, H, sl))
        print("lienzo:", key, len(sl))
    if feat:
        W, H = 1536, 1024
        lines = fit_lines(W, ["%dx%d px  |  NO repetible  |  cuadro 2.4 x 1.6 m (3:2)  |  slot %s" % (W, H, FEATURED),
                              "Horizonte al 40 % desde abajo. Cielo casi gris arremolinado; campo gris debajo.",
                              "La flor amarilla va en la interseccion inferior derecha de los tercios.",
                              "Direccion artistica: la flor destaca por CONTRASTE, no por brillo/glow.",
                              "Exportar: T_Painting_%s.png en %s" % (FEATURED, PAINT_DIR)], [])
        rng = np.random.default_rng(zlib.crc32(FEATURED_KEY.encode()))
        emit(OUT, "lienzos", FEATURED_KEY, (W, H), "#7A7E86", lineart_featured(W, H, rng),
             guide_canvas(W, H, FEATURED_KEY, lines, True), FEATURED_KEY)
        canv.append(("Destacado_CampoGris", "Destacado 3:2 (2.4 x 1.6 m)", W, H, [feat]))
        print("lienzo:", FEATURED_KEY)
    for key, label, W, H, sl in canv:
        tpl = "Lienzo_" + key if key != "Destacado_CampoGris" else FEATURED_KEY
        for n, w, h in sl:
            rows.append(["lienzo", n, "lienzos/krita/%s.ora" % tpl, "%dx%d" % (W, H), "no", "-",
                         "(pintura) %.2f x %.2f m" % (w, h), "cuadro %s" % n, PAINT_DIR + "T_Painting_%s.png" % n, label])
    # ---- inventario.csv
    with open(os.path.join(OUT, "inventario.csv"), "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f, lineterminator="\n")
        wr.writerow(["tipo", "nombre", "plantilla_krita", "tamano_px", "repetible", "m_por_repeticion", "materiales", "donde_se_ve", "exportar_a", "notas"])
        wr.writerows(rows)
    write_readme(canv)
    # ---- zip
    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for dp, _, fs in os.walk(OUT):
            for fn in sorted(fs):
                full = os.path.join(dp, fn)
                z.write(full, "TextureTemplates/" + os.path.relpath(full, OUT).replace(os.sep, "/"))
    print("zip:", ZIP, os.path.getsize(ZIP))


def write_readme(canv):
    L = []
    A = L.append
    A("# Pack de plantillas de textura del museo (The Living Canvas)")
    A("")
    A("Plantillas estilo **libro para colorear** para pintar a mano las texturas del museo. Cada textura trae:")
    A("")
    A("- `krita/T_<Familia>.ora`: capas, de arriba abajo: `GUIDE (ocultar al exportar)`, `LINEART (libro para colorear)`, `paint_here` (transparente) y `base_flat_color`.")
    A("- `colorear/T_<Familia>_colorear.png`: linea negra sobre blanco, para imprimir y colorear a mano.")
    A("- `blender/T_<Familia>.png`: color base plano con el dibujo de lineas al ~35 %, para pintar encima.")
    A("- `preview/T_<Familia>_guia.png`: vista previa con la guia ya fusionada.")
    A("- `lienzos/`: lo mismo para los cuadros (ver mas abajo).")
    A("- `inventario.csv`: una fila por familia y por hueco de cuadro.")
    A("")
    A("## Hechos importantes de las UV")
    A("")
    A("Los modelos del museo tienen **UV por proyeccion de caja a escala real**:")
    A("")
    A("- Arquitectura (paredes, suelos, tejado, escaleras, ventanas, marcos de puerta): **1 repeticion = 2 m**.")
    A("- Props y mobiliario (marcos, pedestales, plantas, bancos, carteles, hojas de puerta): **1 repeticion = 1 m**.")
    A("- Terreno exterior: **1 repeticion = 4 m**.")
    A("")
    A("Por eso casi todas las texturas deben ser **SEAMLESS / REPETIBLES**. En Krita activa el *Wrap Around Mode* (tecla **W**) y pinta sin ver costuras. "
      "El dibujo de lineas de las familias repetibles ya encaja (lo que cruza un borde reaparece en el opuesto). "
      "Excepciones (diseno completo, no repetibles): `Rug_Hall` y los lienzos de los cuadros.")
    A("")
    A("## Direccion artistica (recordatorio corto)")
    A("")
    A("- Pictorico: pinceladas del **MISMO tono** que el material (varia luminosidad y saturacion, no el tono).")
    A("- Trazos que se solapan, sin huecos. **Nada de remolinos tipo Van Gogh** en las texturas de material.")
    A("- Los trazos siguen la forma: veta a lo largo en la madera, a lo largo de la hoja, en hileras en el tejado.")
    A("- Las familias marcadas **TENIDA** se pintan en grises/cremas neutros y CLAROS: Unity las tine con el color de cada material "
      "(una sola textura sirve para muchas paredes, telas o maderas). Base neutra `#DDD6CA`.")
    A("")
    A("## Uso en Krita")
    A("")
    A("1. Abre el `.ora` de `krita/`. Activa **Wrap Around Mode** (tecla `W`).")
    A("2. Pinta en la capa `paint_here`, usando `LINEART` como guia de formas. Puedes ocultar `base_flat_color` si quieres pintar sobre transparente, pero lo normal es dejarlo.")
    A("3. Antes de exportar, **oculta** la capa `GUIDE (ocultar al exportar)` (y `LINEART` si no quieres las lineas en el resultado).")
    A("4. Exporta como PNG con el **nombre exacto** `T_<Familia>.png` y el **tamano exacto** de la plantilla, a `" + EXPORT_DIR + "`.")
    A("")
    A("## Uso en Blender")
    A("")
    A("Abre el PNG de `blender/` en el **Image Editor** (modo *Paint*) o usa *Texture Paint* sobre el modelo, y guarda encima (Image > Save As con el nombre `T_<Familia>.png`). "
      "El dibujo de lineas va al ~35 % para que se vea pero se pueda cubrir.")
    A("")
    A("## Familias de textura")
    A("")
    A("| Archivo | px | Repetible | m/rep | Materiales | Donde se ve |")
    A("|---|---|---|---|---|---|")
    for fam in FAMILIES:
        name, px, tile, mpr, mats, where, _, _, tenida, _, _ = fam
        A("| T_%s%s | %d | %s | %s | %s | %s |" % (name, " (TENIDA)" if tenida else "", px, "si (W)" if tile else "NO", mpr if tile else "-", mats, where))
    A("")
    A("## Lienzos (cuadros)")
    A("")
    A("Cada plantilla de lienzo mide 1536 px en el lado largo e incluye regla de tercios (cian) y margen de seguridad del 5 % (magenta). "
      "Se exporta **un PNG por hueco** a `" + PAINT_DIR + "` con el nombre del hueco, p. ej. `T_Painting_GalleryI_West.png`; la misma plantilla se puede reutilizar para varios huecos. "
      "No son repetibles.")
    A("")
    A("| Plantilla | px | Huecos que la usan |")
    A("|---|---|---|")
    for key, label, W, H, sl in canv:
        tpl = "Lienzo_" + key if key != "Destacado_CampoGris" else FEATURED_KEY
        A("| %s (%s) | %dx%d | %s |" % (tpl, label, W, H, ", ".join("%s (%.2f x %.2f m)" % s for s in sl)))
    A("")
    A("`Lienzo_Destacado_CampoGris` (hueco `GalleryV_Featured_GreyField`, 2.4 x 1.6 m): horizonte al 40 % desde abajo, cielo casi gris arremolinado y la pequena flor amarilla "
      "en la interseccion inferior derecha de los tercios. La flor destaca por **contraste, no por brillo ni glow**.")
    A("")
    A("## Orden de prioridad sugerido")
    A("")
    for i, n in enumerate(["Plaster", "Wood_Grain", "Wood_Planks", "Floor_Tiles_Hall", "Stone_Blocks", "Roof_Tiles", "Gilded", "Lienzo_Destacado_CampoGris"], 1):
        A("%d. %s" % (i, n))
    A("9. El resto de familias y lienzos.")
    A("")
    A("## Nota sobre Rug_Hall")
    A("")
    A("`Rug_Hall` es un medallon circular completo (no repetible). El modelo necesita un **cambio de UV** para mapearla como una sola pieza; lo hace Claude cuando exista la textura.")
    A("")
    A("## Cuando termines")
    A("")
    A("Cuando tengas texturas listas, avisale a Claude para conectarlas al shader **TLC/Painterly** en Unity.")
    A("")
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    main()
