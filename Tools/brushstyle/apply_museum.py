"""Paso 4: pasa las texturas re-trazadas al museo de Unity, por lotes (Int / Ext).

Uso (desde la raiz del proyecto):
  python Tools/brushstyle/apply_museum.py Int          # o Ext
  python Tools/brushstyle/apply_museum.py Int --dry    # solo muestra que cambiaria

Hace dos cosas:
  1. Copia T_<Nombre>_Albedo.png y T_<Nombre>_Brush.png de ArtSource/BrushStyle/restroke/<Nombre>/ a
     Assets/_TheLivingCanvas/Art/Textures/Painted/Museum/BrushStyle/ (los originales no se tocan).
  2. En Museum_<lote>_Painted.json, cada material cuya textura esta en ArtSource/BrushRefs/families.json pasa a la
     re-trazada: "shader" (painterly o lit, segun families.json), "tex" y "brush". La familia "pared" lleva la
     pincelada suave aprobada en el piloto (brush_strength 0.08, brush_breakup 0.2).
Despues hay que correr en Unity: TheLivingCanvas/Museum/Apply Painted Materials. Para volver atras: git checkout del JSON.
"""
import argparse
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FAMILIES = os.path.join(ROOT, "ArtSource", "BrushRefs", "families.json")
RESTROKE = os.path.join(ROOT, "ArtSource", "BrushStyle", "restroke")
MODELS = os.path.join(ROOT, "Assets", "_TheLivingCanvas", "Art", "Models", "Museum")
DEST = os.path.join(ROOT, "Assets", "_TheLivingCanvas", "Art", "Textures", "Painted", "Museum", "BrushStyle")
SOFT = {"pared": {"brush_strength": 0.08, "brush_breakup": 0.2}}   # aprobado en el piloto (paso 3)


def original_tex(entry):
    """Nombre de la textura original (T_X) aunque la entrada ya apunte a la re-trazada."""
    t = os.path.basename(entry["tex"])
    return t[:-len("_Albedo.png")] if t.endswith("_Albedo.png") else os.path.splitext(t)[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag", choices=["Int", "Ext"])
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    fams = json.load(open(FAMILIES, encoding="utf-8"))["textures"]
    path = os.path.join(MODELS, f"Museum_{args.tag}_Painted.json")
    data = json.load(open(path, encoding="utf-8"))
    used, changed = set(), 0
    for mat, e in data.items():
        tex = original_tex(e)
        cfg = fams.get(tex)
        if cfg is None:
            print(f"  sin familia, se queda igual: {mat} ({tex})")
            continue
        name = tex[2:]
        new = {"shader": cfg["shader"], "tex": f"BrushStyle/T_{name}_Albedo.png"}
        if cfg["shader"] == "painterly":
            new["brush"] = f"BrushStyle/T_{name}_Brush.png"
            new.update(SOFT.get(cfg["family"], {}))
        for k in ("brush", "brush_strength", "brush_breakup"):   # al pasar a lit no quedan restos de painterly
            if k not in new:
                e.pop(k, None)
        if any(e.get(k) != v for k, v in new.items()):
            changed += 1
        e.update(new)
        used.add(name)
        print(f"  {mat:26s} {tex:18s} -> {cfg['shader']}")
    print(f"{changed} materiales cambian en {os.path.basename(path)}; texturas: {sorted(used)}")
    if args.dry:
        return
    os.makedirs(DEST, exist_ok=True)
    for name in sorted(used):
        for kind in ("Albedo", "Brush"):
            src = os.path.join(RESTROKE, name, f"T_{name}_{kind}.png")
            if not os.path.exists(src):
                raise SystemExit(f"Falta {src}: correr antes restroke_all.py")
            shutil.copy2(src, DEST)
    # mismo formato que el exportador de Blender (indent 1), para que el diff muestre solo lo que cambia
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print("Escrito", path)


if __name__ == "__main__":
    main()
