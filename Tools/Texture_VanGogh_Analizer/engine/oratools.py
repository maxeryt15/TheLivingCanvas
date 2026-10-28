"""Fuentes para las hojas de comparacion y escritura de .ora (OpenRaster: capas que Krita abre tal cual)."""
import io
import zipfile

from PIL import Image, ImageFont

try:
    FONT = ImageFont.truetype("arial.ttf", 26)
    FONT_S = ImageFont.truetype("arial.ttf", 20)
except OSError:
    FONT = FONT_S = ImageFont.load_default()


def new_layer(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def write_ora(path, size, layers):
    """layers: lista (nombre, Image RGBA) de ARRIBA a ABAJO. Un nombre que empieza por "(hidden)" sale oculto."""
    w, h = size
    stack = ['<?xml version="1.0" encoding="UTF-8"?>', f'<image w="{w}" h="{h}"><stack>']
    for i, (name, _) in enumerate(layers):
        vis = "hidden" if name.startswith("(hidden)") else "visible"
        stack.append(f'<layer name="{name}" src="data/layer{i}.png" x="0" y="0" opacity="1.0" visibility="{vis}" composite-op="svg:src-over"/>')
    stack.append("</stack></image>")
    merged = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for _, im in reversed(layers):
        merged = Image.alpha_composite(merged, im)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "image/openraster", compress_type=zipfile.ZIP_STORED)
        z.writestr("stack.xml", "\n".join(stack))
        for i, (_, im) in enumerate(layers):
            b = io.BytesIO(); im.save(b, "PNG"); z.writestr(f"data/layer{i}.png", b.getvalue())
        b = io.BytesIO(); merged.save(b, "PNG"); z.writestr("mergedimage.png", b.getvalue())
        t = merged.copy(); t.thumbnail((256, 256)); b = io.BytesIO(); t.save(b, "PNG"); z.writestr("Thumbnails/thumbnail.png", b.getvalue())
