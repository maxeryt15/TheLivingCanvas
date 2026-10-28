"""Pasos 4 y 5: genera una textura TILEABLE de pinceladas a partir de un estilo y la compara con las referencias.

Uso (desde la raiz del proyecto):
  python Tools/brushstyle/paint.py sky_swirl                       # desde cero, con la paleta del proyecto
  python Tools/brushstyle/paint.py foliage --base T_Leaves.png     # "re-traza" una textura pintada por el usuario
  Opciones: --size 1024  --seed 1  --no-compare
  Solo con --base: --follow 0.6 (0 = flujo del tema, 1 = direccion de los trazos de la textura)
                   --amount 1.0 (opacidad de los trazos nuevos sobre el original)
                   --edge-de 25 (salto de color que el trazo no cruza: juntas de piedra, bordes de hoja)

Lee ArtSource/BrushRefs/styles/<tema>.json (+ <tema>.overrides.json si existe).
Con --base escribe en ArtSource/BrushStyle/restroke/<Nombre>/ (T_<Nombre>_*.png, compare_<Nombre>.png) y no toca
las texturas del tema. Sin --base escribe en ArtSource/BrushStyle/<tema>/:
  T_<Tema>_Albedo.png   color
  T_<Tema>_Height.png   relieve (16 bit) para impasto
  T_<Tema>_Normal.png   normal tangente (OpenGL, Y+) calculada del relieve
  T_<Tema>_Brush.png    relieve centrado en gris 0.5 -> _BrushMap de TLC/Painterly (rompe el borde de la sombra)
  <tema>_Krita.ora      capas: GUIA_flujo (oculta), trazos, relieve (oculta) -> para seguir pintando a mano
  compare_<tema>.png    referencias | textura | 2x2 (tileado) | medidas de referencia vs medidas de la textura

Como funciona (todo periodico en N px, por eso tilea):
  1. Campo de flujo = deriva suave de fondo + remolinos (tangentes a circulos, con caida gaussiana).
  2. Fondo de color = manchas grandes mezclando la paleta (o la textura base del usuario).
  3. Trazos: cada uno sigue el flujo con su propio desvio (jitter), curva (bend) y temblor; ancho con carga de
     pintura al inicio y punta que se seca; vetas de cerdas; recoge un poco del color de debajo (pintura humeda).
  4. Relieve: cada trazo deja pasta con bordes levantados y surcos de cerdas; los trazos se apilan en parte.
"""
import argparse
import json
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "Tools"))
from make_prototype_textures import FONT, FONT_S, new_layer, write_ora  # noqa: E402

REFS = os.path.join(ROOT, "ArtSource", "BrushRefs")
STYLES = os.path.join(REFS, "styles")
OUT_ROOT = os.path.join(ROOT, "ArtSource", "BrushStyle")
STEP = 3.0   # paso (px) al seguir el flujo


# ------------------------------------------------------------------ utilidades
def hex_to_lab(h):
    rgb = np.array([[[int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]]], np.float32)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2Lab)[0, 0]


def lab_to_rgb8(lab):
    rgb = cv2.cvtColor(lab.astype(np.float32), cv2.COLOR_Lab2RGB)
    return (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)


