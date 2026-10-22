"""[V2 EXPRESIVA] Repinta los atlas de los NPC (skin / clothes / hair) con pinceladas Van Gogh SIN cambiar sus colores.

Uso:  python -I Tools/npc_pipeline/paint_npc_textures.py [Prefijo ...]      (por defecto los 10)
Entrada: ArtSource/NPC/<Carpeta>/Textures/T_<Pre>_<skin|clothes|hair>.png   (no se modifican)
Salida : ArtSource/NPC/Painted_Textures/<Carpeta>/T_<Pre>_<kind>_VG2.png  y  H_<Pre>_<kind>.png (relieve)
Idea: cada trazo es una MODULACION (tono +-, matiz minimo) multiplicada sobre el color original -> el color de cada prenda,
la piel, las manchas y los parches se conservan; solo se anade pincelada + impasto. Piel casi imperceptible (la cara se lee), ropa media, pelo fuerte.
"""
import math
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Tools", "museum_models"))
import make_painted_textures as M  # noqa: E402

NPC = os.path.join(ROOT, "ArtSource", "NPC")
FOLDERS = {"Caf": "Cafe", "Cou": "Courier", "Cur": "Curator", "Doc": "Docent", "Gar": "Gardener", "Gen": "Gentleman",
           "Grd": "Guard", "Pnt": "Painter", "Stu": "Student", "Tou": "Tourist"}
# amp = variacion de tono; chroma = variacion calido/frio; w, ln = ancho/largo de trazo (px); k = relieve; dens = cobertura
STYLE = {
    # amp = variacion de tono; camp = acentos de color (calido/frio/complementario); add = elevacion aditiva (oscuros ganan matiz); k = relieve (impasto)
    "skin": dict(amp=0.07, camp=0.7, add=3.0, acc=0.18, w=(16, 34), ln=(50, 130), k=0.10, dens=1.0, ang=lambda x, y: 35 + 25 * math.sin(x / 150.0 + y / 190.0), bj=0.03),
    "clothes": dict(amp=0.15, camp=0.75, add=6.0, acc=0.28, w=(28, 64), ln=(110, 280), k=0.17, dens=1.0, ang=lambda x, y: 90 + 22 * math.sin(x / 170.0 + y / 260.0), bj=0.05),
    "hair": dict(amp=0.17, camp=0.8, add=6.0, acc=0.26, w=(16, 34), ln=(120, 260), k=0.18, dens=0.9, ang=lambda x, y: 90 + 24 * math.sin(x / 120.0 + y / 170.0), bj=0.05),
}
# acentos de la paleta del proyecto (ART_DIRECTION.md) en RGB 0-1: cerulean, amarillo calido, oliva, terracota, azul grisaceo
ACCENTS = [(0.32, 0.42, 0.51), (0.83, 0.65, 0.17), (0.40, 0.47, 0.35), (0.66, 0.37, 0.28), (0.45, 0.47, 0.51)]
# pelo/ropa aun mas planos en casos concretos (lila y boina): multiplicador sobre amp y k
FLAT = {("Stu", "hair"): 0.6, ("Pnt", "hair"): 0.8}


def paint(src_path, out_img, out_h, kind, seed):
    st = dict(STYLE[kind])
    f = FLAT.get((os.path.basename(src_path).split("_")[1], kind), 1.0)
    st["amp"] *= f; st["k"] *= f
    rng = np.random.default_rng(seed)
    src = Image.open(src_path)
    a = None
    if src.mode == "RGBA":
        a = src.getchannel("A")
    rgb = np.asarray(src.convert("RGB")).astype(float)
    Hh, Ww = rgb.shape[:2]
    L = M.Layer(size=(Ww, Hh))
    L.img.paste((128, 128, 128), (0, 0, Ww, Hh))
    L.hei.paste(90, (0, 0, Ww, Hh))
    wm = 0.5 * (st["w"][0] + st["w"][1])
    lm = 0.5 * (st["ln"][0] + st["ln"][1])
    n = int(Ww * Hh / (wm * lm * 0.45) * st["dens"])
    for _ in range(n):
        x, y = rng.uniform(0, Ww), rng.uniform(0, Hh)
        u = float(np.clip(rng.normal(0, 0.6), -1, 1))
        acc = np.zeros(3)
        if rng.random() < st["acc"]:      # trazo de acento: tira del color hacia un tono de la paleta (el valor/luz se conserva)
            c = np.array(ACCENTS[rng.integers(len(ACCENTS))]) - 0.5
            acc = c / max(np.abs(c).max(), 1e-6) * rng.uniform(0.5, 1.0) * st["camp"]
        else:                             # variacion calido/fria suave
            t = rng.uniform(-1, 1) * 0.35
            acc = np.array([t, 0.0, -t])
        col = tuple(int(np.clip(128 + 127 * (u + acc[k]), 0, 255)) for k in range(3))
        pts = M.trace(x, y, st["ang"], rng.uniform(*st["ln"]), 9, 0.4, rng)
        M.stroke(L, pts, rng.uniform(*st["w"]), col, rng, dry=0.12, bw=4, bjit=st["bj"])
    mod = (np.asarray(L.img).astype(float) - 128.0) / 127.0
    out = rgb * (1.0 + mod * st["amp"]) + mod * st["add"]
    hei = np.asarray(L.hei.filter(M.ImageFilter.GaussianBlur(0.8)), float)
    gx = (np.roll(hei, -1, 1) - np.roll(hei, 1, 1)) / 2
    gy = (np.roll(hei, -1, 0) - np.roll(hei, 1, 0)) / 2
    sh = np.clip((gx * -1 + gy * -1) / 1.414 / 22.0, -1, 1) * st["k"]
    out = out * (1 + sh[..., None])
    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    if a is not None:
        im.putalpha(a)
    os.makedirs(os.path.dirname(out_img), exist_ok=True)
    im.save(out_img)
    L.hei.save(out_h)


def main():
    pres = sys.argv[1:] or list(FOLDERS)
    for pre in pres:
        fol = FOLDERS[pre]
        for kind in ("skin", "clothes", "hair"):
            src = os.path.join(NPC, fol, "Textures", f"T_{pre}_{kind}.png")
            if not os.path.exists(src):
                print("falta", src)
                continue
            paint(src, os.path.join(NPC, "Painted_Textures", fol, f"T_{pre}_{kind}_VG2.png"),
                  os.path.join(NPC, "Painted_Textures", fol, f"H2_{pre}_{kind}.png"), kind, sum(map(ord, pre + kind)))
            print("ok", pre, kind)


if __name__ == "__main__":
    main()
