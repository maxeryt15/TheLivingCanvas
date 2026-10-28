"""Paso 3: mezcla los perfiles medidos de un tema (90 % Van Gogh / 10 % otros) y los traduce a parametros del generador.

Uso (desde la raiz del proyecto):  python profile.py sky_swirl [--mix vangogh=0.9,monet=0.1]

Lee   <datos>/profiles/<artista>_<tema>.json   (salida de analyze.py)
Escribe <datos>/styles/<tema>.json             (se REESCRIBE: no editar a mano)
Retoques a mano: <datos>/styles/<tema>.overrides.json (mismas claves de "generator"; paint.py lo aplica encima).
Si falta el perfil de un artista de la mezcla, se reparte su peso entre los demas y se avisa.
Significado de cada parametro: <datos>/styles/PARAMETROS.md
"""
import argparse
import json
import os
import sys

DATA = os.environ.get("TVGA_DATA") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
REFS = DATA
PROFILES = os.path.join(REFS, "profiles")
STYLES = os.path.join(REFS, "styles")

DEFAULT_MIX = "vangogh=0.9,monet=0.1"

# Paletas del proyecto por tema (ART_DIRECTION.md sec. 6 + variantes). El generador NO usa la paleta del cuadro:
# se mide solo como referencia. Orden: de mas presente a menos.
THEME_PALETTES = {
    "sky_swirl": ["#526A83", "#7A93AE", "#A9BCCB", "#747983", "#E0CDB0", "#C9D3CF"],
    "field": ["#D4A72C", "#C8902E", "#E3C873", "#B0782A", "#E0CDB0", "#65785A"],
    "cypress": ["#2F4A2E", "#1E2A22", "#3E5A34", "#3D5C58", "#65785A", "#9AA24A"],   # masa oscura, acentos claros raros
}
FALLBACK_PALETTE = ["#526A83", "#D4A72C", "#65785A", "#A85F47", "#747983", "#E0CDB0"]


def parse_mix(text):
    out = {}
    for part in text.split(","):
        k, v = part.split("=")
        out[k.strip()] = float(v)
    return out


def mix_profiles(theme, mix):
    have = {}
    for artist, w in mix.items():
        path = os.path.join(PROFILES, f"{artist}_{theme}.json")
        if os.path.exists(path):
            have[artist] = (w, json.load(open(path, encoding="utf-8"))["aggregate"])
        else:
            print(f"AVISO: no hay perfil {artist}_{theme}; su peso ({w}) se reparte entre los demas")
    if not have:
        sys.exit(f"Sin perfiles para {theme}: correr antes analyze.py {theme}")
    tot = sum(w for w, _ in have.values())
    keys = set.intersection(*(set(a) for _, a in have.values()))
    mixed = {}
    for k in sorted(keys):
        vals = [(w / tot, a[k]) for w, a in have.values() if a[k] is not None]
        if vals:
            s = sum(w for w, _ in vals)
            mixed[k] = round(sum(w * v for w, v in vals) / s, 4)
    return mixed, {a: round(w / tot, 3) for a, (w, _) in have.items()}


def to_generator(m, theme):
    """Medidas -> parametros del generador. Todas las longitudes van relativas al ANCHO del trazo o al lado de la textura."""
    # Direccion de fondo: solo si los recortes coinciden (trigal vertical); si no (cielos), al azar en cada textura.
    agree = m.get("direction_agreement", 0) or 0
    direction = m.get("direction_deg") if agree > 0.3 else None
    return {
        "direction_deg": direction,                           # 0 horizontal, 90 vertical; null = al azar
        # cuanto ondula el flujo de fondo (radianes). x0.8 calibrado a ojo: con mas, el trigal se abre en abanicos
        "drift_amount": 0.9 if direction is None else round(min(0.9, max(0.25, 0.8 * (1 - (m.get("direction_order") or 0)))), 2),
        "palette_weighted": True,                             # los colores de acento salen menos en trazos sueltos
        # Tamano: ancho del trazo como fraccion del lado de la textura. El recorte de referencia equivale a ~1 textura.
        "stroke_width_rel": round(m["width_rel"] * 0.9, 4),
        "width_jitter": 0.30,                                 # variacion del ancho entre trazos (fraccion)
        # largo / ancho. x0.8: el analizador une trazos vecinos de color parecido y mide la textura ~25 % mas larga
        "aspect": round(m["aspect"] * 0.8, 2),
        "length_jitter": 0.35,                                # sigma log-normal del largo
        "bend_radius_rel_width": m["curve_radius_rel_width"],  # curva propia del trazo, ademas de seguir el flujo
        "bend_same_side": m["turn_consistency"],              # 0 = curvas a ambos lados, 1 = todas igual
        "jitter_deg": m["jitter_deg"],                        # desvio de cada trazo respecto al flujo
        # Flujo: remolinos por textura (el recorte medio mide ~1.3 texturas de area) y su radio de influencia
        "swirls": round((m.get("swirls_per_region") or 0) / 1.3),
        "swirl_radius_rel": round((m.get("swirl_radius_rel") or 0.12) * 1.6, 3),
        "swirl_same_spin": 0.5,                               # 0.5 = mitad horario / mitad antihorario
        "drift_scale": 2,                                     # ondas del flujo de fondo por textura (entero: tileable)
        # Cobertura y color
        "coverage": round(min(1.6, 0.6 + m["coherent_area"]), 2),  # capas de trazos (>1 = se pisan)
        "neighbour_dE": m["neighbour_dE"],                    # contraste de color entre trazos vecinos (color roto)
        "palette": THEME_PALETTES.get(theme, FALLBACK_PALETTE),
        "palette_scale": 2,                                   # manchas grandes de color de fondo por textura (entero)
        # Relieve (no se mide en fotos: a ojo)
        "impasto": 0.6,                                       # 0 = plano, 1 = pasta muy gruesa
        "bristles": 0.5,                                      # marca de cerdas dentro del trazo
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("theme")
    ap.add_argument("--mix", default=DEFAULT_MIX)
    args = ap.parse_args()
    measured, used = mix_profiles(args.theme, parse_mix(args.mix))
    style = dict(theme=args.theme, mix_requested=parse_mix(args.mix), mix_used=used,
                 measured=measured, generator=to_generator(measured, args.theme))
    os.makedirs(STYLES, exist_ok=True)
    out = os.path.join(STYLES, f"{args.theme}.json")
    json.dump(style, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("Estilo:", out)
    print(json.dumps(style["generator"], ensure_ascii=False))


if __name__ == "__main__":
    main()
