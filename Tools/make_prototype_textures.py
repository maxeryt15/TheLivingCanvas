"""Genera las texturas PLACEHOLDER pintadas y las PLANTILLAS de Krita (.ora) del prototipo artistico.

Uso (desde la raiz del proyecto):  python Tools/make_prototype_textures.py

Salidas:
  Assets/_TheLivingCanvas/Art/Textures/Painted/T_*.png   -> lo que usa Unity. Tu las SOBRESCRIBES con las tuyas
                                                             (mismo nombre y tamano) y Unity las recarga solo.
  ArtSource/Templates/T_*_TEMPLATE.ora                    -> plantillas para Krita (capas: GUIDE, paint_here, base).

Los placeholders estan hechos con trazos con direccion (no ruido): sirven para ver el estilo, no para quedarse.
Las formas de hoja/petalo (shape) deben coincidir con PrototypeMeshes.cs.
"""
import math
import os
import zipfile
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_TEX = os.path.join(ROOT, "Assets", "_TheLivingCanvas", "Art", "Textures", "Painted")
OUT_TPL = os.path.join(ROOT, "ArtSource", "Templates")
os.makedirs(OUT_TEX, exist_ok=True)
os.makedirs(OUT_TPL, exist_ok=True)

# Paleta inicial (ART_DIRECTION.md)
CERULEAN = (82, 106, 131)
YELLOW = (212, 167, 44)
OLIVE = (101, 120, 90)
TERRACOTTA = (168, 95, 71)
GREYBLUE = (116, 121, 131)
CREAM = (224, 205, 176)

# Forma de hoja y petalo: semiancho(v) = HALF * sin(pi * v^a)^b   (v = 0 base .. 1 punta). Igual que en C#.
LEAF = dict(L=0.22, HALF=0.050, a=0.70, b=0.80)
PETAL = dict(L=0.16, HALF=0.034, a=0.90, b=0.60)

try:
    FONT = ImageFont.truetype("arial.ttf", 26)
    FONT_S = ImageFont.truetype("arial.ttf", 20)
except OSError:
    FONT = FONT_S = ImageFont.load_default()


def shape(v, p):
    return p["HALF"] * np.maximum(0, np.sin(np.pi * np.clip(v, 0, 1) ** p["a"])) ** p["b"]


def half_width_uv(v, p):
    """Semiancho en unidades de UV (la textura 1:2 cubre L/2 de ancho)."""
    return shape(v, p) / (p["L"] / 2.0)


class Canvas:
    def __init__(self, w, h, base, gray=False):
        self.w, self.h, self.gray = w, h, gray
        if gray:
            self.a = np.full((h, w), base, np.float32)
        else:
            self.a = np.zeros((h, w, 3), np.float32)
            self.a[:] = np.array(base, np.float32)

    def fill_rows(self, y0, y1, color):
        self.a[y0:y1] = np.array(color, np.float32)

    def stamp(self, rng, cx, cy, ang_deg, length, width, color, alpha, wrap=True):
        ang = math.radians(ang_deg)
        ca, sa = math.cos(ang), math.sin(ang)
        R = int(max(length, width) / 2 * 1.15) + 2
        ys, xs = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float32)
        u = xs * ca + ys * sa
        v = -xs * sa + ys * ca
        hl = length / 2.0
        t = np.clip(np.abs(u) / hl, 0, 1.2)
        taper = 0.55 + 0.45 * (1 - np.clip(t, 0, 1) ** 2)
        hw = np.maximum(width / 2.0 * taper, 0.5)
        edge = np.abs(v) / hw
        a_v = np.clip((1 - edge) * 2.5, 0, 1)
        a_u = np.clip((hl - np.abs(u)) / (hl * 0.3 + 1e-3), 0, 1)
        nb = max(4, int(width / 2))
        streak = rng.uniform(0.0, 1.0, nb + 1)
        k = np.clip((v / (width + 1e-3) + 0.5) * nb, 0, nb)
        i0 = np.floor(k).astype(int)
        i1 = np.minimum(i0 + 1, nb)
        f = k - i0
        s = streak[i0] * (1 - f) + streak[i1] * f
        a = (a_v * a_u * (0.62 + 0.38 * s) * alpha).astype(np.float32)
        yi = (np.arange(-R, R + 1) + int(cy))
        xi = (np.arange(-R, R + 1) + int(cx))
        if wrap:
            yi, xi = yi % self.h, xi % self.w
        else:
            ym = (yi >= 0) & (yi < self.h)
            xm = (xi >= 0) & (xi < self.w)
            yi, xi = yi[ym], xi[xm]
            a = a[np.ix_(ym, xm)]
        sub = self.a[np.ix_(yi, xi)]
        if self.gray:
            self.a[np.ix_(yi, xi)] = sub * (1 - a) + color * a
        else:
            self.a[np.ix_(yi, xi)] = sub * (1 - a[..., None]) + np.array(color, np.float32) * a[..., None]

    def image(self):
        arr = np.clip(self.a, 0, 255).astype(np.uint8)
        return Image.fromarray(arr, "L" if self.gray else "RGB")


