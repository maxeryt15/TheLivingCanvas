"""Pinta el 'pez ojo' (line art) con el motor de pinceladas Van Gogh: colores de koi + fondo marino opaco con trazos.

Uso:  python -I Tools/museum_models/paint_eye_fish.py
Entrada: ArtSource/EyeFish/EyeFish_lineart.png   Salida: ArtSource/EyeFish/EyeFish_Koi.png
Regiones = componentes cerrados del line art (cierre morfologico); cada una lleva paleta, direccion de trazo y densidad propias.
El line art original se multiplica encima (contornos y sombreado de tinta se conservan).
"""
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import make_painted_textures as M  # noqa: E402

DIR = os.path.join(ROOT, "ArtSource", "EyeFish")
SRC = os.path.join(DIR, "EyeFish_lineart.png")
SIMPLE = "simple" in sys.argv[1:]
OUT = os.path.join(DIR, "EyeFish_Koi_simple.png" if SIMPLE else "EyeFish_Koi.png")
# modo simple: menos trazos, mas anchos, color casi plano por trazo, sin pincel seco ni capas de detalle (look de pintor aficionado)
K = dict(dens=0.32, wmul=1.7, bw=6, dry=0.0, jit=0.025, bgn=420, bgw=(34, 60), rays=0, bubbles=5, finish=0.16) if SIMPLE else     dict(dens=1.0, wmul=1.0, bw=3, dry=None, jit=0.05, bgn=2600, bgw=(14, 30), rays=14, bubbles=9, finish=0.20)

# --- paleta koi (Kohaku / Showa): hi = rojo-naranja, shiro = blanco crema, sumi = negro azulado, oro
HI, HI2, HI3 = "#C93A1C", "#E8581F", "#F28A2B"
SHIRO, SHIRO2, SHIRO3 = "#F2E9D8", "#E6DAC4", "#FBF6EA"
SUMI, GOLD, GOLD2 = "#1B1D2A", "#D9A32E", "#F0CB62"
PAL = {
    "red": [HI, "#D9461E", HI2, HI3, GOLD],
    "orange": ["#D9561F", HI2, HI3, "#F7B466", HI],
    "shiro": ["#CFC2AB", SHIRO2, SHIRO, SHIRO3, HI3],
    "shiro_o": ["#E0B58A", "#F0D3AE", SHIRO, "#F7B466", HI2],
    "sumi": ["#0E1018", SUMI, "#2D3142", "#4A5068", HI],
    "sclera": ["#B7C3D2", SHIRO2, SHIRO, SHIRO3, HI3],
}


def make_canvas(W, H):
    return M.Layer(size=(W, H))


def flow_radial(px, py, wob=14.0, k=60.0):
    return lambda x, y: math.degrees(math.atan2(y - py, x - px)) + wob * math.sin((x + y) / k)


def flow_concentric(cx, cy, wob=6.0):
    return lambda x, y: math.degrees(math.atan2(y - cy, x - cx)) + 90 + wob * math.sin((x - y) / 70.0)