def periodic_noise(n, scale, rng, octaves=3):
    """Ruido suave tileable: suma de senos con frecuencias enteras (por eso cierra en los bordes). Rango ~ -1..1."""
    y, x = np.mgrid[0:n, 0:n].astype(np.float32) / n
    out = np.zeros((n, n), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        f = scale * (2 ** o)
        for _ in range(4):
            fx, fy = rng.integers(-f, f + 1, 2)
            if fx == 0 and fy == 0:
                fx = f
            out += amp * np.sin(2 * np.pi * (fx * x + fy * y) + rng.uniform(0, 2 * np.pi))
        tot += amp * 2.0
        amp *= 0.5
    return out / tot * 1.8


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def load_style(theme):
    style = json.load(open(os.path.join(STYLES, f"{theme}.json"), encoding="utf-8"))
    g = style["generator"]
    ov = os.path.join(STYLES, f"{theme}.overrides.json")
    if os.path.exists(ov):
        g.update(json.load(open(ov, encoding="utf-8")))
        print("Aplicados retoques de", ov)
    return style, g


# ------------------------------------------------------------------ campos
def flow_field(n, g, rng):
    """Angulo del flujo en cada px + lista de remolinos (para la guia)."""
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    base = rng.uniform(0, 2 * np.pi)   # se sortea siempre para no cambiar la secuencia aleatoria de otros temas
    if g.get("direction_deg") is not None:
        base = math.radians(g["direction_deg"]) + np.pi * rng.integers(2)  # trazo axial: da igual el sentido
    alpha = base + g.get("drift_amount", 0.9) * periodic_noise(n, g["drift_scale"], rng, octaves=2)
    vx, vy = np.cos(alpha), np.sin(alpha)
    swirls = []
    spin_main = rng.choice([-1, 1])
    for _ in range(g["swirls"]):
        cx, cy = rng.uniform(0, n, 2)
        R = g["swirl_radius_rel"] * n * rng.uniform(0.75, 1.3)
        spin = spin_main if rng.random() < g["swirl_same_spin"] else -spin_main
        dx = (x - cx + n / 2) % n - n / 2     # distancia minima con bordes envueltos (tileable)
        dy = (y - cy + n / 2) % n - n / 2
        r = np.sqrt(dx * dx + dy * dy) + 1e-3
        w = 3.0 * np.exp(-(r / R) ** 2)
        vx += w * spin * -dy / r
        vy += w * spin * dx / r
        swirls.append((cx, cy, R, spin))
    return np.arctan2(vy, vx).astype(np.float32), swirls


def load_base(path, n):
    """Textura del usuario en Lab: original, suavizada (color de los trazos), muy suavizada (zonas que el trazo no
    cruza) y direccion de sus propios trazos (structure tensor del analizador, en angulo doble porque es axial)."""
    import analyze as A
    im = Image.open(path).convert("RGB").resize((n, n), Image.LANCZOS)
    rgb = np.asarray(im)
    orig = cv2.cvtColor(rgb.astype(np.float32) / 255, cv2.COLOR_RGB2Lab)
    def wrap_blur(img, sigma):   # OpenCV no acepta BORDER_WRAP en GaussianBlur: se rodea con copia envuelta
        p = int(4 * sigma) + 1
        return cv2.GaussianBlur(np.pad(img, ((p, p), (p, p), (0, 0)), mode="wrap"), (0, 0), sigma)[p:-p, p:-p]
    under = wrap_blur(orig, n * 0.004)
    region = wrap_blur(orig, n * 0.003)
    # el analizador trabaja a A.WORK px; se rodea con copia envuelta para que la direccion tilee en los bordes
    work = np.asarray(im.resize((A.WORK, A.WORK), Image.LANCZOS))
    pad = A.WORK // 8
    _, theta, coh, _ = A.fields(np.pad(work, ((pad, pad), (pad, pad), (0, 0)), mode="wrap"))
    theta, coh = theta[pad:-pad, pad:-pad], coh[pad:-pad, pad:-pad]
    c2 = cv2.resize(np.cos(2 * theta) * coh, (n, n), interpolation=cv2.INTER_LINEAR)
    s2 = cv2.resize(np.sin(2 * theta) * coh, (n, n), interpolation=cv2.INTER_LINEAR)
    return dict(img=im, orig=orig, under=under, region=region, c2=c2, s2=s2)


def match_original(g, base, amount):
    """Acerca el trazo del tema al de la propia textura (medido con el analizador). Para texturas de veta larga y recta
    (madera, corteza, metal) el trazo del tema (corto y curvo) rompia la veta en garabatos."""
    import analyze as A
    m, _ = A.analyze(dict(name="base", img=base["img"].resize((A.WORK, A.WORK), Image.LANCZOS), weight=1.0))
    target = {"aspect": m["aspect"] * 0.8,                       # mismo x0.8 calibrado que profile.py
              "bend_radius_rel_width": m["curve_radius_rel_width"],
              "jitter_deg": m["jitter_deg"],
              "stroke_width_rel": m["width_rel"] * 0.9}
    for k, v in target.items():
        if v is not None:
            g[k] = round(g[k] + (v - g[k]) * amount, 4)
    base["along"] = True
    print("Trazo ajustado a la textura:", {k: g[k] for k in target})


def follow_structure(field, base, follow):
    """Mezcla el flujo del tema con la direccion de los trazos de la textura (donde es coherente). Resultado axial."""
    strength = np.clip(np.hypot(base["c2"], base["s2"]) / 0.5, 0, 1)
    if base.get("along"):
        # vetas: donde la textura no tiene direccion clara manda el tema. Sin esto, con follow 1 esos huecos daban
        # direcciones al azar y salian trazos largos cruzando la veta.
        w_theme = 1 - follow * strength
        c2 = w_theme * np.cos(2 * field) + follow * strength * base["c2"] / (np.hypot(base["c2"], base["s2"]) + 1e-6)
        s2 = w_theme * np.sin(2 * field) + follow * strength * base["s2"] / (np.hypot(base["c2"], base["s2"]) + 1e-6)
        return (0.5 * np.arctan2(s2, c2)).astype(np.float32)
    c2 = (1 - follow) * np.cos(2 * field) + follow * strength * base["c2"] / (np.hypot(base["c2"], base["s2"]) + 1e-6)
    s2 = (1 - follow) * np.sin(2 * field) + follow * strength * base["s2"] / (np.hypot(base["c2"], base["s2"]) + 1e-6)
    return (0.5 * np.arctan2(s2, c2)).astype(np.float32)


def underpaint(n, g, rng, base):
    """Color de fondo en Lab: manchas grandes de la paleta, o la textura del usuario suavizada."""
    if base:
        return base["under"]
    pal = np.array([hex_to_lab(h) for h in g["palette"]], np.float32)
    prior = 1.0 / (1 + np.arange(len(pal)))             # la paleta va de mas presente a menos
    logits = np.stack([3.0 * periodic_noise(n, g["palette_scale"], rng) + math.log(p) for p in prior])
    w = np.exp(logits - logits.max(0))
    w /= w.sum(0)
    return np.tensordot(w.transpose(1, 2, 0), pal, axes=([2], [0])).astype(np.float32)


# ------------------------------------------------------------------ trazos
def trace_stroke(field, n, p, length, offset, bend, wiggle, rng, axial=False, stop=None):
    """Polilinea que sigue el flujo: primero hacia atras media longitud, luego hacia delante la longitud entera.
    axial: el campo no tiene sentido (0 = 180 grados); se elige el sentido mas parecido al paso anterior.
    stop(q) -> True corta el trazo (p. ej. al llegar a una junta de la textura del usuario)."""
    steps = max(3, int(length / STEP))

    def heading(q, s, sign):
        a = field[int(q[1]) % n, int(q[0]) % n] + offset
        return a + (0 if sign > 0 else np.pi) + sign * bend * s

    def keep_sense(a, prev):
        return a + np.pi if axial and prev is not None and math.cos(a - prev) < 0 else a

    q, prev = np.array(p, np.float64), None
    for i in range(steps // 2):           # retroceder hasta el inicio del trazo
        a = keep_sense(heading(q, i * STEP, -1), prev)
        nq = q + STEP * np.array([math.cos(a), math.sin(a)])
        if stop is not None and stop(nq):
            break
        q, prev = nq, a
    prev = None if prev is None else prev + np.pi
    pts, turn = [q.copy()], 0.0
    for i in range(steps):
        turn += rng.normal(0, wiggle)
        a = keep_sense(heading(q, i * STEP, 1) + turn, prev)
        nq = q + STEP * np.array([math.cos(a), math.sin(a)])
        if stop is not None and stop(nq):
            break
        q, prev = nq, a
        pts.append(q.copy())
    if len(pts) < 2:                      # trazo encerrado entre juntas: un toque minimo
        pts.append(pts[0] + 0.5 * STEP * np.array([math.cos(field[int(p[1]) % n, int(p[0]) % n]),
                                                    math.sin(field[int(p[1]) % n, int(p[0]) % n])]))
    return np.array(pts)


def stroke_geometry(pts, pad):
    """Para cada px de la caja del trazo: distancia a la polilinea, posicion a lo largo (0..1) y a lo ancho (con signo)."""
    x0, y0 = np.floor(pts.min(0) - pad).astype(int)
    x1, y1 = np.ceil(pts.max(0) + pad).astype(int)
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    P = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    A, B = pts[:-1].astype(np.float32), pts[1:].astype(np.float32)
    AB = B - A
    seg_len = np.linalg.norm(AB, axis=1) + 1e-6
    AP = P[:, None, :] - A[None]
    t = np.clip((AP * AB[None]).sum(2) / (seg_len ** 2)[None], 0, 1)
    C = A[None] + t[..., None] * AB[None]
    d = np.linalg.norm(P[:, None, :] - C, axis=2)
    j = d.argmin(1)
    k = np.arange(len(P))
    dist = d[k, j]
    cum = np.concatenate([[0], np.cumsum(seg_len)])
    u = (cum[j] + t[k, j] * seg_len[j]) / cum[-1]
    cross = AB[j, 0] * AP[k, j, 1] - AB[j, 1] * AP[k, j, 0]
    side = np.sign(cross) * dist
    shape = ys.shape
    return (x0, y0, x1, y1), dist.reshape(shape), u.reshape(shape), side.reshape(shape)


def paint(n, g, rng, base=None, follow=0.6, edge_de=25.0):
    field, swirls = flow_field(n, g, rng)
    under = underpaint(n, g, rng, base)
    stop = None
    if base:
        field = follow_structure(field, base, follow)
        region = base["region"]
        canvas = base["orig"].copy()       # donde no cae trazo queda el original con todo su detalle
    else:
        canvas = under.copy()
    height = np.zeros((n, n), np.float32)
    w0 = g["stroke_width_rel"] * n
    count = int(g["coverage"] * n * n / (w0 * w0 * g["aspect"]))
    jit = math.radians(g["jitter_deg"])
    dE = g["neighbour_dE"] * (0.5 if base else 1.0)   # con textura del usuario se respeta mas su color
    imp, bri = g["impasto"], g["bristles"]
    pal = np.array([hex_to_lab(h) for h in g["palette"]], np.float32)
    pal_p = 1.0 / (1 + np.arange(len(pal)))
    pal_p /= pal_p.sum()
    strokes = []
    for _ in range(count):
        p = rng.uniform(0, n, 2)
        w = w0 * math.exp(rng.normal(0, g["width_jitter"]))
        L = g["aspect"] * w * math.exp(rng.normal(0, g["length_jitter"]))
        same = rng.random() < 0.5 + g["bend_same_side"] / 2
        bend = (1 if same else -1) * rng.uniform(0.2, 0.7) / (g["bend_radius_rel_width"] * w)
        if base:
            c0 = region[int(p[1]) % n, int(p[0]) % n]
            stop = lambda q, c0=c0: np.linalg.norm(region[int(q[1]) % n, int(q[0]) % n] - c0) > edge_de  # noqa: E731
        pts = trace_stroke(field, n, p, L, rng.normal(0, jit), bend, jit * 0.5, rng, axial=bool(base), stop=stop)
        (x0, y0, x1, y1), dist, u, side = stroke_geometry(pts, w)
        # ancho: carga de pintura al inicio, se afina y seca hacia la punta; borde irregular
        hw = 0.5 * w * (0.85 + 0.15 * np.sin(np.pi * np.clip(u * 1.4, 0, 1))) * (1 - 0.45 * smoothstep(0.55, 1.0, u))
        hw *= 1 + 0.08 * np.sin(u * L / (0.7 * w) + rng.uniform(0, 6.3))
        a = smoothstep(hw, hw - 0.9, dist)
        v = np.clip(side / np.maximum(hw, 1e-3), -1, 1)      # -1..1 a lo ancho
        fr = rng.uniform(7, 16, 3)
        ph = rng.uniform(0, 6.3, 3)
        bristle = (sum(np.sin(f * np.pi * v + q) for f, q in zip(fr, ph)) / 3) * 0.5 + 0.5
        a *= 1 - 0.5 * bri * smoothstep(0.75, 1.0, u) * (bristle < 0.4)   # pincel seco en la cola
        if a.max() <= 0.01:
            continue
        rows, cols = np.arange(y0, y1) % n, np.arange(x0, x1) % n
        ix = np.ix_(rows, cols)
        if base:   # el ancho del trazo tampoco cruza la junta: se recorta donde la zona cambia de color
            a = a * smoothstep(edge_de, edge_de * 0.6, np.linalg.norm(region[ix] - c0, axis=2))
            if a.max() <= 0.01:
                continue
        sx, sy = int(p[0]) % n, int(p[1]) % n
        # Color del trazo: el fondo empujado hacia OTRO color de la paleta (color roto dentro de la familia, sin
        # tonos ajenos) + variacion de valor. Calibrado para que vecinos difieran ~neighbour_dE en la textura final.
        if base and base.get("along"):   # vetas: el otro color sale de la MISMA veta (a lo largo, no a lo ancho)
            fa = field[sy, sx]
            t, s = rng.uniform(-3 * w, 3 * w), rng.uniform(-0.25 * w, 0.25 * w)
            ny = int(sy + t * math.sin(fa) + s * math.cos(fa)) % n
            nx = int(sx + t * math.cos(fa) - s * math.sin(fa)) % n
            src = base["orig"]
            other = src[ny, nx] if np.linalg.norm(region[ny, nx] - c0) <= edge_de else src[sy, sx]
        elif base:   # otro color de la misma zona de la textura (a pocos anchos), nunca de la otra punta
            r = max(2, int(3 * w))
            ny, nx = (sy + rng.integers(-r, r + 1)) % n, (sx + rng.integers(-r, r + 1)) % n
            src = base["orig"]   # color nitido del original: con el suavizado la re-trazada perdia contraste
            other = src[ny, nx] if np.linalg.norm(region[ny, nx] - c0) <= edge_de else src[sy, sx]
        elif g.get("palette_weighted"):
            other = pal[rng.choice(len(pal), p=pal_p)]
        else:
            other = pal[rng.integers(len(pal))]
        start = base["orig"][sy, sx] if base else under[sy, sx]
        col = start + (other - start) * rng.uniform(0.25, 0.8)
        col[0] += np.clip(rng.normal(0, dE / 1.6), -dE, dE)
        under_here = canvas[ix]
        # vetas de cerdas + un lado del trazo algo mas claro (la pasta recoge luz en un borde)
        c = col[None, None] + ((bri * 10.0 * (bristle - 0.5)) + 3.0 * v)[..., None] * np.array([1, 0, 0])
        c = c * (1 - 0.08 * u[..., None]) + under_here * (0.08 * u[..., None])     # arrastra color de debajo
        canvas[ix] = under_here * (1 - a[..., None]) + c * a[..., None]
        hs = imp * (0.55 + 0.45 * np.abs(v) ** 3) * (1 - 0.5 * u) + 0.15 * bri * (bristle - 0.5)
        height[ix] = height[ix] * (1 - a) + a * (0.4 * height[ix] + hs)
        strokes.append(pts)
    return canvas, height, field, swirls, strokes


def normal_map(height, strength=4.0):
    gx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5 * strength
    gy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5 * strength
    nrm = np.stack([-gx, gy, np.ones_like(height)], -1)   # Y+ (OpenGL, lo que espera Unity)
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    return ((nrm * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)


def guide_layer(n, field, swirls, rng):
    g = new_layer(n, n)
    d = ImageDraw.Draw(g)
    for _ in range(260):
        q = rng.uniform(0, n, 2)
        pts = [tuple(q)]
        for _ in range(40):
            a = field[int(q[1]) % n, int(q[0]) % n]
            q = q + 6 * np.array([math.cos(a), math.sin(a)])
            if not (0 <= q[0] < n and 0 <= q[1] < n):
                break
            pts.append(tuple(q))
        if len(pts) > 2:
            d.line(pts, fill=(255, 255, 255, 110), width=2)
    for cx, cy, R, spin in swirls:
        d.ellipse((cx - R * 0.5, cy - R * 0.5, cx + R * 0.5, cy + R * 0.5), outline=(0, 255, 255, 200), width=3)
    return g


# ------------------------------------------------------------------ paso 5: comparacion
def lit_preview(albedo_img, normal_rgb):
    """Vista con luz rasante desde arriba-izquierda: solo para juzgar el impasto (Unity hara su propia luz)."""
    nrm = normal_rgb.astype(np.float32) / 127.5 - 1
    light = np.array([-0.55, 0.55, 0.63], np.float32)
    light /= np.linalg.norm(light)
    shade = np.clip((nrm * light).sum(2), 0, 1)
    lit = np.asarray(albedo_img, np.float32) * (0.55 + 0.6 * shade[..., None])
    return Image.fromarray(np.clip(lit, 0, 255).astype(np.uint8))


def compare(theme, style, albedo_img, normal_rgb, out_path):
    import analyze as A
    s = A.WORK / albedo_img.width
    region = dict(name="textura", img=albedo_img.resize((A.WORK, A.WORK), Image.LANCZOS), weight=1.0)
    m, f = A.analyze(region)
    ref = style["measured"]
    keys = [("aspect", "largo/ancho"), ("curve_radius_rel_width", "radio curva / ancho"),
            ("turn_consistency", "giro mismo lado"), ("jitter_deg", "jitter (grados)"), ("coherence", "coherencia"),
            ("neighbour_dE", "contraste vecinos dE"), ("width_rel", "ancho / lado")]
    rows = [(label, ref.get(k), m.get(k)) for k, label in keys]
    rows.append(("remolinos por recorte", ref.get("swirls_per_region"), len(m["swirls"])))

    # referencias del tema (los recortes que se midieron)
    refs = [r["img"] for r in A.load_regions(theme, "vangogh")]
    H = 512
    ref_strip = Image.new("RGB", (260, H), "#202020")
    y = 0
    for im in refs[:4]:
        t = im.copy()
        t.thumbnail((260, H // 4 - 4))
        ref_strip.paste(t, (0, y))
        y += t.height + 4
    tex = albedo_img.resize((H, H), Image.LANCZOS)
    tile = Image.new("RGB", (H, H))
    half = albedo_img.resize((H // 2, H // 2), Image.LANCZOS)
    for i in range(2):
        for j in range(2):
            tile.paste(half, (i * H // 2, j * H // 2))
    strokes = Image.new("RGB", (H, H), "#111111")
    ds = ImageDraw.Draw(strokes)
    src = np.asarray(region["img"])
    sc = H / A.WORK
    for pts, wd in f["strokes"][:400]:
        if len(pts) < 4:
            continue
        x0, y0 = pts[len(pts) // 2]
        ds.line([(px * sc, py * sc) for px, py in pts], fill=tuple(int(v) for v in src[int(y0), int(x0)]),
                width=max(1, round((wd or 4) * sc * 0.8)))
    lit = lit_preview(albedo_img, normal_rgb).resize((H, H), Image.LANCZOS)
    W = 260 + 4 * (H + 10) + 470
    sheet = Image.new("RGB", (W, H + 60), "#202020")
    d = ImageDraw.Draw(sheet)
    d.text((10, 10), f"{theme}: referencias | textura generada | con relieve (luz rasante) | tileado 2x2 | "
                     f"trazos que mide el analizador en la textura", fill="white", font=FONT_S)
    x = 10
    for im in (ref_strip, tex, lit, tile, strokes):
        sheet.paste(im, (x, 45))
        x += im.width + 10
    tx = x
    d.text((tx, 45), "medida            ref     textura", fill="white", font=FONT_S)
    for i, (label, a, b) in enumerate(rows):
        fa = "-" if a is None else f"{a:.3g}"
        fb = "-" if b is None else f"{b:.3g}"
        d.text((tx, 75 + i * 28), f"{label}", fill="#dddddd", font=FONT_S)
        d.text((tx + 250, 75 + i * 28), f"{fa:>7}   {fb:>7}", fill="#dddddd", font=FONT_S)
    sheet.save(out_path)
    return rows


def compare_base(theme, style, base_img, albedo_img, normal_rgb, out_path):
    """Hoja para el modo --base: original | re-trazada | con relieve | tileado 2x2 | detalle 1:1 (arriba original,
    abajo re-trazada) + medidas del analizador en el original, en la re-trazada y en las referencias del tema."""
    import analyze as A

    def measure(img):
        m, _ = A.analyze(dict(name="t", img=img.resize((A.WORK, A.WORK), Image.LANCZOS), weight=1.0))
        return m
    mo, mr = measure(base_img), measure(albedo_img)
    ref = style["measured"]
    keys = [("aspect", "largo/ancho"), ("curve_radius_rel_width", "radio curva / ancho"),
            ("jitter_deg", "jitter (grados)"), ("coherence", "coherencia"),
            ("neighbour_dE", "contraste vecinos dE"), ("width_rel", "ancho / lado")]
    rows = [(label, mo.get(k), mr.get(k), ref.get(k)) for k, label in keys]
    H = 512
    half = albedo_img.resize((H // 2, H // 2), Image.LANCZOS)
    tile = Image.new("RGB", (H, H))
    for i in range(2):
        for j in range(2):
            tile.paste(half, (i * H // 2, j * H // 2))
    n = albedo_img.width
    box = (n // 2 - H // 2, n // 2 - H // 4, n // 2 + H // 2, n // 2 + H // 4)
    detail = Image.new("RGB", (H, H))
    detail.paste(base_img.crop(box), (0, 0))
    detail.paste(albedo_img.crop(box), (0, H // 2))
    panels = [base_img.resize((H, H), Image.LANCZOS), albedo_img.resize((H, H), Image.LANCZOS),
              lit_preview(albedo_img, normal_rgb).resize((H, H), Image.LANCZOS), tile, detail]
    W = len(panels) * (H + 10) + 10 + 520
    sheet = Image.new("RGB", (W, H + 60), "#202020")
    d = ImageDraw.Draw(sheet)
    d.text((10, 10), f"{os.path.basename(out_path)} ({theme}): original | re-trazada | con relieve (luz rasante) | "
                     f"tileado 2x2 | detalle 1:1 (arriba original, abajo re-trazada)", fill="white", font=FONT_S)
    x = 10
    for im in panels:
        sheet.paste(im, (x, 45))
        x += H + 10
    d.text((x, 45), "medida              original  re-trazada  ref tema", fill="white", font=FONT_S)
    for i, (label, a, b, c) in enumerate(rows):
        vals = ["-" if v is None else f"{v:.3g}" for v in (a, b, c)]
        d.text((x, 75 + i * 28), label, fill="#dddddd", font=FONT_S)
        d.text((x + 230, 75 + i * 28), f"{vals[0]:>7}   {vals[1]:>7}   {vals[2]:>7}", fill="#dddddd", font=FONT_S)
    sheet.save(out_path)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("theme")
    ap.add_argument("--size", type=int, help="lado en px (por defecto 1024, o el de la textura --base)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--base", help="textura pintada por el usuario: se respeta su color y se le anaden trazos")
    ap.add_argument("--follow", type=float, default=0.6, help="--base: 0 = flujo del tema, 1 = trazos de la textura")
    ap.add_argument("--amount", type=float, default=1.0, help="--base: opacidad de los trazos nuevos")
    ap.add_argument("--edge-de", type=float, default=25.0, help="--base: salto de color que el trazo no cruza")
    ap.add_argument("--set", nargs="*", default=[], metavar="CLAVE=VALOR",
                    help="retoca claves del generador solo en esta corrida (p. ej. impasto=0.3)")
    ap.add_argument("--match", type=float, default=0.0,
                    help="--base: 0 = trazo del tema, 1 = largo, curva, desvio y ancho medidos en la propia textura "
                         "(vetas: madera, corteza, metal cepillado)")
    ap.add_argument("--no-compare", action="store_true")
    args = ap.parse_args()
    style, g = load_style(args.theme)
    rng = np.random.default_rng(args.seed)
    base = None
    if args.base:
        w, h = Image.open(args.base).size
        if w != h:
            sys.exit(f"--base necesita una textura cuadrada (es {w}x{h})")
        n = args.size or w
        base = load_base(args.base, n)
        if args.match > 0:
            match_original(g, base, args.match)
        name = os.path.splitext(os.path.basename(args.base))[0]
        name = name[2:] if name.startswith("T_") else name
        out = os.path.join(OUT_ROOT, "restroke", name)
    else:
        n = args.size or 1024
        name = "".join(p.capitalize() for p in args.theme.split("_"))
        out = os.path.join(OUT_ROOT, args.theme)
    for kv in args.set:   # despues de --match: el retoque a mano siempre gana
        k, v = kv.split("=", 1)
        g[k] = json.loads(v)
    canvas, height, field, swirls, strokes = paint(n, g, rng, base, args.follow, args.edge_de)
    if base:
        canvas = base["orig"] + args.amount * (canvas - base["orig"])
    os.makedirs(out, exist_ok=True)
    albedo = Image.fromarray(lab_to_rgb8(canvas))
    albedo.save(os.path.join(out, f"T_{name}_Albedo.png"))
    h = (height - height.min()) / (np.ptp(height) + 1e-6)
    Image.fromarray((h * 65535).astype(np.uint16)).save(os.path.join(out, f"T_{name}_Height.png"))
    # Brush map para TLC/Painterly (_BrushMap: gris, 0.5 = neutro): el relieve centrado en 0.5
    brush = np.clip(0.5 + (h - h.mean()) / (h.std() * 4 + 1e-6) * 0.7, 0, 1)
    Image.fromarray((brush * 255 + 0.5).astype(np.uint8)).save(os.path.join(out, f"T_{name}_Brush.png"))
    normal = normal_map(h * 6.0)
    Image.fromarray(normal).save(os.path.join(out, f"T_{name}_Normal.png"))
    hl = Image.fromarray((h * 255).astype(np.uint8)).convert("RGBA")
    layers = [("(hidden) GUIA_flujo", guide_layer(n, field, swirls, rng)), ("trazos", albedo.convert("RGBA")),
              ("(hidden) relieve", hl)]
    if base:
        layers.insert(1, ("(hidden) original", base["img"].convert("RGBA")))
    write_ora(os.path.join(out, f"{name if base else args.theme}_Krita.ora"), (n, n), layers)
    print(f"{len(strokes)} trazos -> {out}")
    if base and not args.no_compare:
        rows = compare_base(args.theme, style, base["img"], albedo, normal, os.path.join(out, f"compare_{name}.png"))
        for label, a, b, c in rows:
            print(f"  {label:24s} original {a}  re-trazada {b}  ref {c}")
    elif not args.no_compare:
        rows = compare(args.theme, style, albedo, normal, os.path.join(out, f"compare_{args.theme}.png"))
        for label, a, b in rows:
            print(f"  {label:24s} ref {a}  textura {b}")


if __name__ == "__main__":
    main()
