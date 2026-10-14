"""Medidas y huecos compartidos por exterior e interior (para que encajen exactamente)."""
X0, X1 = -8.0, 8.0        # cara exterior del muro (huella 16 x 12 m)
Y0, Y1 = -6.0, 6.0
TH = 0.4                  # grosor del muro perimetral
IX0, IX1 = X0 + TH, X1 - TH   # cara interior: +-7.6
IY0, IY1 = Y0 + TH, Y1 - TH   # +-5.6

FL0 = 0.5                 # suelo planta baja
STORY = 3.6               # altura libre de cada planta
SLAB = 0.4                # grosor del forjado
FL1 = FL0 + STORY + SLAB  # suelo planta alta = 4.5
WT = FL1 + STORY          # coronacion del muro = 8.1
BASE_Z = -3.2             # suelo del sotano

# huecos: (centro, ancho, z_inf, z_sup)
def win(c, w, floor, sill=0.9, head=2.5):
    f = FL0 if floor == 0 else FL1
    return (c, w, f + sill, f + head)

FRONT = [  # muro y=-6, corre en X
    (0.0, 2.4, FL0, FL0 + 3.0),                       # puerta principal (con montante)
    win(-5.55, 1.8, 0), win(-2.35, 1.2, 0), win(2.35, 1.2, 0), win(5.55, 1.8, 0),
    win(-5.55, 1.8, 1), win(-2.35, 1.2, 1), win(0.0, 1.6, 1, 0.5, 2.7), win(2.35, 1.2, 1), win(5.55, 1.8, 1),
]
BACK = [   # muro y=+6
    (0.0, 1.4, FL0, FL0 + 2.6),                       # puerta trasera (sala de escaleras -> jardin)
    win(-5.55, 1.8, 0), win(-1.8, 1.4, 0), win(1.8, 1.4, 0), win(5.55, 1.8, 0),      # fachada trasera simetrica
    win(-5.55, 1.8, 1), win(-1.8, 1.4, 1), win(1.8, 1.4, 1), win(5.55, 1.8, 1),
]
WEST = [   # muro x=-8, corre en Y
    win(-3.3, 1.4, 0), win(1.9, 1.4, 0), win(3.8, 1.4, 0),        # PB: sala I, sala III, sala III
    win(-3.3, 1.4, 1), win(0.6, 1.4, 1), win(3.8, 1.4, 1),
]
EAST = [   # muro x=+8
    win(-3.0, 1.4, 0), win(0.8, 0.7, 0, 1.9, 2.7), win(2.95, 0.7, 0, 1.9, 2.7),   # PB: sala II, aseo 2, pasillo
    win(-3.0, 1.4, 1), win(1.2, 1.4, 1), win(3.8, 1.4, 1),
]

# ---- interior (compartido para que ambos modelos cuadren) ----
C0 = FL0 + STORY          # techo planta baja = 4.1
C1 = WT                   # techo planta alta = 8.1
STAIR_HOLE = (-2.9, -0.8, 1.0, 5.5)     # hueco de escalera en el forjado (x0, x1, y0, y1)
HATCH = (5.55, 6.45, 3.95, 4.85)        # escotilla al sotano en el cuarto de mantenimiento