def paint_region(L, mask, pal, rng, flow, wlo, whi, lenlo, lenhi, curv=0.4, density=1.0, dry=0.1, accent=0.04,
                 weights=(0.14, 0.34, 0.26, 0.16, 0.10), base=None, grow=1):
    mask = cv2.dilate(mask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * grow + 1, 2 * grow + 1))) > 0
    ys, xs = np.nonzero(mask)
    if len(xs) < 20:
        return
    pad = 40
    x0, x1 = max(0, xs.min() - pad), min(mask.shape[1], xs.max() + pad + 1)
    y0, y1 = max(0, ys.min() - pad), min(mask.shape[0], ys.max() + pad + 1)
    rgb, hei = L.arrays()
    loc = M.Layer(rgb[y0:y1, x0:x1].copy(), hei[y0:y1, x0:x1].copy())
    cols = [M.hx(c) for c in pal]
    loc.img.paste(tuple(int(v) for v in (M.hx(base) if base else cols[1])), (0, 0, loc.size[0], loc.size[1]))
    loc.hei.paste(80, (0, 0, loc.size[0], loc.size[1]))
    area = len(xs)
    wlo, whi = wlo * K['wmul'], whi * K['wmul']
    n = int(area / (0.5 * (wlo + whi) * 0.5 * (lenlo + lenhi) * 0.35) * density * K['dens']) + (4 if SIMPLE else 6)
    idx = rng.integers(0, len(xs), n)
    for i in idx:
        gx, gy = float(xs[i]), float(ys[i])
        pts = M.trace(gx, gy, flow, rng.uniform(lenlo, lenhi), 8, curv, rng)
        pts = [(px - x0, py - y0) for px, py in pts]
        c = cols[4] if rng.random() < accent else M.pick(cols, rng, weights)
        M.stroke(loc, pts, rng.uniform(wlo, whi), M.jitter(c, rng, K['jit']), rng, dry=(dry if K['dry'] is None else K['dry']), bw=K['bw'])
    lr, lh = loc.arrays()
    m = mask[y0:y1, x0:x1]
    rgb[y0:y1, x0:x1][m] = lr[m]
    hei[y0:y1, x0:x1][m] = lh[m]
    L.img, L.hei = Image.fromarray(rgb), Image.fromarray(hei)
    L.dc, L.dh = ImageDraw.Draw(L.img), ImageDraw.Draw(L.hei)


def background(L, rng, W, H):
    """Mar simple y opaco: degradado turquesa -> azul marino con corrientes en remolino y rayos de luz suaves."""
    stops = [(0.0, "#4AA5AC"), (0.30, "#2B7F96"), (0.65, "#1B4F7A"), (1.0, "#0E2A4C")]

    def col_at(t):
        for (a, ca), (b, cb) in zip(stops, stops[1:]):
            if t <= b:
                u = (t - a) / (b - a)
                return M.hx(ca) * (1 - u) + M.hx(cb) * u
        return M.hx(stops[-1][1])

    L.img.paste((26, 80, 120), (0, 0, W, H))
    L.hei.paste(80, (0, 0, W, H))
    cs = [(rng.uniform(0, W), rng.uniform(0, H), rng.choice([-1, 1]), rng.uniform(80, 150)) for _ in range(6)]
    G = 96
    gy, gx = np.mgrid[0:G, 0:G]
    gx, gy = gx * W / G, gy * H / G
    vx, vy = np.zeros((G, G)), np.zeros((G, G))
    for cx, cy, sg, rr in cs:
        dx, dy = gx - cx, gy - cy
        d2 = dx * dx + dy * dy + rr * rr
        vx += -sg * dy * rr * rr / d2 / 60.0
        vy += sg * dx * rr * rr / d2 / 60.0
    vx += 1.0
    vy += 0.18 * np.sin(gx / 140.0 + gy / 220.0)   # corriente horizontal con ondulacion
    ang = np.degrees(np.arctan2(vy, vx))
    flow = lambda x, y: float(ang[int(min(max(y, 0), H - 1) * G / H), int(min(max(x, 0), W - 1) * G / W)])
    for _ in range(K['bgn']):
        x, y = rng.uniform(-40, W + 40), rng.uniform(-40, H + 40)
        t = min(max(y / H, 0.0), 1.0)
        c = col_at(t)
        r = rng.random()
        if r < 0.06:
            c = M.hx("#8FD3CF") * (1 - t * 0.6) + c * (t * 0.6)      # destellos claros
        elif r < 0.10:
            c = M.hx("#1B3F7A")                                      # ultramar profundo
        elif r < 0.115:
            c = M.hx("#C9B95A") * 0.7 + c * 0.3                      # toque amarillo (como en la noche estrellada)
        else:
            c = c * rng.uniform(0.85, 1.15)
        M.stroke(L, M.trace(x, y, flow, rng.uniform(90, 230) * (1.5 if SIMPLE else 1), 9, 0.45, rng), rng.uniform(*K['bgw']), M.jitter(c, rng, K['jit']), rng, dry=(0.15 if K['dry'] is None else K['dry']), bw=K['bw'], lift=0.5)
    # rayos de luz: cintas claras diagonales cerca de la superficie (suaves)
    for _ in range(K['rays']):
        x, y = rng.uniform(0, W), rng.uniform(-60, H * 0.40)
        pts = M.trace(x, y, lambda a, b: 66 + 14 * math.sin(b / 120.0 + a / 200.0), rng.uniform(200, 380), 12, 0.35, rng)
        c = M.hx("#9CDAD2") * 0.30 + col_at(max(y / H, 0)) * 0.70
        M.stroke(L, pts, rng.uniform(20, 38), M.jitter(c, rng, 0.03), rng, dry=0.25, bw=4, lift=0.25)
    # burbujas: espirales pequenas
    for _ in range(K['bubbles']):
        bx, by, br = rng.uniform(40, W - 40), rng.uniform(80, H - 80), rng.uniform(14, 30)
        for k in range(3):
            a0 = rng.uniform(0, math.tau)
            pts = [(bx + math.cos(a0 + s) * br * (1 - 0.15 * k), by + math.sin(a0 + s) * br * (1 - 0.15 * k)) for s in np.linspace(0, 4.6, 14)]
            M.stroke(L, pts, 6, M.jitter(M.hx("#CFEFEA"), rng, 0.03), rng, bw=2, lift=0.6)


