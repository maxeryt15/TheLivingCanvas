"""Construye el pack de plantillas de arte de The Living Canvas.

Uso:  python Tools/template_pack/make_pack.py
Salida: ArtSource/TheLivingCanvas_ArtTemplates.zip  (y la carpeta ArtSource/Pack/ con el contenido)

Pasos: texturas placeholder -> plantillas Krita (.ora) -> .blend (Blender headless) -> FBX -> documentacion -> zip.
"""
import csv
import math
import os
import shutil
import subprocess
import textwrap
import sys
import zipfile

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import spec  # noqa: E402
from make_prototype_textures import FONT, FONT_S, arrow, guide_common, new_layer, write_ora  # noqa: E402

BLENDER = os.environ.get("BLENDER_EXE", r"D:\SteamLibrary\steamapps\common\Blender\blender.exe")
PACK = os.path.join(ROOT, "ArtSource", "Pack", "TheLivingCanvas_ArtTemplates")
ZIP = os.path.join(ROOT, "ArtSource", "TheLivingCanvas_ArtTemplates.zip")
TEX_SRC = os.path.join(ROOT, "Assets", "_TheLivingCanvas", "Art", "Textures")


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def family_members():
    fam = {}
    for mat, (hexc, f) in spec.MATERIALS.items():
        if f:
            fam.setdefault(f, []).append((mat, hexc))
    return fam


def used_by():
    """material -> lista de assets que lo usan."""
    out = {}
    for fname, assets in spec.BLEND_FILES.items():
        for a in assets:
            for p in a[3]:
                out.setdefault(p[2], set()).add(a[0])
    return out


