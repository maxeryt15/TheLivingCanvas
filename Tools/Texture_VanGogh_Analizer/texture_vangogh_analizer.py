"""Texture_VanGogh_Analizer: mide la pincelada de cuadros de referencia y la aplica a texturas.

Uso:
  python texture_vangogh_analizer.py <comando> [opciones del comando]
  python texture_vangogh_analizer.py <comando> -h        # ayuda de cada comando

Comandos (en el orden habitual):
  refs      hojas para comprobar a ojo las regiones de data/refs.json
  analyze   mide un tema en las referencias -> data/profiles/<artista>_<tema>.json
  profile   mezcla perfiles de artistas en un estilo -> data/styles/<tema>.json
  paint     genera una textura tileable desde cero, o re-traza una existente (--base)
  islands   exporta islas UV de un FBX (necesita Blender) para re-trazar atlas sin costuras
  themes    lista los temas (estilos) disponibles

Opciones globales (antes del comando):
  --data DIR    carpeta de datos (refs.json, imagenes, profiles/, styles/); por defecto ./data
  --out DIR     carpeta de salida de paint; por defecto ./out
  --blender EXE ejecutable de Blender para islands (o variable BLENDER)
"""
import argparse
import os
import runpy
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "engine")
MODULES = {"refs": "refs_sheet", "analyze": "analyze", "profile": "profile", "paint": "paint"}


def find_blender(explicit):
    for c in (explicit, os.environ.get("BLENDER"), shutil.which("blender"),
              r"C:\Program Files\Blender Foundation\Blender\blender.exe",
              r"D:\SteamLibrary\steamapps\common\Blender\blender.exe"):
        if c and os.path.isfile(c):
            return c
    sys.exit("No encuentro Blender: pasa --blender <ruta a blender.exe> o define la variable BLENDER")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, add_help=False)
    ap.add_argument("--data", default=os.path.join(HERE, "data"))
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--blender")
    ap.add_argument("-h", "--help", action="store_true")
    ap.add_argument("command", nargs="?")
    args, rest = ap.parse_known_args()
    if args.help and not args.command or not args.command:
        print(__doc__)
        return
    if args.help:
        rest = ["-h"] + rest
    os.environ["TVGA_DATA"] = os.path.abspath(args.data)
    os.environ["TVGA_OUT"] = os.path.abspath(args.out)

    if args.command == "themes":
        styles = os.path.join(args.data, "styles")
        for f in sorted(os.listdir(styles)):
            if f.endswith(".json") and not f.endswith(".overrides.json"):
                print(f[:-5])
        return
    if args.command == "islands":
        if len(rest) != 2 or rest[0] in ("-h", "--help"):
            sys.exit("Uso: islands <modelo.fbx> <salida.json>  (materiales cuyo nombre contiene clothes o hair)")
        r = subprocess.run([find_blender(args.blender), "-b", "--python", os.path.join(ENGINE, "uv_islands.py"), "--",
                            os.path.abspath(rest[0]), os.path.abspath(rest[1])], capture_output=True, text=True)
        lines = [l for l in r.stdout.splitlines() + r.stderr.splitlines() if "UVISLANDS" in l or "Error" in l or "Traceback" in l]
        print("\n".join(lines) or r.stdout[-2000:])
        sys.exit(r.returncode)
    if args.command not in MODULES:
        sys.exit(f"Comando desconocido: {args.command}. Comandos: {', '.join(list(MODULES) + ['islands', 'themes'])}")
    sys.path.insert(0, ENGINE)
    sys.argv = [MODULES[args.command] + ".py"] + rest
    runpy.run_path(os.path.join(ENGINE, MODULES[args.command] + ".py"), run_name="__main__")


if __name__ == "__main__":
    main()
