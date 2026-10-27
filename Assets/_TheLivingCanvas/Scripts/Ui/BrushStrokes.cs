using System.Collections.Generic;
using UnityEngine;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// Pinceladas procedurales (blancas, se tiñen con Image.color): trazo, mancha y anillo irregular.
    /// Son el placeholder de las texturas pintadas a mano; el UITheme puede sustituirlas más adelante.
    /// Se generan una vez por (tipo, semilla, tamaño) y se cachean.
    /// </summary>
    public static class BrushStrokes
    {
        static readonly Dictionary<long, Sprite> cache = new Dictionary<long, Sprite>();

        /// <summary>Trazo horizontal con extremos irregulares y cerdas; el final se vuelve seco.</summary>
        public static Sprite Stroke(int seed = 1, int w = 256, int h = 48) => StrokeCore(1, seed, w, h, .45f);

        /// <summary>Pincelada corta y gruesa, de cuerpo casi recto y extremos de cerdas (para marcas pequeñas, ej. la tecla).</summary>
        public static Sprite Dab(int seed = 1, int w = 160, int h = 112) => StrokeCore(4, seed, w, h, .34f);

        /// <summary>Barrido ancho con puntas afiladas (resaltado de pincel): cuerpo curvo, nada de esquinas.</summary>
        public static Sprite Swipe(int seed = 1, int w = 512, int h = 96) => StrokeCore(5, seed, w, h, .8f);

        static Sprite StrokeCore(int kind, int seed, int w, int h, float bodyExponent)
        {
            return Cached(kind, seed, w, h, () =>
            {
                var px = new Color32[w * h];
                float so = seed * 17.3f;
                for (int y = 0; y < h; y++)
                    for (int x = 0; x < w; x++)
                    {
                        float u = (x + .5f) / w, v = (y + .5f) / h * 2f - 1f;
                        float taper = Mathf.Pow(Mathf.Sin(Mathf.PI * Mathf.Clamp01(u * .92f + .04f)), bodyExponent);
                        float th = taper * (.62f + .3f * Mathf.PerlinNoise(u * 4f + so, 1.7f));
                        th += (Mathf.PerlinNoise(u * 26f + so, 9.1f) - .5f) * .16f;
                        float edge = (th - Mathf.Abs(v)) * h * .5f; // píxeles hasta el borde
                        float a = Mathf.Clamp01(edge / 1.6f);
                        float streak = Mathf.PerlinNoise(v * 7f + so, u * 2.5f + 3f);
                        float dry = Mathf.SmoothStep(.55f, 1f, u); // el final se seca: más huecos entre cerdas
                        a *= Mathf.Clamp01(.78f + .35f * streak - dry * (1.1f - streak) * 1.2f);
                        px[y * w + x] = new Color32(255, 255, 255, (byte)(Mathf.Clamp01(a) * 255f));
                    }
                return px;
            });
        }

        /// <summary>Mancha de pintura irregular, casi redonda.</summary>
        public static Sprite Blot(int seed = 1, int size = 64)
        {
            return Cached(2, seed, size, size, () =>
            {
                var px = new Color32[size * size];
                float so = seed * 11.7f;
                for (int y = 0; y < size; y++)
                    for (int x = 0; x < size; x++)
                    {
                        float dx = (x + .5f) / size * 2f - 1f, dy = (y + .5f) / size * 2f - 1f;
                        float d = Mathf.Sqrt(dx * dx + dy * dy);
                        float ang = Mathf.Atan2(dy, dx);
                        float r = .62f * (1f + .22f * (Mathf.PerlinNoise(Mathf.Cos(ang) * 1.4f + 5f + so, Mathf.Sin(ang) * 1.4f + 5f) - .5f) * 2f);
                        float a = Mathf.Clamp01((r - d) * size * .5f / 1.5f);
                        a *= .85f + .15f * Mathf.PerlinNoise(dx * 5f + so, dy * 5f);
                        px[y * size + x] = new Color32(255, 255, 255, (byte)(Mathf.Clamp01(a) * 255f));
                    }
                return px;
            });
        }

        /// <summary>Anillo de tinta casi cerrado, con grosor irregular y un hueco pequeño.</summary>
        public static Sprite Ring(int seed = 1, int size = 128)
        {
            return Cached(3, seed, size, size, () =>
            {
                var px = new Color32[size * size];
                float so = seed * 7.9f;
                float gapAt = (seed * 2.399f) % (Mathf.PI * 2f) - Mathf.PI;
                for (int y = 0; y < size; y++)
                    for (int x = 0; x < size; x++)
                    {
                        float dx = (x + .5f) / size * 2f - 1f, dy = (y + .5f) / size * 2f - 1f;
                        float d = Mathf.Sqrt(dx * dx + dy * dy);
                        float ang = Mathf.Atan2(dy, dx);
                        float n = Mathf.PerlinNoise(Mathf.Cos(ang) * 1.6f + 3f + so, Mathf.Sin(ang) * 1.6f + 3f);
                        float radius = .72f + (n - .5f) * .1f;
                        float thick = .075f + .045f * Mathf.PerlinNoise(ang * 1.2f + 8f + so, 2f);
                        float a = Mathf.Clamp01((thick - Mathf.Abs(d - radius)) * size * .5f / 1.5f);
                        float da = Mathf.Abs(Mathf.DeltaAngle(ang * Mathf.Rad2Deg, gapAt * Mathf.Rad2Deg));
                        a *= Mathf.SmoothStep(0f, 1f, (da - 6f) / 14f); // hueco de ~12°
                        px[y * size + x] = new Color32(255, 255, 255, (byte)(a * 255f));
                    }
                return px;
            });
        }

        static Sprite Cached(int kind, int seed, int w, int h, System.Func<Color32[]> make)
        {
            long key = ((long)kind << 48) ^ ((long)seed << 24) ^ ((long)w << 12) ^ (long)h;
            if (cache.TryGetValue(key, out var s) && s != null) return s;
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear, name = $"Brush{kind}_{seed}" };
            tex.SetPixels32(make());
            tex.Apply(false, false); // legible: el horneado del editor recorta con esta silueta
            s = Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(.5f, .5f), 100f);
            s.name = tex.name;
            cache[key] = s;
            return s;
        }
    }
}