def vary(rng, color, amt=0.18, hue=0.0):
    c = np.array(color, np.float32) * (1 + rng.uniform(-amt, amt))
    if hue:
        c = c + rng.uniform(-hue, hue, 3)
    return tuple(np.clip(c, 0, 255))


def mix(a, b, t):
    return tuple(np.array(a, np.float32) * (1 - t) + np.array(b, np.float32) * t)


# ---------------------------------------------------------------- placeholders
def tex_brush(rng):
    c = Canvas(512, 512, 128.0, gray=True)
    for _ in range(420):
        val = 128 + rng.choice([-1, 1]) * rng.uniform(25, 75)
        c.stamp(rng, rng.uniform(0, 512), rng.uniform(0, 512), rng.uniform(-14, 14),
                rng.uniform(110, 300), rng.uniform(8, 26), val, rng.uniform(0.45, 0.8))
    return c.image()


def tex_wood_floor(rng):
    n, plank = 1024, 256
    base = [(132, 86, 58), (150, 98, 66), (122, 80, 56), (143, 92, 62)]
    c = Canvas(n, n, (0, 0, 0))
    for i, b in enumerate(base):
        c.fill_rows(i * plank, (i + 1) * plank, b)
    for _ in range(1300):
        row = rng.integers(0, 4)
        cy = row * plank + rng.uniform(8, plank - 8)
        tint = [TERRACOTTA, YELLOW, OLIVE, (70, 45, 32)][rng.choice(4, p=[0.35, 0.15, 0.1, 0.4])]
        col = mix(base[row], tint, rng.uniform(0.1, 0.4))
        c.stamp(rng, rng.uniform(0, n), cy, rng.uniform(-3, 3), rng.uniform(220, 520), rng.uniform(5, 15), vary(rng, col), rng.uniform(0.35, 0.7))
    for i in range(4):  # juntas entre tablones, a mano
        x = 0
        while x < n:
            seg = rng.uniform(90, 220)
            c.stamp(rng, x + seg / 2, i * plank + rng.uniform(-2, 2), 0, seg, rng.uniform(4, 8), (52, 32, 24), 0.85)
            x += seg * 0.9
    return c.image()


