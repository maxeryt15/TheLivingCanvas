"""Mide el estilo de pincelada de un tema de <datos>/refs.json y escribe un perfil + hoja de verificacion.

Uso (desde la raiz del proyecto):  python analyze.py sky_swirl [--artist vangogh]

Que mide, por recorte (todo en una escala de trabajo con el lado corto = WORK px):
  - orientacion del trazo y coherencia: structure tensor sobre Lab (los trazos se separan mas por color que por luz)
  - ancho del trazo: distancia entre bordes de color a lo ancho del trazo
  - largo del trazo: cuanto se puede avanzar siguiendo la orientacion sin cambiar de color (streamline)
  - curvatura: giro por pixel a lo largo de esos streamlines, y si gira siempre hacia el mismo lado
  - jitter: cuanto se desvia cada trazo de la direccion media de sus vecinos
  - remolinos: centros donde la orientacion es tangente a circulos (centro + radio + fuerza)
  - color: paleta (k-means en Lab), rango de valor, contraste entre trazos vecinos (color roto)
El impasto (relieve) NO se mide: en una foto se confunde con trazos claros. Se ajusta a ojo en el generador.
Los tamanos absolutos dependen de la resolucion y del encuadre; lo fiable son las PROPORCIONES (largo/ancho,
radio de curva/ancho, radio de remolino/lado), que son las que usara el generador.

Salidas: <datos>/profiles/<artista>_<tema>.json y <datos>/_sheets/analyze_<tema>.png
"""
import argparse
import json
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oratools import FONT, FONT_S  # noqa: E402

DATA = os.environ.get("TVGA_DATA") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
REFS = DATA
PROFILES = os.path.join(REFS, "profiles")
SHEETS = os.path.join(REFS, "_sheets")

WORK = 400            # lado corto de trabajo (px)
TENSOR_SIGMA = 3.0    # suavizado del structure tensor: ~medio ancho de trazo a escala de trabajo
# Umbrales de color relativos al contraste propio de cada recorte (C = Delta E tipico entre trazos vecinos):
# un cielo palido (Trigal con cipreses) separa sus trazos con saltos de color mucho menores que La noche estrellada.
EDGE_K = 0.35         # salto de color por px que cuenta como borde entre trazos  = EDGE_K * C
STROKE_K = 1.0        # cambio de color desde el inicio que termina un trazo al seguirlo = STROKE_K * C
MIN_COH = 0.25        # coherencia minima para medir en un punto
N_SAMPLES = 500
rng = np.random.default_rng(7)  # semilla fija: mismas medidas en cada ejecucion


# ------------------------------------------------------------------ carga
def load_regions(theme, artist):
    data = json.load(open(os.path.join(REFS, "refs.json"), encoding="utf-8"))
    out = []
    for e in data["images"]:
        if not e.get("use", True) or (artist and e["artist"] != artist):
            continue
        path = os.path.join(REFS, e["file"])
        if not os.path.exists(path):
            print("FALTA", e["file"])
            continue
        im = Image.open(path).convert("RGB")
        for i, r in enumerate(e.get("regions", [])):
            if r["theme"] != theme:
                continue
            x0, y0, x1, y1 = r["box"]
            c = im.crop((round(x0 * im.width), round(y0 * im.height), round(x1 * im.width), round(y1 * im.height)))
            s = WORK / min(c.size)
            c = c.resize((round(c.width * s), round(c.height * s)), Image.LANCZOS)
            out.append(dict(name=f"{os.path.basename(e['file'])[:2]}#{i}", file=e["file"], box=r["box"],
                            weight=e.get("weight", 1.0) * r.get("weight", 1.0), src_scale=s, img=c))
    return out


# ------------------------------------------------------------------ campos
def fields(rgb):
    lab = cv2.cvtColor(rgb.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)  # L 0..100, a/b ~ -128..127
    lab_s = cv2.GaussianBlur(lab, (0, 0), 1.0)
    jxx = jyy = jxy = 0
    for ch in range(3):
        gx = cv2.Sobel(lab_s[..., ch], cv2.CV_32F, 1, 0, ksize=3) / 8
        gy = cv2.Sobel(lab_s[..., ch], cv2.CV_32F, 0, 1, ksize=3) / 8
        jxx, jyy, jxy = jxx + gx * gx, jyy + gy * gy, jxy + gx * gy

    def orient(sigma):
        a, b, c = (cv2.GaussianBlur(j, (0, 0), sigma) for j in (jxx, jyy, jxy))
        theta = 0.5 * np.arctan2(2 * c, a - b) + np.pi / 2           # gradiente -> direccion del trazo
        coh = np.sqrt((a - b) ** 2 + 4 * c * c) / (a + b + 1e-6)
        return theta, coh

    theta, coh = orient(TENSOR_SIGMA)
    theta_wide, _ = orient(TENSOR_SIGMA * 3)
    return lab_s, theta, coh, theta_wide


