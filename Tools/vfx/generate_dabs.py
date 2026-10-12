"""Textura de las partículas de feedback: 4 pinceladitas blancas (2×2 en 256×256) con borde irregular y
vetas de cerdas, para que las partículas se lean como toques de pintura y no como puntos brillantes.
Blanco + alfa: el color lo pone cada partícula. Placeholder hasta pintarlas a mano. Uso:
    python Tools/vfx/generate_dabs.py
Escribe Assets/_TheLivingCanvas/Art/VFX/T_PaintDabs.png.
"""
from pathlib import Path

import numpy as np
from PIL import Image

CELL = 128
OUT = Path(__file__).resolve().parents[2] / "Assets" / "_TheLivingCanvas" / "Art" / "VFX" / "T_PaintDabs.png"
rng = np.random.default_rng(11)  # semilla fija: el archivo no cambia entre ejecuciones


def dab(length, width, bend, angle):
    """Una pincelada: elipse alargada y algo curvada, con borde roto y vetas a lo largo."""
    y, x = np.mgrid[0:CELL, 0:CELL] / (CELL - 1) * 2 - 1  # -1..1
    c, s = np.cos(angle), np.sin(angle)
    u = x * c + y * s          # a lo largo del trazo
    v = -x * s + y * c         # a lo ancho
    v = v - bend * (u ** 2 - 0.3)  # curvatura del trazo
    # Ancho que se estrecha hacia la cola (el pincel se levanta) y borde irregular a lo largo.
    taper = np.clip(1 - np.maximum(u, 0) * 0.55, 0.2, 1)
    edge_noise = 1 + 0.07 * np.sin(u * 9 + rng.uniform(0, 6)) + 0.04 * np.sin(u * 17 + rng.uniform(0, 6))
    d = (u / length) ** 2 + (v / (width * taper * edge_noise)) ** 2
    shape = np.clip((1 - d) * 2.2, 0, 1)
    shape = shape * shape * (3 - 2 * shape)  # borde suave, sin dientes
    # Vetas de cerdas: varias frecuencias al azar a lo ancho (constantes a lo largo), más marcadas hacia la cola.
    across = v / width
    streaks = sum(a * np.sin(across * f + rng.uniform(0, 6)) for f, a in ((7, 0.5), (13, 0.3), (29, 0.2)))
    bristles = 0.8 + 0.2 * streaks * np.clip(u + 0.4, 0, 1.2)
    return np.clip(shape * bristles, 0, 1)


def main():
    cells = [dab(0.85, 0.32, 0.25, 0.3), dab(0.75, 0.40, -0.2, -0.5), dab(0.9, 0.26, 0.4, 1.2), dab(0.6, 0.45, 0.1, 2.4)]
    alpha = np.zeros((CELL * 2, CELL * 2))
    for i, cell in enumerate(cells):
        r, col = divmod(i, 2)
        alpha[r * CELL:(r + 1) * CELL, col * CELL:(col + 1) * CELL] = cell
    rgba = np.zeros((CELL * 2, CELL * 2, 4), dtype=np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = (alpha * 255).astype(np.uint8)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
