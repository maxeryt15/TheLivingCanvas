"""Re-traza todas las texturas del museo segun ArtSource/BrushRefs/families.json y arma una hoja de conjunto.

Uso (desde la raiz del proyecto):
  python Tools/brushstyle/restroke_all.py               # todas
  python Tools/brushstyle/restroke_all.py T_Fabric T_Bark   # solo esas
  Opciones: --jobs 4 (corridas en paralelo)  --sheet-only (rehace solo la hoja con lo ya generado)

Cada textura se re-traza con paint.py --base (no toca los originales de Assets/). Salida:
  ArtSource/BrushStyle/restroke/<Nombre>/   (texturas, .ora para Krita y compare_<Nombre>.png)
  ArtSource/BrushStyle/restroke/_overview.png   original | re-trazada de cada una, con familia y tema
"""
import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "Tools"))
from make_prototype_textures import FONT_S  # noqa: E402

FAMILIES = os.path.join(ROOT, "ArtSource", "BrushRefs", "families.json")
TEX_DIR = os.path.join(ROOT, "Assets", "_TheLivingCanvas", "Art", "Textures", "Painted", "Museum")
OUT = os.path.join(ROOT, "ArtSource", "BrushStyle", "restroke")


def command(tex, cfg):
    cmd = [sys.executable, os.path.join(HERE, "paint.py"), cfg["theme"], "--base", os.path.join(TEX_DIR, tex + ".png"),
           "--follow", str(cfg["follow"]), "--amount", str(cfg["amount"]), "--edge-de", str(cfg["edge_de"])]
    if cfg.get("match"):
        cmd += ["--match", str(cfg["match"])]
    if cfg.get("set"):
        cmd += ["--set"] + [f"{k}={json.dumps(v)}" for k, v in cfg["set"].items()]
    return cmd


def run(tex, cfg):
    r = subprocess.run(command(tex, cfg), cwd=ROOT, capture_output=True, text=True)
    status = "ok" if r.returncode == 0 else "ERROR"
    print(f"[{status}] {tex} ({cfg['theme']})" + ("" if r.returncode == 0 else "\n" + r.stderr[-1500:]), flush=True)
    return r.returncode == 0


def overview(textures):
    S, cols = 220, 4
    cell_w, cell_h = 2 * S + 30, S + 40
    rows = (len(textures) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w + 10, rows * cell_h + 10), "#202020")
    d = ImageDraw.Draw(sheet)
    for i, (tex, cfg) in enumerate(textures.items()):
        name = tex[2:]
        x, y = 10 + (i % cols) * cell_w, 10 + (i // cols) * cell_h
        d.text((x, y), f"{name} - {cfg['family']} / {cfg['theme']} ({cfg['shader']})", fill="white", font=FONT_S)
        orig = Image.open(os.path.join(TEX_DIR, tex + ".png")).convert("RGB").resize((S, S), Image.LANCZOS)
        sheet.paste(orig, (x, y + 30))
        res = os.path.join(OUT, name, f"T_{name}_Albedo.png")
        if os.path.exists(res):
            sheet.paste(Image.open(res).convert("RGB").resize((S, S), Image.LANCZOS), (x + S + 6, y + 30))
        else:
            d.text((x + S + 20, y + 30 + S // 2), "falta", fill="#ff8080", font=FONT_S)
    path = os.path.join(OUT, "_overview.png")
    sheet.save(path)
    print("Hoja:", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("only", nargs="*")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--sheet-only", action="store_true")
    args = ap.parse_args()
    textures = json.load(open(FAMILIES, encoding="utf-8"))["textures"]
    todo = {t: c for t, c in textures.items() if not args.only or t in args.only}
    if not args.sheet_only:
        with ThreadPoolExecutor(args.jobs) as ex:
            results = list(ex.map(lambda tc: run(*tc), todo.items()))
        print(f"{sum(results)}/{len(results)} re-trazadas")
    overview(textures)


if __name__ == "__main__":
    main()