def axial_diff(a, b):
    """Diferencia entre dos orientaciones sin sentido (0..pi/2)."""
    d = np.abs((a - b + np.pi / 2) % np.pi - np.pi / 2)
    return d


def sample(arr, x, y):
    h, w = arr.shape[:2]
    return arr[min(max(int(round(y)), 0), h - 1), min(max(int(round(x)), 0), w - 1)]


# ------------------------------------------------------------------ trazos
def trace(theta, coh, lab, x, y, direction, stroke_de, max_len=400):
    """Sigue la orientacion desde (x, y) hasta que cambia el color, cae la coherencia o se sale."""
    h, w = coh.shape
    start = lab[int(y), int(x)]
    pts, dx, dy = [], math.cos(theta[int(y), int(x)]) * direction, math.sin(theta[int(y), int(x)]) * direction
    for _ in range(max_len):
        t = sample(theta, x, y)
        nx, ny = math.cos(t), math.sin(t)
        if nx * dx + ny * dy < 0:          # la orientacion no tiene sentido: mantener el de la marcha
            nx, ny = -nx, -ny
        dx, dy = nx, ny
        x, y = x + dx, y + dy
        if not (0 <= x < w - 1 and 0 <= y < h - 1) or sample(coh, x, y) < MIN_COH * 0.6:
            break
        if np.linalg.norm(sample(lab, x, y) - start) > stroke_de:
            break
        pts.append((x, y))
    return pts


def stroke_at(theta, coh, lab, x, y, stroke_de):
    back = trace(theta, coh, lab, x, y, -1, stroke_de)
    fwd = trace(theta, coh, lab, x, y, 1, stroke_de)
    return back[::-1] + [(x, y)] + fwd


def curvature(pts, step=6):
    """Giro medio por pixel (signo incluido) a lo largo de una polilinea."""
    if len(pts) < 2 * step + 1:
        return None
    p = np.array(pts[::step])
    v = np.diff(p, axis=0)
    ang = np.arctan2(v[:, 1], v[:, 0])
    turn = (np.diff(ang) + np.pi) % (2 * np.pi) - np.pi
    return turn / step


def width_at(theta, lab, x, y, edge_de, half=40):
    """Distancia mediana entre bordes de color a lo ancho del trazo."""
    t = theta[int(y), int(x)]
    px, py = -math.sin(t), math.cos(t)
    s = np.arange(-half, half + 1)
    prof = np.array([sample(lab, x + px * k, y + py * k) for k in s])
    g = np.linalg.norm(np.diff(prof, axis=0), axis=1)
    g = np.convolve(g, [0.25, 0.5, 0.25], mode="same")
    peaks = [i for i in range(1, len(g) - 1) if g[i] > edge_de and g[i] >= g[i - 1] and g[i] >= g[i + 1]]
    if len(peaks) < 2:
        return None
    return float(np.median(np.diff(peaks)))