def tex_wall(rng):
    n = 1024
    c = Canvas(n, n, CREAM)
    zones = rng.uniform(-35, 75, (4, 4))  # direccion por zona, no ruido
    for _ in range(520):
        cx, cy = rng.uniform(0, n), rng.uniform(0, n)
        ang = zones[int(cy // 256) % 4, int(cx // 256) % 4] + rng.uniform(-12, 12)
        col = rng.choice(4, p=[0.45, 0.2, 0.2, 0.15])
        base = [CREAM, (236, 222, 196), mix(CREAM, GREYBLUE, 0.35), mix(CREAM, TERRACOTTA, 0.3)][col]
        c.stamp(rng, cx, cy, ang, rng.uniform(150, 330), rng.uniform(30, 75), vary(rng, base, 0.07), rng.uniform(0.22, 0.45))
    return c.image()


def tex_wood_frame(rng):
    n = 1024
    c = Canvas(n, n, (102, 66, 46))
    for _ in range(1100):
        col = mix((102, 66, 46), [TERRACOTTA, (60, 38, 28), YELLOW][rng.choice(3, p=[0.3, 0.5, 0.2])], rng.uniform(0.1, 0.4))
        c.stamp(rng, rng.uniform(0, n), rng.uniform(0, n), 90 + rng.uniform(-3, 3), rng.uniform(200, 480), rng.uniform(5, 14), vary(rng, col), rng.uniform(0.35, 0.7))
    return c.image()


def tex_leaf(rng):
    w, h = 512, 1024
    c = Canvas(w, h, OLIVE)
    for _ in range(900):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        side = 1 if x > w / 2 else -1
        fan = 1 - y / h  # mas abierto hacia la base
        ang = math.degrees(math.atan2(-math.cos(math.radians(30 + 20 * fan)), side * math.sin(math.radians(30 + 20 * fan))))
        col = mix(OLIVE, [(140, 150, 70), (70, 92, 70), TERRACOTTA, YELLOW][rng.choice(4, p=[0.4, 0.35, 0.1, 0.15])], rng.uniform(0.1, 0.45))
        c.stamp(rng, x, y, ang, rng.uniform(70, 150), rng.uniform(10, 24), vary(rng, col, 0.1), rng.uniform(0.4, 0.75), wrap=False)
    for yy in range(0, h, 60):  # nervio central
        c.stamp(rng, w / 2, yy + 30, -90, 110, rng.uniform(9, 14), (182, 188, 120), 0.8, wrap=False)
    return c.image()


def tex_petal(rng):
    w, h = 512, 1024
    c = Canvas(w, h, YELLOW)
    for _ in range(800):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        v = 1 - y / h
        fan = (x - w / 2) / (w / 2) * 12  # abanico suave desde la base
        ang = -90 + fan
        tip = [(236, 202, 96), (214, 140, 42), (176, 112, 36), (230, 190, 70)][rng.choice(4, p=[0.35, 0.25, 0.15, 0.25])]
        col = mix(YELLOW, OLIVE if v < 0.15 else tip, rng.uniform(0.15, 0.55))
        c.stamp(rng, x, y, ang, rng.uniform(90, 220), rng.uniform(10, 26), vary(rng, col, 0.08), rng.uniform(0.4, 0.75), wrap=False)
    return c.image()


def tex_painting(rng):
    w, h = 1024, 768
    c = Canvas(w, h, (122, 126, 134))
    horizon = int(h * 0.62)
    centers = [(300, 210, 1), (700, 150, -1)]
    for _ in range(1400):  # cielo arremolinado casi gris
        x, y = rng.uniform(0, w), rng.uniform(0, horizon)
        a = 0.0
        wsum = 0.0
        for cx, cy, s in centers:
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy) + 1
            tang = math.degrees(math.atan2(dy, dx)) + 90 * s
            wgt = 1.0 / d
            a += tang * wgt
            wsum += wgt
        ang = a / wsum + rng.uniform(-8, 8)
        col = mix(GREYBLUE, [(160, 160, 162), (96, 104, 118), (140, 134, 128), CERULEAN][rng.choice(4, p=[0.3, 0.3, 0.2, 0.2])], rng.uniform(0.2, 0.7))
        c.stamp(rng, x, y, ang, rng.uniform(60, 150), rng.uniform(10, 26), vary(rng, col, 0.06), rng.uniform(0.35, 0.65), wrap=False)
    c.fill_rows(horizon, h, (104, 110, 100))
    for _ in range(900):  # campo gris, trazos curvos/horizontales
        x, y = rng.uniform(0, w), rng.uniform(horizon - 6, h)
        col = mix((104, 110, 100), [GREYBLUE, (84, 92, 84), (130, 128, 118)][rng.choice(3)], rng.uniform(0.2, 0.7))
        c.stamp(rng, x, y, rng.uniform(-18, 18) + (y - horizon) * 0.03, rng.uniform(50, 140), rng.uniform(8, 20), vary(rng, col, 0.06), rng.uniform(0.4, 0.7), wrap=False)
    fx, fy = 610, 575  # la flor amarilla
    for k in range(7):
        c.stamp(rng, fx + math.sin(k) * 2, fy + 22 + k * 11, -90 + rng.uniform(-6, 6), 30, 6, vary(rng, (96, 108, 70), 0.1), 0.9, wrap=False)
    for k in range(10):
        a = k / 10 * 360
        c.stamp(rng, fx + math.cos(math.radians(a)) * 13, fy + math.sin(math.radians(a)) * 13, a, 26, 11, vary(rng, YELLOW, 0.1), 0.95, wrap=False)
    c.stamp(rng, fx, fy, 0, 12, 12, (110, 70, 30), 0.95, wrap=False)
    return c.image()


# ---------------------------------------------------------------- plantillas .ora
def new_layer(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def arrow(d, x0, y0, x1, y1, col, wd=3):
    d.line([(x0, y0), (x1, y1)], fill=col, width=wd)
    ang = math.atan2(y1 - y0, x1 - x0)
    for s in (-0.5, 0.5):
        d.line([(x1, y1), (x1 - 16 * math.cos(ang + s), y1 - 16 * math.sin(ang + s))], fill=col, width=wd)


def guide_common(g, w, h, title, lines):
    d = ImageDraw.Draw(g)
    d.rectangle([1, 1, w - 2, h - 2], outline=(0, 255, 255, 255), width=3)
    d.text((14, 10), title, fill=(255, 255, 255, 255), font=FONT, stroke_width=2, stroke_fill=(0, 0, 0, 255))
    for i, t in enumerate(lines):
        d.text((14, 44 + i * 24), t, fill=(255, 255, 255, 255), font=FONT_S, stroke_width=2, stroke_fill=(0, 0, 0, 255))
    return d


def silhouette_guide(w, h, p, title, lines):
    g = new_layer(w, h)
    veil = Image.new("RGBA", (w, h), (0, 0, 0, 120))
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    vs = np.linspace(0, 1, 120)
    hw = half_width_uv(vs, p)
    pts_r = [(w * (0.5 + hw[i]), h * (1 - vs[i])) for i in range(len(vs))]
    pts_l = [(w * (0.5 - hw[i]), h * (1 - vs[i])) for i in range(len(vs))][::-1]
    poly = pts_r + pts_l
    md.polygon(poly, fill=255)
    inv = Image.eval(mask, lambda v: 255 - v)
    g.paste(veil, (0, 0), inv)
    d = guide_common(g, w, h, title, lines)
    d.line(poly + [poly[0]], fill=(120, 255, 120, 255), width=3)
    d.line([(w / 2, h), (w / 2, 0)], fill=(255, 255, 0, 200), width=2)
    return g, d


def make_guides():
    out = {}
    # suelo de madera
    w = h = 1024
    g = new_layer(w, h)
    d = guide_common(g, w, h, "T_Wood_Floor  1024x1024  TILEABLE", [
        "4 tablones (lineas cian). Vetas en horizontal (flechas).",
        "Lo que sale por la derecha entra por la izquierda; igual arriba/abajo.",
        "Oculta/borra esta capa GUIDE antes de exportar a PNG."])
    for i in range(1, 4):
        d.line([(0, i * 256), (w, i * 256)], fill=(0, 255, 255, 255), width=2)
    for i in range(4):
        arrow(d, 80, i * 256 + 150, 380, i * 256 + 150, (255, 255, 0, 255))
    out["T_Wood_Floor"] = (g, (1024, 1024), (136, 90, 60))
    # pared
    g = new_layer(w, h)
    d = guide_common(g, w, h, "T_Wall_Plaster  1024x1024  TILEABLE", [
        "Yeso/pintura de pared: trazos anchos y sueltos, direccion cambia por zonas.",
        "Mantener valores suaves: es un fondo, no debe competir con los cuadros."])
    for (x0, y0, x1, y1) in [(120, 400, 360, 320), (600, 500, 800, 640), (300, 800, 560, 760)]:
        arrow(d, x0, y0, x1, y1, (255, 255, 0, 255))
    out["T_Wall_Plaster"] = (g, (1024, 1024), CREAM)
    # marco / madera oscura
    g = new_layer(w, h)
    d = guide_common(g, w, h, "T_Wood_Frame  1024x1024  TILEABLE", [
        "Madera oscura para marco, banco y maceta-soporte. Vetas VERTICALES (flechas).",
        "Esta textura se estira en las piezas: no pintes nudos grandes aislados."])
    for i in range(5):
        arrow(d, 100 + i * 200, 800, 100 + i * 200, 450, (255, 255, 0, 255))
    out["T_Wood_Frame"] = (g, (1024, 1024), (102, 66, 46))
    # hoja y petalo
    g, d = silhouette_guide(512, 1024, LEAF, "T_Leaf  512x1024  (NO tileable)", [
        "Verde = silueta real de la hoja (lo oscuro se recorta).",
        "Base abajo, punta arriba. Nervio central amarillo.",
        "Trazos de nervios saliendo del centro hacia la punta."])
    for yy in range(250, 950, 130):
        arrow(d, 256, yy, 400, yy - 110, (255, 255, 0, 220), 2)
        arrow(d, 256, yy, 112, yy - 110, (255, 255, 0, 220), 2)
    out["T_Leaf"] = (g, (512, 1024), OLIVE)
    g, d = silhouette_guide(512, 1024, PETAL, "T_Petal  512x1024  (NO tileable)", [
        "Verde = silueta real del petalo. Base abajo, punta arriba.",
        "Trazos radiales (abanico desde la base hacia la punta)."])
    for xx in (150, 256, 362):
        arrow(d, 256, 900, xx, 180, (255, 255, 0, 220), 2)
    out["T_Petal"] = (g, (512, 1024), YELLOW)
    # brush
    g = new_layer(512, 512)
    d = guide_common(g, 512, 512, "T_Brush_Dir  512x512  TILEABLE  (gris)", [
        "Mapa de pincelada: GRIS MEDIO (128) = neutro, claro/oscuro = trazo.",
        "Trazos horizontales; el shader lo rota con Brush rotation."])
    for i in range(3):
        arrow(d, 60, 200 + i * 90, 300, 200 + i * 90, (255, 255, 0, 255))
    out["T_Brush_Dir"] = (g, (512, 512), (128, 128, 128))
    # pintura
    g = new_layer(1024, 768)
    d = guide_common(g, 1024, 768, "T_Painting_GreyField  1024x768", [
        "Campo gris bajo cielo arremolinado; UNA flor amarilla (cruz amarilla = punto focal).",
        "Regla de tercios en cian. Que el amarillo sea lo UNICO saturado."])
    for f in (1 / 3, 2 / 3):
        d.line([(1024 * f, 0), (1024 * f, 768)], fill=(0, 255, 255, 150), width=1)
        d.line([(0, 768 * f), (1024, 768 * f)], fill=(0, 255, 255, 150), width=1)
    d.line([(0, 476), (1024, 476)], fill=(255, 128, 255, 200), width=2)
    d.line([(590, 575), (630, 575)], fill=(255, 255, 0, 255), width=3)
    d.line([(610, 555), (610, 595)], fill=(255, 255, 0, 255), width=3)
    out["T_Painting_GreyField"] = (g, (1024, 768), (122, 126, 134))
    return out


def write_ora(path, size, layers):
    """layers: lista (nombre, Image RGBA) de ARRIBA a ABAJO."""
    w, h = size
    stack = ['<?xml version="1.0" encoding="UTF-8"?>', f'<image w="{w}" h="{h}"><stack>']
    for i, (name, _) in enumerate(layers):
        vis = "hidden" if name.startswith("(hidden)") else "visible"
        stack.append(f'<layer name="{name}" src="data/layer{i}.png" x="0" y="0" opacity="1.0" visibility="{vis}" composite-op="svg:src-over"/>')
    stack.append("</stack></image>")
    merged = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for _, im in reversed(layers):
        merged = Image.alpha_composite(merged, im)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "image/openraster", compress_type=zipfile.ZIP_STORED)
        z.writestr("stack.xml", "\n".join(stack))
        for i, (_, im) in enumerate(layers):
            b = io.BytesIO(); im.save(b, "PNG"); z.writestr(f"data/layer{i}.png", b.getvalue())
        b = io.BytesIO(); merged.save(b, "PNG"); z.writestr("mergedimage.png", b.getvalue())
        t = merged.copy(); t.thumbnail((256, 256)); b = io.BytesIO(); t.save(b, "PNG"); z.writestr("Thumbnails/thumbnail.png", b.getvalue())


def main():
    rng = np.random.default_rng(1307)
    painted = {
        "T_Brush_Dir": tex_brush, "T_Wood_Floor": tex_wood_floor, "T_Wall_Plaster": tex_wall,
        "T_Wood_Frame": tex_wood_frame, "T_Leaf": tex_leaf, "T_Petal": tex_petal,
        "T_Painting_GreyField": tex_painting,
    }
    for name, fn in painted.items():
        path = os.path.join(OUT_TEX, name + ".png")
        if os.path.exists(path) and "--force" not in os.sys.argv:
            print("existe (no se pisa; usa --force):", name)
            continue
        fn(rng).save(path)
        print("placeholder:", path)
    for name, (guide, size, base) in make_guides().items():
        w, h = size
        base_layer = Image.new("RGBA", size, tuple(int(x) for x in base) + (255,))
        write_ora(os.path.join(OUT_TPL, name + "_TEMPLATE.ora"), size,
                  [("GUIDE (ocultar antes de exportar)", guide), ("paint_here", new_layer(w, h)), ("base_flat_color", base_layer)])
        print("plantilla:", name + "_TEMPLATE.ora")


if __name__ == "__main__":
    main()