# ---------------------------------------------------------------- texturas y plantillas de material
def make_textures():
    fam = family_members()
    users = used_by()
    os.makedirs(os.path.join(PACK, "blender", "textures"), exist_ok=True)
    os.makedirs(os.path.join(PACK, "krita", "textures"), exist_ok=True)
    for f, (size, tile, direction, desc) in spec.FAMILIES.items():
        members = fam[f]
        base = hex_rgb(members[0][1])
        # PNG que usan los .blend (plano, del color actual de Unity): lo SOBRESCRIBES con tu textura.
        Image.new("RGB", (size, size), base).save(os.path.join(PACK, "blender", "textures", f"T_{f}.png"))

        g = new_layer(size, size)
        mats = ", ".join(m for m, _ in members)
        objs = sorted({a for m, _ in members for a in users.get(m, [])})
        cols = max(20, size // 11)
        lines = [f"{size}x{size}  " + ("REPETIBLE (tecla W = wrap)" if tile else "NO repetible")]
        lines += textwrap.wrap(desc, cols)
        lines += textwrap.wrap("Materiales: " + mats, cols)
        lines += textwrap.wrap("Se ve en: " + (", ".join(objs) if objs else "(solo en escena)"), cols)
        lines = lines[:9]
        d = guide_common(g, size, size, f"T_{f}", lines)
        top = 44 + 24 * len(lines) + 24
        bottom = size - (60 if size >= 512 else 20)
        step = max(40, (bottom - top) // 3)
        for i in range(3):
            y = top + step // 2 + i * step
            if y > bottom:
                break
            if direction == "h":
                arrow(d, int(size * 0.15), y, int(size * 0.55), y, (255, 255, 0, 255))
            elif direction == "v":
                x = int(size * (0.2 + 0.25 * i))
                arrow(d, x, min(bottom, y + step // 2), x, max(top, y - step // 2), (255, 255, 0, 255))
            else:
                x = size * (0.2 + 0.2 * i)
                arrow(d, x, y + step // 4, x + size * 0.25, y - step // 4, (255, 255, 0, 255))
        if size >= 512:
            d.text((14, size - 56), "1 unidad UV = 1 m en bloques: ajusta el Tiling en Unity.", fill=(255, 255, 255, 255), font=FONT_S, stroke_width=2, stroke_fill=(0, 0, 0, 255))
            d.text((14, size - 30), f"Exporta como  blender/textures/T_{f}.png", fill=(255, 255, 255, 255), font=FONT_S, stroke_width=2, stroke_fill=(0, 0, 0, 255))
        base_layer = Image.new("RGBA", (size, size), base + (255,))
        write_ora(os.path.join(PACK, "krita", "textures", f"T_{f}_TEMPLATE.ora"), (size, size),
                  [("GUIDE (ocultar antes de exportar)", g), ("paint_here", new_layer(size, size)), ("base_flat_color (color actual de Unity)", base_layer)])


# ---------------------------------------------------------------- UI, iconos, mascaras de zona
UI_SLOTS = [
    ("Panel_9slice", 256, 256, "Panel de ventanas. Borde de 24 px (9-slice)."),
    ("Panel_Dark", 256, 256, "Variante oscura (paleta de pintura)."),
    ("Button_Normal", 192, 64, ""), ("Button_Hover", 192, 64, ""), ("Button_Pressed", 192, 64, ""), ("Button_Disabled", 192, 64, ""),
    ("Slider_Track", 256, 24, ""), ("Slider_Fill", 256, 24, ""), ("Slider_Handle", 32, 32, ""),
    ("Swatch_Frame", 64, 64, "Marco de cada pigmento."), ("Brush_Cursor", 64, 64, "Cursor del pincel (centro = punto de pintura)."),
    ("Icon_Coin", 64, 64, ""), ("Icon_Level", 64, 64, ""), ("Icon_Season_Spring", 64, 64, ""), ("Icon_Season_Summer", 64, 64, ""),
    ("Icon_Season_Autumn", 64, 64, ""), ("Icon_Season_Winter", 64, 64, ""),
    ("Icon_Brush", 64, 64, ""), ("Icon_Eraser", 64, 64, ""), ("Icon_Eyedropper", 64, 64, ""), ("Icon_Symmetry", 64, 64, ""),
    ("Icon_Undo", 64, 64, ""), ("Icon_Redo", 64, 64, ""), ("Icon_Clear", 64, 64, ""), ("Icon_Guide", 64, 64, ""),
    ("Icon_Hints", 64, 64, ""), ("Icon_Finish", 64, 64, ""), ("Icon_Close", 64, 64, ""), ("Icon_Next", 64, 64, ""),
    ("Icon_Pigment", 64, 64, ""), ("Icon_Lock", 64, 64, ""),
]


def make_ui():
    os.makedirs(os.path.join(PACK, "krita", "ui"), exist_ok=True)
    W, H = 1536, 1024
    g = new_layer(W, H)
    d = guide_common(g, W, H, f"UI_Kit  {W}x{H}  (hoja de elementos de interfaz)", [
        "Hoy toda la UI usa el skin por defecto de Unity (botones con texto). Cada recuadro cian es un elemento con su tamano real.",
        "Pinta dentro de cada recuadro; luego se recorta por rejilla. Fondo transparente."])
    x, y, row_h = 20, 110, 0
    index = []
    for name, w, h, note in UI_SLOTS:
        cell = max(w, 215) + 16
        if x + cell > W - 10:
            x, y, row_h = 20, y + row_h + 62, 0
        d.rectangle([x, y, x + w, y + h], outline=(0, 255, 255, 255), width=2)
        d.text((x, y + h + 2), name, fill=(255, 255, 255, 255), font=FONT_S, stroke_width=2, stroke_fill=(0, 0, 0, 255))
        d.text((x, y + h + 24), f"{w}x{h}", fill=(255, 255, 0, 255), font=FONT_S, stroke_width=2, stroke_fill=(0, 0, 0, 255))
        index.append((name, x, y, w, h))
        x += cell
        row_h = max(row_h, h)
    write_ora(os.path.join(PACK, "krita", "ui", "UI_Kit_TEMPLATE.ora"), (W, H),
              [("GUIDE (ocultar antes de exportar)", g), ("paint_here", new_layer(W, H))])
    with open(os.path.join(PACK, "krita", "ui", "UI_Kit_slots.csv"), "w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["slot", "x", "y", "width", "height"])
        w.writerows(index)


def make_icons_and_masks():
    out_i = os.path.join(PACK, "krita", "icons")
    out_m = os.path.join(PACK, "krita", "gameplay_masks")
    os.makedirs(out_i, exist_ok=True)
    os.makedirs(out_m, exist_ok=True)
    for name in spec.ICONS:
        ref = Image.open(os.path.join(TEX_SRC, name + ".png")).convert("RGBA")
        g = new_layer(128, 128)
        d = guide_common(g, 128, 128, "", [])
        d.ellipse([8, 8, 119, 119], outline=(0, 255, 255, 200), width=1)
        d.text((6, 4), name, fill=(255, 255, 255, 255), font=FONT_S, stroke_width=2, stroke_fill=(0, 0, 0, 255))
        write_ora(os.path.join(out_i, name + "_TEMPLATE.ora"), (128, 128),
                  [("GUIDE (ocultar antes de exportar)", g), ("paint_here", new_layer(128, 128)), ("reference_current_icon", ref)])
    for name, chans in spec.GAMEPLAY_MASKS.items():
        mask = Image.open(os.path.join(TEX_SRC, "PaintTemplates", name + ".png")).convert("RGBA")
        g = new_layer(640, 512)
        d = guide_common(g, 640, 512, f"{name}  640x512  -- MASCARA DE JUEGO (no es arte)", [
            "Rojo puro (255,0,0) = " + chans["R"], "Verde puro (0,255,0) = " + chans["G"], "Azul puro (0,0,255) = " + chans["B"],
            "Negro (0,0,0) = fuera de la planta.",
            "OBLIGATORIO: colores PUROS y SIN antialias (pincel 'pixel' / antialiasing OFF).",
            "Mantén 640x512. Cambia las FORMAS, nunca los canales: el juego puntua por canal."][:7])
        write_ora(os.path.join(out_m, name + "_TEMPLATE.ora"), (640, 512),
                  [("GUIDE (ocultar antes de exportar)", g), ("zone_mask (EDITAR AQUI, colores puros)", mask)])


# ---------------------------------------------------------------- Blender / FBX
def run_blender(args):
    cmd = [BLENDER, "-b", "--python"] + args
    print(">", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = r.stdout + r.stderr
    if r.returncode != 0 or "Traceback" in out:
        print(out[-3000:])
        raise SystemExit("Blender fallo")
    return out


def make_blend_and_fbx():
    out_blend = os.path.join(PACK, "blender")
    prev = os.path.join(PACK, "reference", "previews")
    run_blender([os.path.join(HERE, "build_blend.py"), "--", out_blend, "--preview", prev])
    scripts = os.path.join(out_blend, "scripts")
    os.makedirs(scripts, exist_ok=True)
    for f in ("export_fbx.py", "spec.py", "build_blend.py"):
        shutil.copy(os.path.join(HERE, f), scripts)
    fbx = os.path.join(PACK, "fbx")
    os.makedirs(fbx, exist_ok=True)
    for blend in sorted(spec.BLEND_FILES):
        run_blender([os.path.join(HERE, "export_fbx.py"), "--", os.path.join(out_blend, blend + ".blend"), fbx])


# ---------------------------------------------------------------- documentacion
def dims(parts):
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for p in parts:
        s, pos = p[3], p[4]
        ext = (s[0], s[1], s[2]) if p[1] not in ("quad", "quadh") else ((s[0], s[1], 0.0) if p[1] == "quad" else (s[0], 0.0, s[1]))
        if p[5] != (0, 0, 0):
            m = max(ext)
            ext = (m, m, m)
        for i in range(3):
            lo[i] = min(lo[i], pos[i] - ext[i] / 2)
            hi[i] = max(hi[i], pos[i] + ext[i] / 2)
    return tuple(round(hi[i] - lo[i], 2) for i in range(3))


def write_docs():
    fam = family_members()
    users = used_by()
    rows = []
    md = ["# Inventario de placeholders — The Living Canvas", "",
          "Generado el 2026-10-12 a partir de `Studio.unity` y los prefabs. Medidas en metros (Unity: X ancho, Y alto, Z fondo).", ""]
    md += ["## 3D (Blender)", ""]
    for fname, assets in spec.BLEND_FILES.items():
        md += [f"### `blender/{fname}.blend`", "", "| Asset | Tamaño aprox. (X·Y·Z) | Dónde está en Unity | Materiales | Notas |", "|---|---|---|---|---|"]
        for a in assets:
            aname, cat, where, parts, notes = a
            mats = ", ".join(sorted({p[2] for p in parts}))
            d = dims(parts)
            md.append(f"| **{aname}** | {d[0]} · {d[1]} · {d[2]} | {where} | {mats} | {notes} |")
            rows.append([fname + ".blend", aname, cat, f"{d[0]}x{d[1]}x{d[2]}", where, mats, notes])
        md.append("")
    md += ["## 2D — texturas de material (Krita)", "",
           "Hoy **todos los materiales de Unity son colores planos**. Cada familia de textura sustituirá a uno o varios materiales.", "",
           "| Plantilla (`krita/textures/`) | Tamaño | ¿Repetible? | Materiales que cubre | Se ve en |", "|---|---|---|---|---|"]
    for f, (size, tile, direction, desc) in spec.FAMILIES.items():
        mats = ", ".join(m for m, _ in fam[f])
        objs = ", ".join(sorted({a for m, _ in fam[f] for a in users.get(m, [])}))
        md.append(f"| `T_{f}_TEMPLATE.ora` | {size}×{size} | {'sí' if tile else 'no'} | {mats} | {objs} — {desc} |")
        rows.append(["krita/textures", f"T_{f}", "Textura", f"{size}x{size}", "materiales", mats, desc])
    md += ["", "**No tienen plantilla (se generan en el juego):** `M_PaintingPlot`, el lienzo del caballete y las pinturas de los marcos "
           "de la galería usan la pintura del jugador (textura creada en runtime).", "",
           "## 2D — interfaz, iconos y máscaras", "",
           "| Plantilla | Tamaño | Qué es |", "|---|---|---|",
           "| `krita/ui/UI_Kit_TEMPLATE.ora` | 1536×1024 | Hoja con todos los elementos de UI (paneles, botones, slider, iconos de herramientas). Hoy usa el skin por defecto de Unity. `UI_Kit_slots.csv` da las coordenadas de cada recuadro. |"]
    for n in spec.ICONS:
        md.append(f"| `krita/icons/{n}_TEMPLATE.ora` | 128×128 | Icono del cultivo en inventario/tienda (trae el icono actual como referencia). |")
    for n, c in spec.GAMEPLAY_MASKS.items():
        md.append(f"| `krita/gameplay_masks/{n}_TEMPLATE.ora` | 640×512 | **Máscara de juego** (R={c['R']}, G={c['G']}, B={c['B']}). Define por zonas qué se evalúa al pintar y qué color toma cada parte de la planta. Colores puros y sin antialias. |")
    md += ["", "## Audio / VFX", "", "El proyecto aún no tiene audio ni efectos (`Art/VFX` y `Audio` están vacíos).", ""]
    with open(os.path.join(PACK, "INVENTORY.md"), "w", encoding="utf8", newline="\n") as fh:
        fh.write("\n".join(md))
    with open(os.path.join(PACK, "inventory.csv"), "w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "asset", "category", "size_m", "unity_location", "materials", "notes"])
        w.writerows(rows)
    shutil.copy(os.path.join(ROOT, "ART_DIRECTION.md"), os.path.join(PACK, "ART_DIRECTION.md"))

    readme = f"""# The Living Canvas — pack de plantillas de arte

Contiene **todos los placeholders del juego** como plantillas para que los rehagas con tu estética.
Lista completa con medidas: `INVENTORY.md` (y `inventory.csv`). Dirección artística: `ART_DIRECTION.md`.

## Contenido
```
blender/     4 archivos .blend (3D) + textures/ (las PNG que leen los .blend) + scripts/
fbx/         un .fbx por asset (para arrastrar a Unity)
krita/       plantillas .ora: textures/ ({len(spec.FAMILIES)} familias de material), ui/, icons/, gameplay_masks/
reference/   previews/ (render de cada .blend)
```

## 3D en Blender (Blender 4.2+; probado en 5.2)
- Hay **{sum(len(v) for v in spec.BLEND_FILES.values())} assets** en 4 archivos: `TLC_Characters`, `TLC_Props`, `TLC_Crops`, `TLC_Architecture`.
  Cada asset es una colección `SM_<Nombre>` con un Empty del mismo nombre (= **pivote/origen**, en el centro de la base) y sus partes como objetos separados.
- Son **bloqueos a escala real** (1 unidad = 1 m) con las medidas exactas que tiene hoy el juego. Reemplázalos con tus modelos manteniendo: tamaño aproximado, pivote y nombres de las colecciones/partes.
- Los materiales se llaman igual que en Unity (`M_Floor_Wood`…), muestran el color actual y leen `//textures/T_<Familia>.png`.
  Pinta en Krita, exporta a `blender/textures/` y en Blender: *Image → Reload*.
- Las colecciones `_REFERENCE` (persona de 1,8 m y cubo de 1 m) y `_LABELS` no se exportan.
- **UVs**: los bloques usan 1 unidad UV = 1 metro (para texturas repetibles). Para tus modelos finales desenvuelve a tu gusto;
  la textura pintada sigue al UV (ver `Docs/Guia_Texturas_Painterly.md` del proyecto).
- **Ejes**: estándar Blender → Unity: el **frente** del objeto mira a **−Y** en Blender (vista *Front*, numpad 1) y arriba es +Z. Así llega a Unity con el frente en +Z y sin giros.
- **Partes que el código anima** (no las fusiones): cultivos (`Stem`, `Leaf_*`, `Petal_*`/`Fruit_*`/`Bell_*`…), `GardenGate` (el pivote de la hoja es `Post_L`)
  y `Easel`/`PaintingPlot`/`Gallery_Frame` (el quad `Canvas`/`Painting`/`Picture` recibe la pintura del jugador: UV 0–1 completos).

### Exportar a Unity
Dos opciones:
1. Usar los `.fbx` ya generados en `fbx/` (uno por asset, origen en 0).
2. Regenerarlos tras editar: `blender -b TLC_Props.blend --python scripts/export_fbx.py -- TLC_Props.blend ../fbx`
   (ejes `-Z` adelante / `Y` arriba, transformaciones aplicadas, escala 1; es lo estándar y llega a Unity sin rotación).

## 2D en Krita (Krita 5.x)
Cada `.ora` se abre directamente en Krita y trae capas: `GUIDE` (tamaño, dirección de pincelada, para qué sirve; **ocúltala antes de exportar**),
`paint_here` y `base_flat_color` (el color actual de Unity).
1. Pinta siguiendo las flechas (la dirección del trazo acompaña la forma: vetas, curvatura…). En las repetibles activa *Wrap Around Mode* (tecla `W`).
2. Oculta `GUIDE`, exporta como PNG **con el mismo nombre y tamaño** que indica la guía.
3. **Máscaras de juego** (`gameplay_masks/`): no son arte; los canales R/G/B puros definen las zonas que puntúa el juego. Edita las formas con pincel sin antialias y no cambies los colores.
4. **Pinturas del jugador** (lienzo, parcela, marcos de galería): se generan en el juego, no tienen plantilla.

## Pasar tus assets a Unity
- Modelos: `.fbx` a `Assets/_TheLivingCanvas/Art/Models/`; texturas PNG a `Assets/_TheLivingCanvas/Art/Textures/Painted/`.
- Hoy los materiales de Unity son colores planos; cuando tengas listas las texturas, el siguiente paso es asignarlas con el shader `TLC/Painterly`
  (ya existe, ver `ART_DIRECTION.md`). Avísame y lo hago por familia, empezando por el rincón del prototipo.
- Si cambias el tamaño de algo (casas, puertas, altura del jugador…) avisa: el código de colisiones, cámara y el builder de la escena usan estas medidas.
"""
    with open(os.path.join(PACK, "README.md"), "w", encoding="utf8", newline="\n") as fh:
        fh.write(readme)


def make_zip():
    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for folder, _, files in os.walk(PACK):
            for f in files:
                full = os.path.join(folder, f)
                z.write(full, os.path.relpath(full, os.path.dirname(PACK)))
    print("ZIP:", ZIP, round(os.path.getsize(ZIP) / 1e6, 2), "MB")


def main():
    if os.path.exists(PACK):
        shutil.rmtree(PACK)
    os.makedirs(PACK)
    make_textures()
    make_ui()
    make_icons_and_masks()
    make_blend_and_fbx()
    write_docs()
    make_zip()


if __name__ == "__main__":
    main()