def main():
    rng = np.random.default_rng(7)
    rgb0 = cv2.imread(SRC)[:, :, ::-1]
    g = cv2.cvtColor(rgb0, cv2.COLOR_RGB2GRAY)
    H, W = g.shape
    lines = (g < 150).astype(np.uint8)
    # --- pupila/iris: mancha oscura grande (el cierre morfologico no sirve: es un relleno, no una linea)
    blob = cv2.morphologyEx(lines, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
    lab_b, nb = ndi.label(blob)
    blob = lab_b == (1 + int(np.argmax(ndi.sum(blob, lab_b, range(1, nb + 1))))) if nb else blob > 0
    blob = ndi.binary_fill_holes(blob)
    sat = rgb0.astype(int).max(2) - rgb0.astype(int).min(2)
    iris = blob & (sat > 18)
    iris = ndi.binary_fill_holes(cv2.morphologyEx(iris.astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))) > 0)
    pupil = blob & ~iris
    thin = (lines > 0) & ~blob
    # --- regiones cerradas del cuerpo
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))
    closed = cv2.morphologyEx(thin.astype(np.uint8) | blob.astype(np.uint8), cv2.MORPH_CLOSE, ker)
    lab, n = ndi.label(closed == 0)
    outside = lab[0, 0]
    inner = (lab != outside) & (lab != 0)
    ink_soft = g < 245
    fish = inner | blob | cv2.morphologyEx(ink_soft.astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))).astype(bool)
    fish = cv2.morphologyEx(fish.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))).astype(bool) | blob
    ys, xs = np.nonzero(iris)
    icx, icy = (xs.mean(), ys.mean()) if len(xs) else (880.0, 410.0)
    print("regiones:", n, "iris centro", round(icx), round(icy))

    def label_at(x, y):
        return lab[y, x]

    L = make_canvas(W, H)
    background(L, rng, W, H)
    # --- cuerpo: regiones por semilla (posiciones del dibujo original)
    seeds = {
        "sclera": ((700, 420), "sclera", flow_concentric(icx, icy), (14, 26, 70, 150)),
        "fin_top": ((640, 262), "orange", flow_radial(700, 330), (12, 22, 60, 130)),
        "fin_big": ((330, 405), "red", flow_radial(590, 490), (14, 26, 80, 170)),
        "f7": ((365, 470), "orange", flow_radial(590, 490), (12, 22, 60, 130)),
        "f8": ((250, 465), "sumi", flow_radial(590, 490), (10, 18, 40, 90)),
        "f10": ((395, 545), "shiro_o", flow_radial(590, 490), (12, 22, 60, 130)),
        "f12": ((455, 600), "shiro", flow_radial(590, 490), (10, 20, 50, 110)),
        "f14": ((385, 650), "orange", flow_radial(590, 490), (10, 20, 50, 110)),
        "f15": ((490, 700), "red", flow_radial(590, 490), (12, 24, 70, 150)),
        "f16": ((420, 730), "shiro", flow_radial(590, 490), (10, 20, 50, 110)),
        "f17": ((362, 712), "red", flow_radial(590, 490), (8, 16, 36, 80)),
        "f13": ((720, 605), "orange", lambda x, y: 90 + 20 * math.sin(y / 60.0), (8, 16, 36, 80)),
    }
    used = np.zeros((H, W), bool)
    for key, ((sx, sy), pal, flow, (wlo, whi, llo, lhi)) in seeds.items():
        lb = label_at(sx, sy)
        if lb == outside or lb == 0:
            print("semilla fuera de region:", key)
            continue
        m = lab == lb
        used |= m
        paint_region(L, m, PAL[pal], rng, flow, wlo, whi, llo, lhi, curv=0.35)
    # --- parches kohaku en el globo ocular (hi) y una mancha sumi, siguiendo la curvatura
    sc = (lab == label_at(700, 420))
    yy, xx = np.mgrid[0:H, 0:W]
    def blobmask(cx, cy, r, ph):
        th = np.arctan2(yy - cy, xx - cx)
        rr = r * (1 + 0.28 * np.sin(3 * th + ph) + 0.16 * np.sin(5 * th + 2 * ph) + 0.08 * np.sin(9 * th))
        return np.hypot(xx - cx, yy - cy) < rr
    patch1 = sc & blobmask(655, 335, 90, 0.4)
    patch2 = sc & blobmask(775, 525, 62, 2.1)
    patch3 = sc & blobmask(680, 450, 20, 1.0) & False
    paint_region(L, patch1, PAL["red"], rng, flow_concentric(icx, icy), 12, 22, 50, 110, curv=0.3, density=1.3, grow=0)
    paint_region(L, patch2, PAL["orange"], rng, flow_concentric(icx, icy), 12, 22, 50, 110, curv=0.3, density=1.2, grow=0)
    # --- resto del pez (tentaculos largos, filamentos): degradado naranja -> shiro -> hi segun la altura
    rest = fish & ~used & ~blob
    wob = 45 * (M.smooth_noise(rng, 3, 2) if False else np.sin(xx / 37.0 + yy / 53.0))
    for (ya, yb, pal) in ((0, 560, "orange"), (560, 900, "shiro_o"), (900, H, "red")):
        band = rest & (yy + wob >= ya - 40) & (yy + wob < yb + 40)
        paint_region(L, band, PAL[pal], rng, lambda x, y: 90 + 28 * math.sin(y / 85.0 + 0.5), 8, 16, 50, 120, curv=0.2, density=1.4, grow=1)
    # --- iris (oro, trazos radiales como un sol) y pupila (casi negra con azul)
    paint_region(L, iris, [GOLD, "#C98E22", GOLD, GOLD2, HI3], rng, lambda x, y: math.degrees(math.atan2(y - icy, x - icx)), 6, 12, 18, 34, curv=0.1, density=1.4, grow=0)
    paint_region(L, pupil, ["#07090F", "#10131C", "#1A2030", "#2A3A5A", "#2E5A5A"], rng, flow_concentric(icx, icy, 3), 10, 20, 50, 110, curv=0.25, density=1.2, grow=0)
    # destello de la pupila (como en el dibujo: pequeno, arriba a la izquierda del iris)
    M.stroke(L, [(icx - 22, icy - 26), (icx - 10, icy - 34), (icx + 4, icy - 36)], 7, M.hx("#F6EFE2"), rng, bw=2, lift=1.0)
    img = M.finish(L, K['finish'])
    arr = np.asarray(img).astype(float)
    # --- tinta del line art encima (multiplicar): contornos y sombreado; la pupila/iris quedan sin multiplicar
    ink = g.astype(float) / 255.0
    ink[blob] = 1.0
    ink = np.where(thin, ink ** 0.9, ink)
    arr *= ink[..., None]
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(OUT)
    print("guardado", OUT)


if __name__ == "__main__":
    main()
