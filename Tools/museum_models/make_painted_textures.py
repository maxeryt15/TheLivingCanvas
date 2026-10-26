"""Genera texturas EXTERIOR pintadas con pincelada tipo Van Gogh (impasto) a partir de los campos de flujo/paletas del pack.

Uso:  python -I Tools/museum_models/make_painted_textures.py [familia ...]
Salida (NO toca Unity): ArtSource/Museum/Painted_Textures/T_<Familia>.png (1024, repetible) + _preview.png (hoja 2x2 para ver costuras)
Motor: cada trazo = varias cerdas (lineas paralelas) con color/altura propios; la altura (impasto) se convierte en luz
lateral para que se lea el relieve de la pintura. Regiones (bloques, tejas, losas, tablas) se pintan con mascara.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "ArtSource", "Museum", "Painted_Textures")
N = 1024
TAU = math.tau

PAL = {  # oscuro, base, claro, luz, acento (de make_vangogh_pack.py)
    "Plaster": ["#C4B493", "#E3D6BA", "#EFE4CB", "#F7EEDA", "#CDA877"],
    "Stone_Blocks": ["#5C5750", "#867F74", "#A29B8E", "#BDB29C", "#6B7685"],
    "Roof_Tiles": ["#7A4234", "#A85F47", "#B96A52", "#C97A5C", "#6B7685"],
    "Painted_Boards": ["#3F5240", "#65785A", "#7A8F69", "#93A97A", "#D4A72C"],
    "Grass_Ground": ["#566A44", "#6E8157", "#869A6B", "#9CAE7B", "#D4A72C"],
    "Path_Stone": ["#6F727A", "#9A9A98", "#B0ADA5", "#C6B79A", "#A85F47"],
    "Wood_Grain": ["#5E4029", "#8A6240", "#A87C52", "#C9A06B", "#526A83"],
    "Leaves": ["#3C5236", "#587A48", "#7F9467", "#A3B574", "#D4A72C"],
    "Bark": ["#2F2119", "#5B4030", "#745440", "#8A6A52", "#65785A"],
    "Metal": ["#262A33", "#3C424E", "#566070", "#7E8590", "#A85F47"],
    "Cypress": ["#0F1D17", "#1F3A2B", "#2C4A36", "#4F6347", "#5A3A22"],
    "Bush_Swirl": ["#17302A", "#2F5A48", "#4A7F5C", "#86B087", "#C9B95A"],
    "Wall_Wavy": ["#C9BB9B", "#E2D5BA", "#ECE1C8", "#F5ECD8", "#D3B88B"],
    "Wall_Soft": ["#CDBF9F", "#E6DAC0", "#EFE5CE", "#F7EFDD", "#D3B88B"],
    "Fabric": ["#A89E8E", "#CFC6B4", "#E2DAC8", "#F0E9D8", "#B99A6A"],
    "Ceramic": ["#CFC6B2", "#E8DFCB", "#F2EAD8", "#FBF6EA", "#7E96A8"],
    "Floor_Tile": ["#5A6F75", "#7C9298", "#9BB0B4", "#BFCFCF", "#C9B27A"],
    "Gilded": ["#9A7428", "#C49A3A", "#D4A72C", "#F3DC96", "#A85F47"],
}
JOINT = {"Stone_Blocks": "#2E3A52", "Roof_Tiles": "#3A2A3C", "Painted_Boards": "#1F2E3A", "Path_Stone": "#3B4050"}


LAST_H = None


def hx(h):
    if not isinstance(h, str):
        return np.array(h, float)
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def jitter(c, rng, amt=0.07):
    k = 1 + rng.uniform(-amt, amt) + rng.uniform(-amt * 0.3, amt * 0.3, 3)   # luminosidad + cromatismo minimo (sin ruido de color)
    return tuple(int(v) for v in np.clip(c * k + rng.uniform(-2, 2), 0, 255))


def pick(pal, rng, w=(0.14, 0.34, 0.26, 0.16, 0.10)):
    return pal[rng.choice(len(pal), p=np.array(w) / sum(w))]


class Layer:
    """Color + altura de un lienzo (o recorte) con dibujo de trazos."""

    def __init__(self, rgb=None, h=None, size=(N, N)):
        self.img = Image.fromarray(rgb) if rgb is not None else Image.new("RGB", size)
        self.hei = Image.fromarray(h) if h is not None else Image.new("L", size, 90)
        self.dc = ImageDraw.Draw(self.img)
        self.dh = ImageDraw.Draw(self.hei)
        self.size = self.img.size

    def arrays(self):
        return np.asarray(self.img).copy(), np.asarray(self.hei).copy()


def stroke(L, pts, w, color, rng, wrap=False, dry=0.0, bw=3, lift=1.0, bjit=0.05):
    """Trazo de cerdas a lo largo de pts (lista de (x,y)). dry = prob. de saltar tramos (pincel seco)."""
    pts = np.array(pts, float)
    if len(pts) < 2:
        return
    d = np.gradient(pts, axis=0)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-6)
    nb = max(3, int(w / bw))
    taper = np.sin(np.linspace(0.15, math.pi - 0.15, len(pts))) ** 0.5
    offs = (-1, 0, 1) if wrap else (0,)
    S = L.size[0]
    for b in range(nb):
        u = (b / (nb - 1) - 0.5) * w
        wob = rng.normal(0, 0.6, len(pts)).cumsum() * 0.35
        p = pts + nrm * (u * taper[:, None] + wob[:, None] * 0.4)
        i0 = int(rng.uniform(0, 0.12) * len(p))
        i1 = len(p) - int(rng.uniform(0, 0.12) * len(p))
        p = p[i0:i1]
        if len(p) < 2:
            continue
        col = jitter(np.array(color, float), rng, bjit)
        hv = int(np.clip(125 + (1 - abs(2 * b / (nb - 1) - 1)) * 60 * lift + rng.uniform(-35, 35), 0, 255))
        segs = [p]
        if dry > 0:
            segs, cur = [], []
            for q in p:
                cur.append(q)
                if rng.random() < dry * 0.18:
                    if len(cur) > 1:
                        segs.append(np.array(cur))
                    cur = []
            if len(cur) > 1:
                segs.append(np.array(cur))
        for sgm in segs:
            for ox in offs:
                for oy in offs:
                    q = sgm + (ox * S, oy * S)
                    if wrap and (q[:, 0].max() < 0 or q[:, 0].min() > S or q[:, 1].max() < 0 or q[:, 1].min() > S):
                        continue
                    t = [tuple(v) for v in q]
                    L.dc.line(t, fill=col, width=bw, joint="curve")
                    L.dh.line(t, fill=hv, width=bw, joint="curve")


def trace(x, y, ang_fn, length, step, curv, rng):
    pts, a = [(x, y)], math.radians(ang_fn(x, y))
    bend = rng.uniform(-curv, curv)
    for i in range(int(length / step)):
        a = math.radians(ang_fn(x, y)) + bend * math.sin(math.pi * i * step / length)
        x += math.cos(a) * step
        y += math.sin(a) * step
        pts.append((x, y))
    return pts


def wave(kx, ky, ph=0.0):
    return lambda x, y: math.sin(TAU * (kx * x + ky * y) / N + ph)


def smooth_noise(rng, cycles=4, octaves=3):
    """Ruido de baja frecuencia repetible (0..1)."""
    out = np.zeros((N, N))
    for o in range(octaves):
        c = cycles * 2 ** o
        g = rng.random((c, c))
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((N + 2 * N // c, N + 2 * N // c), Image.BICUBIC)
        # tile-wrap: usa np.tile del grid antes de reescalar
        gt = np.tile(g, (3, 3))
        im = Image.fromarray((gt * 255).astype(np.uint8)).resize((3 * N, 3 * N), Image.BICUBIC)
        out += np.asarray(im, float)[N:2 * N, N:2 * N] / 255 / 2 ** o
    out -= out.min()
    return out / out.max()


def finish(L, k=0.20, light=(-1.0, -1.0)):
    """Convierte la altura en sombreado lateral (impasto) y devuelve la imagen final."""
    rgb, hei = L.arrays()
    h = np.asarray(Image.fromarray(hei).filter(ImageFilter.GaussianBlur(0.9)), float)
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / 2
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / 2
    lx, ly = light
    nl = math.hypot(lx, ly)
    sh = (gx * lx + gy * ly) / nl / 22.0
    sh = np.clip(sh, -1, 1) * k
    rgb = rgb.astype(float) * (1 + sh[..., None])
    global LAST_H
    LAST_H = Image.fromarray(hei)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))


def blotches(L, pal, rng, n, wlo, whi, ang_fn, wrap=True, mix=(0.1, 0.3, 0.3, 0.2, 0.1)):
    for _ in range(n):
        x, y = rng.uniform(0, N, 2)
        pts = trace(x, y, ang_fn, rng.uniform(120, 260), 14, 0.5, rng)
        stroke(L, pts, rng.uniform(wlo, whi), jitter(hx(pick(pal, rng, mix)), rng, 0.04), rng, wrap=wrap, bw=4, lift=0.5)


# ------------------------------------------------------------------ regiones con mascara
def paint_region(L, mask, fn):
    """Pinta fn(local_layer, mask_local, bbox_w, bbox_h) dentro de mask (bool NxN, puede cruzar bordes: se centra con roll)."""
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return
    cx = int(round((math.atan2(np.sin(TAU * xs / N).mean(), np.cos(TAU * xs / N).mean()) / TAU * N) % N))
    cy = int(round((math.atan2(np.sin(TAU * ys / N).mean(), np.cos(TAU * ys / N).mean()) / TAU * N) % N))
    sx, sy = N // 2 - cx, N // 2 - cy
    rm = np.roll(mask, (sy, sx), (0, 1))
    ys, xs = np.nonzero(rm)
    pad = 28
    x0, x1 = max(0, xs.min() - pad), min(N, xs.max() + pad + 1)
    y0, y1 = max(0, ys.min() - pad), min(N, ys.max() + pad + 1)
    rgb, hei = L.arrays()
    rgb, hei = np.roll(rgb, (sy, sx), (0, 1)), np.roll(hei, (sy, sx), (0, 1))
    loc = Layer(rgb[y0:y1, x0:x1].copy(), hei[y0:y1, x0:x1].copy())
    fn(loc, rm[y0:y1, x0:x1], x0 - sx, y0 - sy)
    lr, lh = loc.arrays()
    m = rm[y0:y1, x0:x1]
    rgb[y0:y1, x0:x1][m] = lr[m]
    hei[y0:y1, x0:x1][m] = lh[m]
    L.img = Image.fromarray(np.roll(rgb, (-sy, -sx), (0, 1)))
    L.hei = Image.fromarray(np.roll(hei, (-sy, -sx), (0, 1)))
    L.dc, L.dh = ImageDraw.Draw(L.img), ImageDraw.Draw(L.hei)


def fill_base(L, color, h=70):
    L.img.paste(tuple(int(v) for v in color), (0, 0, N, N))
    L.hei.paste(h, (0, 0, N, N))


def region_strokes(loc, mask, base, pal, rng, n, wlo, whi, ang, lenlo, lenhi, curv=0.35, dry=0.0, accent=0.07):
    h, w = mask.shape
    loc.img.paste(tuple(int(v) for v in base), (0, 0, w, h))
    loc.hei.paste(100, (0, 0, w, h))
    for i in range(n):
        x, y = rng.uniform(-10, w + 10), rng.uniform(-10, h + 10)
        pts = trace(x, y, lambda a, b: ang(a, b), rng.uniform(lenlo, lenhi), 9, curv, rng)
        c = pal[4] if rng.random() < accent else pick(pal, rng)
        stroke(loc, pts, rng.uniform(wlo, whi), jitter(hx(c) if isinstance(c, str) else np.array(c, float), rng), rng, dry=dry, bw=3)


# ------------------------------------------------------------------ familias
def make_grass(rng):
    pal = [hx(c) for c in PAL["Grass_Ground"]]
    L = Layer()
    fill_base(L, pal[1])
    f = lambda x, y: -90 + 38 * wave(2, 1, 0.4)(x, y) + 22 * wave(3, -2, 1.6)(x, y) + 14 * wave(1, 3, 2.7)(x, y)
    blotches(L, pal, rng, 160, 36, 60, f)
    for _ in range(1500):
        x, y = rng.uniform(0, N, 2)
        pts = trace(x, y, f, rng.uniform(110, 220), 11, 0.7, rng)
        r = rng.random()
        c = pal[4] if r < 0.008 else (hx("#526A83") if r < 0.016 else pick(pal, rng))
        stroke(L, pts, rng.uniform(12, 24), jitter(c, rng), rng, wrap=True, dry=0.25)
    return finish(L, 0.12)


def make_plaster(rng):
    pal = [hx(c) for c in PAL["Plaster"]]
    L = Layer()
    fill_base(L, pal[1], 80)
    f = lambda x, y: 8 + 26 * wave(1, 1, 0.5)(x, y) + 18 * wave(2, -1, 2.2)(x, y)
    for _ in range(420):
        x, y = rng.uniform(0, N, 2)
        pts = trace(x, y, f, rng.uniform(90, 200), 12, 0.55, rng)
        r = rng.random()
        c = hx("#A9B0B8") if r < 0.012 else (hx("#D8BE98") if r < 0.10 else pick(pal, rng, (0.2, 0.3, 0.25, 0.25, 0.06)))
        stroke(L, pts, rng.uniform(38, 70), jitter(c, rng, 0.03), rng, wrap=True, bw=4, lift=0.45)
    return finish(L, 0.14)


def make_stone_blocks(rng):
    pal = [hx(c) for c in PAL["Stone_Blocks"]]
    L = Layer()
    fill_base(L, hx(JOINT["Stone_Blocks"]), 40)
    rows, rh = 6, N // 6
    for r in range(rows):
        widths = rng.uniform(0.7, 1.3, 2 + r % 2)
        widths = (widths / widths.sum() * N).astype(int)
        widths[-1] = N - widths[:-1].sum()
        x = int(rng.integers(0, N))
        for bw_ in widths:
            m = np.zeros((N, N), bool)
            ii = (np.arange(N)[None, :] - x) % N
            jj = np.arange(N)[:, None]
            m[:] = (ii >= 6) & (ii < bw_ - 6) & (jj >= r * rh + 6) & (jj < (r + 1) * rh - 6)
            tone = pal[rng.integers(0, 4)] * rng.uniform(0.9, 1.08)
            shift = rng.uniform(-1, 1)
            n_ = int(bw_ * rh / 300)
            paint_region(L, m, lambda loc, mk, ox, oy, tone=tone, n_=n_: region_strokes(
                loc, mk, tone, [tone * 0.8, tone, tone * 1.1, tone * 1.22, pal[4]], rng, n_, 22, 36,
                lambda a, b: 0 + 7 * math.sin(a / 40.0) + 3, 70, 150, 0.2, dry=0.2, accent=0.08))
            x = (x + bw_) % N
    return finish(L, 0.22)


def make_roof_tiles(rng):
    pal = [hx(c) for c in PAL["Roof_Tiles"]]
    L = Layer()
    fill_base(L, hx(JOINT["Roof_Tiles"]), 40)
    cols, rows = 8, 6
    cw, rh = N // cols, N // rows
    yy, xx = np.mgrid[0:N, 0:N]
    for r in range(rows):
        off = (cw // 2) if r % 2 else 0
        for c in range(cols):
            x0 = (c * cw + off) % N
            ii = (xx - x0) % N
            jj = yy - r * rh
            # teja con borde inferior festoneado
            cx = cw / 2
            edge = (r + 1) * rh - 8 - ((1 - ((ii - cx) / cx) ** 2).clip(0) ** 0.5) * -14 - 14 * ((ii - cx) / cx) ** 2
            m = (ii >= 5) & (ii < cw - 5) & (jj >= 4) & (yy < ((r + 1) * rh - 10) + 10 * np.sqrt(np.clip(1 - ((ii - cx) / cx) ** 2, 0, 1)) - 10)
            tone = pal[rng.integers(0, 4)] * rng.uniform(0.95, 1.05)
            if rng.random() < 0.025:
                tone = hx("#C98E5E")
            n_ = 48
            paint_region(L, m, lambda loc, mk, ox, oy, tone=tone: region_strokes(
                loc, mk, tone, [tone * 0.72, tone, tone * 1.1, tone * 1.22, pal[4]], rng, n_, 14, 26,
                lambda a, b: 90 + 8 * math.sin(b / 30.0), 80, 150, 0.25, dry=0.15, accent=0.02))
    return finish(L, 0.16)


def make_path_stone(rng):
    pal = [hx(c) for c in PAL["Path_Stone"]]
    L = Layer()
    fill_base(L, hx(JOINT["Path_Stone"]), 40)
    g = 4
    seeds = np.array([((i + rng.uniform(0.15, 0.85)) * N / g, (j + rng.uniform(0.15, 0.85)) * N / g) for i in range(g) for j in range(g)])
    yy, xx = np.mgrid[0:N, 0:N]
    d = []
    for sx, sy in seeds:
        dx = np.minimum(np.abs(xx - sx), N - np.abs(xx - sx))
        dy = np.minimum(np.abs(yy - sy), N - np.abs(yy - sy))
        d.append(np.hypot(dx, dy))
    d = np.stack(d)
    order = np.argsort(d, 0)
    d1 = np.take_along_axis(d, order[:1], 0)[0]
    d2 = np.take_along_axis(d, order[1:2], 0)[0]
    lab = order[0]
    inner = (d2 - d1) > 11
    for i, (sx, sy) in enumerate(seeds):
        m = (lab == i) & inner
        tone = pal[rng.integers(0, 4)] * rng.uniform(0.9, 1.08)
        ang0 = rng.uniform(0, 180)
        paint_region(L, m, lambda loc, mk, ox, oy, tone=tone, a0=ang0: region_strokes(
            loc, mk, tone, [tone * 0.78, tone, tone * 1.1, tone * 1.22, pal[4]], rng, 150, 16, 30,
            lambda a, b: a0 + 20 * math.sin(a / 35.0), 60, 130, 0.5, dry=0.2, accent=0.07))
    return finish(L, 0.22)


def make_boards(rng):
    pal = [hx(c) for c in PAL["Painted_Boards"]]
    L = Layer()
    fill_base(L, hx(JOINT["Painted_Boards"]), 40)
    bw_ = N // 8
    for i in range(8):
        m = np.zeros((N, N), bool)
        m[:, i * bw_ + 5:(i + 1) * bw_ - 5] = True
        tone = pal[rng.integers(0, 4)] * rng.uniform(0.9, 1.08)
        paint_region(L, m, lambda loc, mk, ox, oy, tone=tone: region_strokes(
            loc, mk, tone, [tone * 0.78, tone, tone * 1.1, tone * 1.2, hx("#B58459")], rng, 30, 20, 34,
            lambda a, b: 90 + 4 * math.sin(b / 120.0), 500, 900, 0.05, dry=0.6, accent=0.12))
    # descascarillado: toques cortos de madera/crema
    for _ in range(70):
        x, y = rng.uniform(0, N, 2)
        stroke(L, trace(x, y, lambda a, b: 90, rng.uniform(15, 45), 5, 0.1, rng), rng.uniform(6, 12),
               jitter(hx(rng.choice(["#C9A06B", "#E0CDB0", "#8A6A52"])), rng), rng, wrap=True, bw=3)
    return finish(L, 0.22)


# ------------------------------------------------------------------ variante MUNCH (zonas de Descoloracion): cintas largas y fluidas, pintura fina, contorno oscuro
MUNCH_PAL = {  # oscuro, base, claro, luz, acento (cálido/frío, saturación reducida)
    "Grass_Ground": ["#3E4A3C", "#6B7560", "#8E9580", "#B7B59B", "#B5603F"],
    "Plaster": ["#A89E92", "#CFC6B6", "#E2D9C6", "#EFE7D4", "#C07A55"],
    "Path_Stone": ["#4A5260", "#7C7F86", "#A29E98", "#C2B49A", "#B5603F"],
}


def make_munch(name, rng):
    pal = [hx(c) for c in MUNCH_PAL[name]]
    L = Layer()
    fill_base(L, pal[1], 80)
    f = lambda x, y: 6 + 30 * wave(1, 0, 0.3)(x, y) + 12 * wave(2, 1, 1.9)(x, y) + 8 * wave(1, 2, 0.7)(x, y)
    for band in range(9):  # cintas horizontales onduladas que cubren toda la hoja
        y0 = band * N / 9 + rng.uniform(-20, 20)
        col = pick(pal, rng, (0.2, 0.3, 0.25, 0.15, 0.1))
        for k in range(5):
            x0 = rng.uniform(0, N)
            pts = trace(x0, y0 + rng.uniform(-30, 30), f, rng.uniform(420, 760), 16, 0.3, rng)
            stroke(L, pts, rng.uniform(46, 84), jitter(col, rng, 0.05), rng, wrap=True, dry=0.15, bw=5, lift=0.25)
    for _ in range(26):  # contornos oscuros finos entre cintas
        x0, y0 = rng.uniform(0, N, 2)
        pts = trace(x0, y0, f, rng.uniform(300, 700), 16, 0.25, rng)
        stroke(L, pts, rng.uniform(8, 14), jitter(pal[0] * 0.7, rng, 0.05), rng, wrap=True, dry=0.1, bw=3, lift=0.2)
    for _ in range(10):  # acento cálido
        x0, y0 = rng.uniform(0, N, 2)
        pts = trace(x0, y0, f, rng.uniform(200, 420), 16, 0.3, rng)
        stroke(L, pts, rng.uniform(14, 26), jitter(pal[4], rng, 0.05), rng, wrap=True, dry=0.2, bw=4, lift=0.25)
    return finish(L, 0.10)


def flow_tex(name, ang, n, lenlo, lenhi, wlo, whi, curv, dry, k, bw=3, accent=0.05, blot=80, blot_w=(30, 55), mix=(0.14, 0.34, 0.26, 0.16, 0.10), fissure=0):
    def make(rng):
        pal = [hx(c) for c in PAL[name]]
        L = Layer()
        fill_base(L, pal[1])
        blotches(L, pal, rng, blot, blot_w[0], blot_w[1], ang)
        for _ in range(fissure):  # fisuras finas oscuras
            x, y = rng.uniform(0, N, 2)
            stroke(L, trace(x, y, ang, rng.uniform(200, 500), 12, 0.2, rng), rng.uniform(5, 9), jitter(pal[0] * 0.55, rng), rng, wrap=True, bw=3)
        for _ in range(n):
            x, y = rng.uniform(0, N, 2)
            c = pal[4] if rng.random() < accent else pick(pal, rng, mix)
            stroke(L, trace(x, y, ang, rng.uniform(lenlo, lenhi), 9, curv, rng), rng.uniform(wlo, whi), jitter(c, rng), rng, wrap=True, dry=dry, bw=bw)
        return finish(L, k)
    return make


def make_cypress(rng):
    """Cipres de La noche estrellada: verde casi negro, tongas de llama largas en S, contornos marrones y toques azul-verdoso."""
    pal = [hx(c) for c in PAL["Cypress"]]
    L = Layer()
    fill_base(L, pal[1], 70)
    f = lambda x, y: 90 + 38 * wave(2, 0, 0.3)(x, y) + 20 * wave(3, 2, 1.7)(x, y) + 12 * wave(1, 4, 0.6)(x, y)
    blotches(L, pal, rng, 140, 40, 70, f, mix=(0.35, 0.35, 0.2, 0.08, 0.02))
    for _ in range(900):  # tongas de llama
        x, y = rng.uniform(0, N, 2)
        r = rng.random()
        c = hx("#2E5A5A") if r < 0.04 else (pal[3] if r < 0.12 else pick(pal, rng, (0.34, 0.32, 0.24, 0.10, 0.0)))
        stroke(L, trace(x, y, f, rng.uniform(260, 560), 11, 0.5, rng), rng.uniform(16, 34), jitter(c, rng, 0.05), rng, wrap=True, dry=0.22, bw=3)
    for _ in range(28):  # contornos marrones entre tongas
        x, y = rng.uniform(0, N, 2)
        stroke(L, trace(x, y, f, rng.uniform(300, 650), 11, 0.4, rng), rng.uniform(4, 7), jitter(pal[4], rng, 0.08), rng, wrap=True, dry=0.3, bw=2)
    return finish(L, 0.24)


def make_bush_swirl(rng):
    """Follaje de La noche estrellada (pueblo): trazos cortos que giran en remolinos/rizos, azul marino, verde azulado y turquesa claro."""
    pal = [hx(c) for c in PAL["Bush_Swirl"]]
    L = Layer()
    fill_base(L, pal[1], 70)
    G = 128
    cs = [(rng.uniform(0, N), rng.uniform(0, N), rng.choice([-1, 1])) for _ in range(9)]
    yy, xx = np.mgrid[0:G, 0:G] * (N / G)
    vx = np.zeros((G, G)); vy = np.zeros((G, G))
    for cx, cy, sg in cs:
        for ox in (-N, 0, N):
            for oy in (-N, 0, N):
                dx, dy = xx - (cx + ox), yy - (cy + oy)
                d2 = dx * dx + dy * dy + 70.0 ** 2
                vx += -sg * dy / d2
                vy += sg * dx / d2
    ang = np.degrees(np.arctan2(vy, vx))
    f = lambda x, y: float(ang[int(y % N) * G // N, int(x % N) * G // N])
    blotches(L, pal, rng, 160, 36, 60, f, mix=(0.30, 0.34, 0.22, 0.12, 0.02))
    for _ in range(1500):
        x, y = rng.uniform(0, N, 2)
        r = rng.random()
        c = pal[4] if r < 0.03 else (pal[3] if r < 0.18 else pick(pal, rng, (0.30, 0.34, 0.24, 0.12, 0.0)))
        stroke(L, trace(x, y, f, rng.uniform(70, 160), 8, 0.35, rng), rng.uniform(13, 26), jitter(c, rng, 0.05), rng, wrap=True, dry=0.2, bw=3)
    return finish(L, 0.25)


# ------------------------------------------------------------------ interior: calmas, trazos anchos y tonos cercanos
def make_fabric(rng):
    pal = [hx(c) for c in PAL["Fabric"]]
    L = Layer()
    fill_base(L, pal[1], 80)
    for ang, n in ((0, 520), (90, 520)):  # tejido: pasadas horizontales y luego verticales
        f = lambda x, y, a=ang: a + 4 * wave(1, 2, 0.5)(x, y)
        for _ in range(n):
            x, y = rng.uniform(0, N, 2)
            c = pal[4] if rng.random() < 0.02 else pick(pal, rng, (0.1, 0.4, 0.3, 0.2, 0.0))
            stroke(L, trace(x, y, f, rng.uniform(140, 320), 12, 0.05, rng), rng.uniform(9, 15), jitter(c, rng, 0.03), rng, wrap=True, dry=0.15, bw=3, lift=0.4)
    for _ in range(18):  # pliegues suaves
        x, y = rng.uniform(0, N, 2)
        stroke(L, trace(x, y, lambda a, b: 90 + 6 * wave(1, 1, 1.0)(a, b), rng.uniform(300, 600), 14, 0.05, rng), rng.uniform(30, 50), jitter(pal[0] * 0.5 + pal[1] * 0.5, rng, 0.03), rng, wrap=True, bw=5, lift=0.2)
    return finish(L, 0.12)


def make_ceramic(rng):
    pal = [hx(c) for c in PAL["Ceramic"]]
    L = Layer()
    fill_base(L, pal[1], 90)
    f = lambda x, y: 10 + 14 * wave(1, 1, 0.7)(x, y)
    for _ in range(110):
        x, y = rng.uniform(0, N, 2)
        stroke(L, trace(x, y, f, rng.uniform(150, 320), 14, 0.3, rng), rng.uniform(46, 80), jitter(pick(pal, rng, (0.1, 0.4, 0.3, 0.2, 0.0)), rng, 0.02), rng, wrap=True, bw=5, lift=0.25)
    for _ in range(7):  # brillos largos
        x, y = rng.uniform(0, N, 2)
        stroke(L, trace(x, y, f, rng.uniform(300, 520), 14, 0.15, rng), rng.uniform(10, 18), jitter(pal[3], rng, 0.01), rng, wrap=True, bw=3, lift=0.2)
    for _ in range(5):
        x, y = rng.uniform(0, N, 2)
        stroke(L, trace(x, y, f, rng.uniform(100, 200), 14, 0.2, rng), rng.uniform(14, 24), jitter(pal[4], rng, 0.04), rng, wrap=True, bw=3, lift=0.2)
    return finish(L, 0.08)


def make_floor_tile(rng):
    pal = [hx(c) for c in PAL["Floor_Tile"]]
    L = Layer()
    fill_base(L, hx("#2E3A4A"), 40)
    g, cell = 4, N // 4
    for i in range(g):
        for j in range(g):
            m = np.zeros((N, N), bool)
            m[j * cell + 6:(j + 1) * cell - 6, i * cell + 6:(i + 1) * cell - 6] = True
            tone = pal[rng.integers(0, 4)] * rng.uniform(0.95, 1.05)
            paint_region(L, m, lambda loc, mk, ox, oy, tone=tone: region_strokes(
                loc, mk, tone, [tone * 0.85, tone, tone * 1.08, tone * 1.16, tone * 0.92], rng, 36, 22, 36,
                lambda a, b: 45 + 5 * math.sin(a / 40.0), 70, 140, 0.15, dry=0.1, accent=0.0))
    return finish(L, 0.14)


MAKERS = {"Grass_Ground": make_grass, "Plaster": make_plaster, "Stone_Blocks": make_stone_blocks,
          "Roof_Tiles": make_roof_tiles, "Path_Stone": make_path_stone, "Painted_Boards": make_boards}
MAKERS["Cypress"] = make_cypress
MAKERS["Bush_Swirl"] = make_bush_swirl
MAKERS["Fabric"] = make_fabric
MAKERS["Ceramic"] = make_ceramic
MAKERS["Floor_Tile"] = make_floor_tile
MAKERS["Wall_Wavy"] = flow_tex("Wall_Wavy", lambda x, y: 4 + 16 * wave(1, 1, 0.5)(x, y) + 9 * wave(2, 1, 2.2)(x, y), 330, 520, 900, 30, 56, 0.35, 0.05, 0.08, bw=5, accent=0.0, blot=26, blot_w=(60, 90), mix=(0.10, 0.40, 0.32, 0.18, 0.0))
MAKERS["Wall_Soft"] = flow_tex("Wall_Soft", lambda x, y: 8 + 10 * wave(1, 1, 0.5)(x, y) + 8 * wave(2, -1, 2.2)(x, y), 260, 90, 200, 50, 90, 0.5, 0.0, 0.09, bw=5, accent=0.0, blot=30, blot_w=(70, 100), mix=(0.12, 0.4, 0.3, 0.18, 0.0))
MAKERS["Wood_Grain"] = flow_tex("Wood_Grain", lambda x, y: 90 + 5 * wave(1, 2, 0.4)(x, y) + 3 * wave(2, 1, 2.0)(x, y), 150, 400, 800, 34, 60, 0.08, 0.0, 0.07, bw=4, accent=0.0, blot=40, blot_w=(60, 90), mix=(0.06, 0.46, 0.34, 0.14, 0.0))
MAKERS["Leaves"] = flow_tex("Leaves", lambda x, y: -60 + 55 * wave(3, 2, 0.5)(x, y) + 40 * wave(5, -3, 1.7)(x, y), 1700, 45, 95, 9, 17, 0.9, 0.05, 0.22, accent=0.06)
MAKERS["Bark"] = flow_tex("Bark", lambda x, y: 90 + 9 * wave(2, 1, 0.9)(x, y) + 6 * wave(1, 4, 0.2)(x, y), 700, 250, 520, 12, 22, 0.1, 0.3, 0.24, accent=0.04, fissure=60)
MAKERS["Metal"] = flow_tex("Metal", lambda x, y: 0 + 3 * wave(1, 2, 0.5)(x, y), 520, 250, 600, 8, 16, 0.04, 0.2, 0.18, bw=2, accent=0.03, blot_w=(20, 36))
MAKERS["Gilded"] = flow_tex("Gilded", lambda x, y: 20 + 60 * wave(3, 3, 1.1)(x, y), 1300, 30, 60, 10, 18, 0.5, 0.0, 0.26, accent=0.05, mix=(0.1, 0.3, 0.3, 0.25, 0.05))
for _n in MUNCH_PAL:
    MAKERS[_n + "_Munch"] = (lambda r, _n=_n: make_munch(_n, r))


def main():
    names = sys.argv[1:] or list(MAKERS)
    os.makedirs(OUT, exist_ok=True)
    for n in names:
        rng = np.random.default_rng(abs(hash(n)) % 2 ** 31 if False else sum(map(ord, n)) * 97)
        img = MAKERS[n](rng)
        img.save(os.path.join(OUT, f"T_{n}.png"))
        LAST_H.save(os.path.join(OUT, f"H_{n}.png"))
        big = Image.new("RGB", (N * 2, N * 2))
        for a in range(2):
            for b in range(2):
                big.paste(img, (a * N, b * N))
        big.resize((1024, 1024), Image.LANCZOS).save(os.path.join(OUT, f"_preview_{n}.png"))
        print("ok", n)


if __name__ == "__main__":
    main()
