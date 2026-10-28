"""Hoja de verificacion de las referencias: cada imagen con sus regiones dibujadas y, por tema, los recortes juntos.
Sirve para comprobar a ojo que las cajas de refs.json caen donde deben antes de medir nada.

Uso (desde la raiz del proyecto):  python Tools/brushstyle/refs_sheet.py
Lee ArtSource/BrushRefs/refs.json. Escribe ArtSource/BrushRefs/_sheets/overview.png y theme_<tema>.png.
"""
import json
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Tools"))
from make_prototype_textures import FONT, FONT_S  # noqa: E402

REFS = os.path.join(ROOT, "ArtSource", "BrushRefs")
OUT = os.path.join(REFS, "_sheets")
THUMB = 360   # lado mayor de cada miniatura en la vista general
CROP = 300    # lado mayor de cada recorte en las hojas por tema

# Un color por tema para distinguir las cajas en la vista general
COLORS = ["#ff3b30", "#ffcc00", "#34c759", "#00c7be", "#007aff", "#af52de", "#ff2d55",
          "#ff9500", "#5ac8fa", "#a2845e", "#ffffff", "#000000", "#8e8e93"]


def fit(im, side):
    s = side / max(im.size)
    return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)


def crop(im, box):
    x0, y0, x1, y1 = box
    return im.crop((round(x0 * im.width), round(y0 * im.height), round(x1 * im.width), round(y1 * im.height)))


def grid(tiles, cols, cell_w, cell_h, title):
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, 40 + rows * cell_h), "#202020")
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), title, fill="white", font=FONT)
    for i, (img, label) in enumerate(tiles):
        x, y = (i % cols) * cell_w, 40 + (i // cols) * cell_h
        sheet.paste(img, (x + 5, y + 5))
        d.text((x + 5, y + cell_h - 22), label, fill="#dddddd", font=FONT_S)
    return sheet


def main():
    data = json.load(open(os.path.join(REFS, "refs.json"), encoding="utf-8"))
    color = {t: COLORS[i % len(COLORS)] for i, t in enumerate(data["themes"])}
    os.makedirs(OUT, exist_ok=True)

    overview, by_theme = [], {}
    for entry in data["images"]:
        path = os.path.join(REFS, entry["file"])
        if not os.path.exists(path):
            print("FALTA", entry["file"])
            continue
        im = Image.open(path).convert("RGB")
        th = fit(im, THUMB)
        d = ImageDraw.Draw(th)
        for r in entry.get("regions", []):
            x0, y0, x1, y1 = r["box"]
            d.rectangle((x0 * th.width, y0 * th.height, x1 * th.width - 1, y1 * th.height - 1), outline=color[r["theme"]], width=3)
            d.text((x0 * th.width + 4, y0 * th.height + 2), r["theme"], fill=color[r["theme"]], font=FONT_S)
            if entry.get("use", True):
                by_theme.setdefault(r["theme"], []).append((fit(crop(im, r["box"]), CROP), os.path.basename(entry["file"])[:2] + f"  w={entry['weight']}"))
        label = os.path.basename(entry["file"])[:30] + ("" if entry.get("use", True) else "  [NO SE USA]")
        overview.append((th, label))

    grid(overview, 5, THUMB + 10, THUMB + 30, "BrushRefs: regiones por imagen").save(os.path.join(OUT, "overview.png"))
    for theme, tiles in by_theme.items():
        grid(tiles, 4, CROP + 10, CROP + 30, f"{theme}: {data['themes'][theme]}").save(os.path.join(OUT, f"theme_{theme}.png"))
    print("Hojas en", OUT, "| temas:", ", ".join(f"{t}={len(v)}" for t, v in by_theme.items()))


if __name__ == "__main__":
    main()
