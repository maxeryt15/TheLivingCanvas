"""Efectos de sonido placeholder de The Living Canvas, sintetizados con numpy (sin samples ajenos).
Suaves y cortos, para sustituirlos más adelante por sonidos propios. Uso:
    python Tools/sfx/generate_sfx.py
Escribe WAV mono 16 bit 44.1 kHz en Assets/_TheLivingCanvas/Audio/Sfx/.
"""
import wave
from pathlib import Path

import numpy as np

RATE = 44100
OUT = Path(__file__).resolve().parents[2] / "Assets" / "_TheLivingCanvas" / "Audio" / "Sfx"
rng = np.random.default_rng(7)  # semilla fija: los archivos no cambian entre ejecuciones


def t(seconds):
    return np.arange(int(RATE * seconds)) / RATE


def envelope(n, attack, release):
    """Subida y bajada lineales (en segundos) sobre n muestras."""
    env = np.ones(n)
    a, r = int(RATE * attack), int(RATE * release)
    if a: env[:a] = np.linspace(0, 1, a)
    if r: env[-r:] *= np.linspace(1, 0, r)
    return env


def lowpass(x, cutoff):
    """Paso bajo de un polo (suficiente para suavizar ruido)."""
    alpha = 1 - np.exp(-2 * np.pi * cutoff / RATE)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alpha * (v - acc)
        y[i] = acc
    return y


def bell(freq, seconds, decay, partials=((1, 1), (2.76, 0.35), (5.4, 0.12))):
    """Campanita: parciales inarmónicos que se apagan exponencialmente."""
    x = t(seconds)
    s = sum(a * np.sin(2 * np.pi * freq * m * x) * np.exp(-x * decay * m ** 0.5) for m, a in partials)
    return s * envelope(len(x), 0.004, 0.05)


def pluck(freq, seconds, decay):
    """Cuerda pulsada suave (seno con armónicos que caen rápido)."""
    x = t(seconds)
    s = sum(np.sin(2 * np.pi * freq * k * x) * np.exp(-x * decay * k) / k for k in range(1, 5))
    return s * envelope(len(x), 0.003, 0.04)


def mix(*parts):
    n = max(len(p) + int(RATE * start) for p, start in parts)
    out = np.zeros(n)
    for p, start in parts:
        s = int(RATE * start)
        out[s:s + len(p)] += p
    return out


def write(name, x, gain=0.6):
    x = x / max(1e-9, np.max(np.abs(x))) * gain
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((x * 32767).astype("<i2").tobytes())
    print(f"{name}.wav  {len(x) / RATE:.2f}s")


def brush_loop():
    """Roce del pincel sobre tela: ruido filtrado con un vaivén lento. Bucle sin cortes (2 s, fundido cruzado)."""
    seconds, fade = 2.0, 0.25
    n, f = int(RATE * seconds), int(RATE * fade)
    noise = rng.standard_normal(n + f)
    soft = lowpass(noise, 2200) - lowpass(noise, 300)  # banda media: "fffff" de cerdas
    x = np.arange(n + f) / RATE
    soft *= 0.75 + 0.25 * np.sin(2 * np.pi * 1.5 * x)
    loop = soft[:n].copy()
    ramp = np.linspace(0, 1, f)
    loop[:f] = soft[:f] * ramp + soft[n:n + f] * (1 - ramp)  # el final se funde con el principio
    return loop


def paint_finish():
    """Pintura terminada: arpegio ascendente de campanitas (Re mayor)."""
    notes = [587.33, 739.99, 880.0, 1174.66]
    return mix(*[(bell(f, 1.6, 2.2), i * 0.11) for i, f in enumerate(notes)])


def harvest():
    """Cosecha: un 'pop' de cuerda grave + roce de hojas."""
    leaves = lowpass(rng.standard_normal(int(RATE * 0.35)), 3500) * envelope(int(RATE * 0.35), 0.01, 0.3)
    return mix((pluck(220.0, 0.6, 6), 0), (pluck(330.0, 0.5, 7) * 0.6, 0.06), (leaves * 0.5, 0))


def coin():
    """Monedas: dos campanitas agudas y cortas."""
    return mix((bell(1318.5, 0.5, 7), 0), (bell(1760.0, 0.6, 6), 0.07))


def ui_open():
    """Panel que se abre: golpecito de madera, subiendo."""
    return mix((pluck(520.0, 0.18, 25), 0), (pluck(780.0, 0.18, 25) * 0.5, 0.04))


def ui_close():
    """Panel que se cierra: golpecito de madera, bajando."""
    return mix((pluck(780.0, 0.18, 25) * 0.5, 0), (pluck(520.0, 0.18, 25), 0.04))


def place():
    """Pintura colocada en el suelo: golpe sordo y suave."""
    x = t(0.4)
    thump = np.sin(2 * np.pi * (110 - 50 * x) * x) * np.exp(-x * 12)
    dust = lowpass(rng.standard_normal(len(x)), 1200) * np.exp(-x * 18) * 0.3
    return (thump + dust) * envelope(len(x), 0.002, 0.05)


def level_up():
    """Subida de nivel: acorde de campanitas que se abre (Sol mayor)."""
    return mix((bell(392.0, 2.2, 1.4), 0), (bell(493.88, 2.2, 1.4), 0.08), (bell(587.33, 2.2, 1.4), 0.16),
               (bell(783.99, 2.4, 1.2), 0.3))


if __name__ == "__main__":
    write("brush_loop", brush_loop(), gain=0.35)
    write("paint_finish", paint_finish())
    write("harvest", harvest())
    write("coin", coin(), gain=0.45)
    write("ui_open", ui_open(), gain=0.4)
    write("ui_close", ui_close(), gain=0.4)
    write("place", place())
    write("level_up", level_up())
