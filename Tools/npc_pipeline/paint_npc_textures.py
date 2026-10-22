"""Repinta los atlas de los NPC (skin / clothes / hair) con pinceladas Van Gogh SIN cambiar sus colores.

Uso:  python -I Tools/npc_pipeline/paint_npc_textures.py [Prefijo ...]      (por defecto los 10)
Entrada: ArtSource/NPC/<Carpeta>/Textures/T_<Pre>_<skin|clothes|hair>.png   (no se modifican)
Salida : ArtSource/NPC/Painted_Textures/<Carpeta>/T_<Pre>_<kind>_VG.png  y  H_<Pre>_<kind>.png (relieve)
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
    "skin": dict(amp=0.035, chroma=0.012, w=(14, 24), ln=(40, 90), k=0.05, dens=0.9, ang=lambda x, y: 35 + 20 * math.sin(x / 160.0 + y / 210.0), bj=0.02),
    "clothes": dict(amp=0.07, chroma=0.015, w=(32, 52), ln=(90, 190), k=0.07, dens=0.8, ang=lambda x, y: 90 + 14 * math.sin(x / 200.0 + y / 320.0), bj=0.03),
    "hair": dict(amp=0.09, chroma=0.015, w=(18, 30), ln=(100, 220), k=0.08, dens=0.7, ang=lambda x, y: 90 + 16 * math.sin(x / 130.0 + y / 200.0), bj=0.03),
}
# pelo/ropa aun mas planos en casos concretos (lila y boina): multiplicador sobre amp y k
FLAT = {("Stu", "hair"): 0.45, ("Pnt", "hair"): 0.8}


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
        u = float(np.clip(rng.normal(0, 0.55), -1, 1))
        t = rng.uniform(-1, 1) * st["chroma"] / max(st["amp"], 1e-6)
        g = 128 + u * 127
        col = (int(np.clip(g + 127 * t, 0, 255)), int(g), int(np.clip(g - 127 * t, 0, 255)))
        pts = M.trace(x, y, st["ang"], rng.uniform(*st["ln"]), 9, 0.4, rng)
        M.stroke(L, pts, rng.uniform(*st["w"]), col, rng, dry=0.12, bw=4, bjit=st["bj"])
    mod = (np.asarray(L.img).astype(float) - 128.0) / 127.0
    out = rgb * (1.0 + mod * st["amp"] / 1.0 * 1.0)
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
            paint(src, os.path.join(NPC, "Painted_Textures", fol, f"T_{pre}_{kind}_VG.png"),
                  os.path.join(NPC, "Painted_Textures", fol, f"H_{pre}_{kind}.png"), kind, sum(map(ord, pre + kind)))
            print("ok", pre, kind)


if __name__ == "__main__":
    main()