# ------------------------------------------------------------------ remolinos
def swirls(theta, coh):
    """Centros donde la orientacion es tangente a circulos. Devuelve [(cx, cy, r, score)] en px de trabajo."""
    f = 128 / min(theta.shape)
    small_h, small_w = round(theta.shape[0] * f), round(theta.shape[1] * f)
    c2 = cv2.resize(np.cos(2 * theta).astype(np.float32), (small_w, small_h), interpolation=cv2.INTER_AREA)
    s2 = cv2.resize(np.sin(2 * theta).astype(np.float32), (small_w, small_h), interpolation=cv2.INTER_AREA)
    w = cv2.resize(coh.astype(np.float32), (small_w, small_h), interpolation=cv2.INTER_AREA)
    found = []
    for R in (14, 24, 40):
        yy, xx = np.mgrid[-R:R + 1, -R:R + 1]
        rr = np.hypot(xx, yy)
        ring = (rr >= 0.35 * R) & (rr <= R)
        ox, oy = xx[ring], yy[ring]
        tan2 = 2 * (np.arctan2(oy, ox) + np.pi / 2)        # angulo tangente, doblado
        tc, ts = np.cos(tan2), np.sin(tan2)
        for cy in range(R // 2, small_h - R // 2, 3):
            for cx in range(R // 2, small_w - R // 2, 3):
                px, py = cx + ox, cy + oy
                ok = (px >= 0) & (px < small_w) & (py >= 0) & (py < small_h)
                if ok.mean() < 0.7:
                    continue
                px, py = px[ok], py[ok]
                ww = w[py, px]
                # cos(2*(theta - tangente)) = 1 si es tangente, -1 si es radial
                align = (c2[py, px] * tc[ok] + s2[py, px] * ts[ok])
                score = float((ww * align).sum() / (ww.sum() + 1e-6))
                found.append((cx / f, cy / f, R / f, score))
    found.sort(key=lambda t: -t[3])
    keep = []
    for cx, cy, r, sc in found:
        if sc < 0.55:   # < 0.55 aparecen falsos remolinos en trazos casi paralelos (trigales)
            break
        if all(math.hypot(cx - k[0], cy - k[1]) > 0.8 * max(r, k[2]) for k in keep):
            keep.append((cx, cy, r, sc))
    return keep[:6]


# ------------------------------------------------------------------ color
def palette(lab, k=6):
    px = lab.reshape(-1, 3)[rng.choice(lab.shape[0] * lab.shape[1], 20000, replace=False)].astype(np.float32)
    _, labels, centers = cv2.kmeans(px, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.2), 3,
                                    cv2.KMEANS_PP_CENTERS)
    share = np.bincount(labels.ravel(), minlength=k) / len(labels)
    order = np.argsort(-share)
    return [(lab_to_hex(centers[i]), round(float(share[i]), 3)) for i in order]


def lab_to_hex(c):
    rgb = cv2.cvtColor(np.array([[c]], np.float32), cv2.COLOR_Lab2RGB)[0, 0]
    r, g, b = (int(round(np.clip(v, 0, 1) * 255)) for v in rgb)
    return f"#{r:02X}{g:02X}{b:02X}"


def across_dE(theta, lab, xs, ys, dist):
    """Delta E entre cada punto y el que esta a `dist` px a lo ancho del trazo."""
    out = []
    for x, y in zip(xs, ys):
        t = theta[int(y), int(x)]
        out.append(float(np.linalg.norm(sample(lab, x - math.sin(t) * dist, y + math.cos(t) * dist) - lab[int(y), int(x)])))
    return out


# ------------------------------------------------------------------ analisis de un recorte
def analyze(region):
    rgb = np.asarray(region["img"])
    lab, theta, coh, theta_wide = fields(rgb)
    h, w = coh.shape
    ys, xs = np.nonzero(coh > MIN_COH)
    idx = rng.choice(len(xs), min(N_SAMPLES, len(xs)), replace=False)
    # Contraste propio del recorte: Delta E a 6 px a lo ancho (mas o menos un trazo en la escala de trabajo)
    contrast = float(np.median(across_dE(theta, lab, xs[idx[:200]], ys[idx[:200]], 6.0)))
    edge_de, stroke_de = max(2.0, EDGE_K * contrast), max(5.0, STROKE_K * contrast)
    strokes, lengths, widths, kappas, signs = [], [], [], [], []
    for i in idx:
        x, y = float(xs[i]), float(ys[i])
        pts = stroke_at(theta, coh, lab, x, y, stroke_de)
        if len(pts) < 4:
            continue
        lengths.append(len(pts))
        wd = width_at(theta, lab, x, y, edge_de)
        if wd:
            widths.append(wd)
        k = curvature(pts)
        if k is not None and len(k):
            kappas.append(float(np.median(np.abs(k))))
            signs.append(float(np.sign(k).mean()))
        strokes.append((pts, wd))
    mask = coh > MIN_COH
    jitter = float(np.degrees(np.median(axial_diff(theta, theta_wide)[mask])))
    L = lab[..., 0]
    # Contraste entre trazos vecinos: Delta E entre puntos separados un ancho de trazo a lo ancho
    wmed = float(np.median(widths)) if widths else 8.0
    de = across_dE(theta, lab, xs[idx[:300]], ys[idx[:300]], wmed)
    sw = swirls(theta, coh)
    # Direccion dominante (sin sentido): media de exp(2i*theta) pesada por coherencia. order 1 = todo paralelo.
    z = (coh * np.exp(2j * theta)).sum() / (coh.sum() + 1e-6)
    direction = math.degrees(np.angle(z) / 2) % 180     # 0 = horizontal, 90 = vertical (y hacia abajo)
    kmed =float(np.median(kappas)) if kappas else 0.0
    lmed = float(np.median(lengths)) if lengths else 0.0
    m = dict(
        size_px=[w, h],
        stroke_width_px=round(wmed, 1),
        stroke_length_px=round(lmed, 1),
        length_p90_px=round(float(np.percentile(lengths, 90)), 1) if lengths else 0.0,
        aspect=round(lmed / wmed, 2) if wmed else None,
        width_rel=round(wmed / min(w, h), 4),
        curvature_per_px=round(kmed, 4),
        curve_radius_rel_width=round(1 / kmed / wmed, 2) if kmed > 1e-4 else None,
        turn_consistency=round(float(np.median(np.abs(signs))), 2) if signs else None,
        jitter_deg=round(jitter, 1),
        direction_deg=round(direction, 1),
        direction_order=round(float(abs(z)), 3),
        coherence=round(float(np.median(coh)), 3),
        coherent_area=round(float(mask.mean()), 3),
        swirls=[dict(cx_rel=round(cx / w, 3), cy_rel=round(cy / h, 3), radius_rel=round(r / min(w, h), 3), score=round(s, 2))
                for cx, cy, r, s in sw],
        neighbour_dE=round(float(np.median(de)), 1),
        value_p5_p95=[round(float(np.percentile(L, 5)), 1), round(float(np.percentile(L, 95)), 1)],
        thresholds_dE=dict(edge=round(edge_de, 1), stroke=round(stroke_de, 1)),
        palette=palette(lab),
    )
    return m, dict(theta=theta, coh=coh, strokes=strokes, swirls=sw)


# ------------------------------------------------------------------ perfil agregado
NUMERIC = ["stroke_width_px", "stroke_length_px", "aspect", "width_rel", "curvature_per_px", "curve_radius_rel_width",
           "turn_consistency", "jitter_deg", "coherence", "coherent_area", "neighbour_dE", "direction_order"]


def wmedian(vals, weights):
    pairs = sorted((v, w) for v, w in zip(vals, weights) if v is not None)
    if not pairs:
        return None
    tot, acc = sum(w for _, w in pairs), 0.0
    for v, w in pairs:
        acc += w
        if acc >= tot / 2:
            return v
    return pairs[-1][0]


def aggregate(results):
    ws = [r["weight"] for r in results]
    agg = {k: wmedian([r["metrics"][k] for r in results], ws) for k in NUMERIC}
    sw = [s for r in results for s in r["metrics"]["swirls"]]
    agg["swirls_per_region"] = round(len(sw) / len(results), 2)
    agg["swirl_radius_rel"] = wmedian([s["radius_rel"] for s in sw], [1] * len(sw)) if sw else None
    # direccion media entre recortes (axial), pesada por peso y por lo paralelos que son
    z = sum(r["weight"] * r["metrics"]["direction_order"] * np.exp(2j * math.radians(r["metrics"]["direction_deg"]))
            for r in results)
    agg["direction_deg"] = round(math.degrees(np.angle(z) / 2) % 180, 1)
    agg["direction_agreement"] = round(float(abs(z) / sum(r["weight"] for r in results)), 3)
    return agg


# ------------------------------------------------------------------ hoja de verificacion
def draw_sheet(theme, results, path):
    col = 300
    rows = []
    for r in results:
        img = r["region"]["img"]
        s = col / img.width
        th = (col, round(img.height * s))
        a = img.resize(th, Image.LANCZOS)
        # 2: orientacion (rayitas) + remolinos
        b = Image.blend(a, Image.new("RGB", th, "black"), 0.55)
        d = ImageDraw.Draw(b)
        f = r["fields"]
        step = 12
        for y in range(step // 2, img.height, round(step / s)):
            for x in range(step // 2, img.width, round(step / s)):
                c, t = f["coh"][y, x], f["theta"][y, x]
                L = 5 * min(1.0, c / 0.6) + 1
                cx, cy = x * s, y * s
                d.line((cx - math.cos(t) * L, cy - math.sin(t) * L, cx + math.cos(t) * L, cy + math.sin(t) * L),
                       fill=(255, int(255 * min(1, c / 0.6)), 80), width=1)
        for cx, cy, rad, sc in f["swirls"]:
            d.ellipse(((cx - rad) * s, (cy - rad) * s, (cx + rad) * s, (cy + rad) * s), outline="#00e5ff", width=2)
        # 3: trazos detectados, con su ancho medido
        c3 = Image.new("RGB", th, "#111111")
        d3 = ImageDraw.Draw(c3)
        src = np.asarray(img)
        for pts, wd in f["strokes"][:350]:
            if len(pts) < 4:
                continue
            x0, y0 = pts[len(pts) // 2]
            color = tuple(int(v) for v in src[int(y0), int(x0)])
            d3.line([(px * s, py * s) for px, py in pts], fill=color, width=max(1, round((wd or 4) * s * 0.8)))
        m = r["metrics"]
        txt = (f"{r['region']['name']}  w={r['weight']}\n"
               f"ancho {m['stroke_width_px']}px  largo {m['stroke_length_px']}px  L/A {m['aspect']}\n"
               f"radio curva {m['curve_radius_rel_width']}x ancho  giro mismo lado {m['turn_consistency']}\n"
               f"jitter {m['jitter_deg']} grad  coherencia {m['coherence']}  remolinos {len(m['swirls'])}\n"
               f"direccion {m['direction_deg']} grad (orden {m['direction_order']})\n"
               f"contraste vecinos dE {m['neighbour_dE']}  umbral borde/trazo {m['thresholds_dE']['edge']}/{m['thresholds_dE']['stroke']}")
        rows.append((a, b, c3, txt, m["palette"]))
    H = sum(max(t[0].height, 190) + 20 for t in rows) + 50
    sheet = Image.new("RGB", (col * 3 + 40 + 560, H), "#202020")
    d = ImageDraw.Draw(sheet)
    d.text((10, 10), f"analyze {theme}:  recorte | orientacion + remolinos (cian) | trazos detectados", fill="white", font=FONT)
    y = 50
    for a, b, c3, txt, pal in rows:
        for i, im in enumerate((a, b, c3)):
            sheet.paste(im, (10 + i * (col + 10), y))
        tx = 10 + 3 * (col + 10)
        d.multiline_text((tx, y), txt, fill="#dddddd", font=FONT_S, spacing=4)
        px = tx
        for hexc, share in pal:
            wsw = max(4, round(440 * share))
            d.rectangle((px, y + 160, px + wsw, y + 180), fill=hexc)
            px += wsw
        y += max(a.height, 190) + 20
    sheet.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("theme")
    ap.add_argument("--artist", default="vangogh")
    args = ap.parse_args()
    regions = load_regions(args.theme, args.artist)
    if not regions:
        sys.exit(f"Sin recortes para {args.theme} ({args.artist})")
    results = []
    for reg in regions:
        m, f = analyze(reg)
        results.append(dict(region=reg, weight=reg["weight"], metrics=m, fields=f))
        print(f"{reg['name']}: ancho {m['stroke_width_px']} largo {m['stroke_length_px']} L/A {m['aspect']} "
              f"radio {m['curve_radius_rel_width']} giro {m['turn_consistency']} jitter {m['jitter_deg']} "
              f"remolinos {len(m['swirls'])}")
    profile = dict(artist=args.artist, theme=args.theme, work_short_side_px=WORK,
                   aggregate=aggregate(results),
                   regions=[dict(name=r["region"]["name"], file=r["region"]["file"], box=r["region"]["box"],
                                 weight=r["weight"], **r["metrics"]) for r in results])
    os.makedirs(PROFILES, exist_ok=True)
    os.makedirs(SHEETS, exist_ok=True)
    out = os.path.join(PROFILES, f"{args.artist}_{args.theme}.json")
    json.dump(profile, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    draw_sheet(args.theme, results, os.path.join(SHEETS, f"analyze_{args.theme}.png"))
    print("Perfil:", out)
    print("Agregado:", json.dumps(profile["aggregate"], ensure_ascii=False))


if __name__ == "__main__":
    main()
