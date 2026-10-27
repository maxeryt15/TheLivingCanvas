using System.IO;
using TheLivingCanvas.Ui;
using UnityEditor;
using UnityEngine;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Hornea la ilustración de la pantalla de carga: "una ventana al jardín del museo" (luz de Monet, pincelada de Van Gogh).
    /// Genera papel, boceto a carbón sobre lienzo imprimado, el paisaje pintado y su versión apagada (Descoloración: menos
    /// saturación y más frío, sin gris uniforme). Es arte provisional pensado para ser sustituido por pintura a mano:
    /// basta con reasignar los sprites en Resources/LoadingScreenSettings.asset.
    /// No reproduce la pintura de la flor amarilla ni el campo gris del Maestro: eso es contenido narrativo que el jugador descubre.
    /// </summary>
    public static class LoadingArtBake
    {
        const string Dir = "Assets/_TheLivingCanvas/UI/Loading";
        const string SettingsPath = "Assets/_TheLivingCanvas/Resources/LoadingScreenSettings.asset";
        const int W = 960, H = 540;

        enum Id : byte { Sky, Hills, Facade, Roof, Cypress, Grass, Path, Bed, Window }

        static Color Hex(int rgb) => new Color(((rgb >> 16) & 255) / 255f, ((rgb >> 8) & 255) / 255f, (rgb & 255) / 255f, 1f);

        /// <summary>Paletas por región: [normal, apagada].</summary>
        static Color[] Palette(Id id, bool faded, bool dusk = false)
        {
            if (dusk)
            {
                // Atardecer: el mismo jardín con luz cálida baja; los verdes se enfrían y el cielo pasa de terracota a cerúleo profundo
                switch (id)
                {
                    case Id.Sky: return faded ? new[] { Hex(0x7A7D8A), Hex(0x9A9496), Hex(0xC9B8A6) } : new[] { Hex(0x3C4E73), Hex(0x526A83), Hex(0xC98A66), Hex(0xE8B07A), Hex(0xF2D3A0) };
                    case Id.Hills: return faded ? new[] { Hex(0x6E7470), Hex(0x777A7E) } : new[] { Hex(0x4A5E55), Hex(0x526A83), Hex(0x65785A), Hex(0x3C4E73) };
                    case Id.Facade: return faded ? new[] { Hex(0xBDB3A6), Hex(0xAAA095) } : new[] { Hex(0xE6C9A0), Hex(0xC49A74), Hex(0xF0D5AE) };
                    case Id.Roof: return faded ? new[] { Hex(0x7F6A60), Hex(0x6E5E56) } : new[] { Hex(0x8F4E3A), Hex(0xA85F47), Hex(0x6E3B2E) };
                    case Id.Cypress: return faded ? new[] { Hex(0x3E4843), Hex(0x4A5550) } : new[] { Hex(0x22362A), Hex(0x2F4A33), Hex(0x2B3F52) };
                    case Id.Grass: return faded ? new[] { Hex(0x6A7064), Hex(0x777B70) } : new[] { Hex(0x52674F), Hex(0x65785A), Hex(0x7E8F5A), Hex(0x3C4E73) };
                    case Id.Path: return faded ? new[] { Hex(0xB8AE9E), Hex(0xC4BAAA) } : new[] { Hex(0xD9B58A), Hex(0xC49A74), Hex(0xE8C9A0) };
                    case Id.Window: return faded ? new[] { Hex(0x6A6F77) } : new[] { Hex(0xE8B07A), Hex(0xF2D3A0), Hex(0xC98A66) }; // ventanas encendidas
                    default: return faded ? new[] { Hex(0x7A6C68), Hex(0x6E7480) } : new[] { Hex(0x8F4E3A), Hex(0x3C4E73), Hex(0xC98A66), Hex(0x52674F) };
                }
            }
            switch (id)
            {
                case Id.Sky: return faded ? new[] { Hex(0x8A9099), Hex(0xA3A8AD), Hex(0xCFC7B4), Hex(0xD9D2C0) } : new[] { Hex(0x6E8DAE), Hex(0x526A83), Hex(0xA9C0D6), Hex(0xEAD9B4), Hex(0xF2E7CC) };
                case Id.Hills: return faded ? new[] { Hex(0x7B8078), Hex(0x808488), Hex(0x6E7470) } : new[] { Hex(0x65785A), Hex(0x747983), Hex(0x7E8F5A), Hex(0x526A83) };
                case Id.Facade: return faded ? new[] { Hex(0xC9C3B5), Hex(0xB8B2A6), Hex(0xD6D0C2) } : new[] { Hex(0xE0CDB0), Hex(0xBFA98A), Hex(0xEEDFC4) };
                case Id.Roof: return faded ? new[] { Hex(0x8E7467), Hex(0x7F6A60) } : new[] { Hex(0xA85F47), Hex(0x8F4E3A), Hex(0xB86C50) };
                case Id.Cypress: return faded ? new[] { Hex(0x4C5750), Hex(0x3F4A45), Hex(0x59645C) } : new[] { Hex(0x2F4A33), Hex(0x3C5A3A), Hex(0x24382A), Hex(0x3A5560) };
                case Id.Grass: return faded ? new[] { Hex(0x7A8070), Hex(0x6E7466), Hex(0x8A8E80) } : new[] { Hex(0x65785A), Hex(0x7E8F5A), Hex(0x9AA66A), Hex(0x526A83) };
                case Id.Path: return faded ? new[] { Hex(0xC8C1B0), Hex(0xB9B2A2), Hex(0xD3CCBC) } : new[] { Hex(0xE0CDB0), Hex(0xD4B98A), Hex(0xEEDFC4) };
                case Id.Window: return faded ? new[] { Hex(0x5A646B), Hex(0x66707A) } : new[] { Hex(0x3A5560), Hex(0x2C4673), Hex(0x526A83) };
                default: return faded ? new[] { Hex(0x8A7A74), Hex(0x6E7480), Hex(0xB9B2A2), Hex(0x7A8070) } : new[] { Hex(0xA85F47), Hex(0x526A83), Hex(0xE0CDB0), Hex(0x65785A) };
            }
        }

        [MenuItem("TheLivingCanvas/UI/7 Bake Loading Screen Art")]
        static void Bake()
        {
            Directory.CreateDirectory(Dir);
            var ids = BuildIdMap(false);
            var paper = Save("T_Loading_Paper", PaintPaper(640, 360, 3), 640, 360, false);
            var sketch = Save("T_Loading_Sketch", PaintSketch(ids), W, H, true);
            var painted = Save("T_Loading_Garden", PaintScene(ids, false, 11, false), W, H, true);
            var faded = Save("T_Loading_Garden_Faded", PaintScene(ids, true, 23, false), W, H, true);

            // Segunda ilustración: el mismo jardín visto al revés (el edificio a la izquierda) y al atardecer
            var idsDusk = BuildIdMap(true);
            var sketchDusk = Save("T_Loading_Sketch_Dusk", PaintSketch(idsDusk), W, H, true);
            var dusk = Save("T_Loading_Dusk", PaintScene(idsDusk, false, 37, true), W, H, true);
            var duskFaded = Save("T_Loading_Dusk_Faded", PaintScene(idsDusk, true, 41, true), W, H, true);
            var paperDusk = Save("T_Loading_Paper_Dusk", PaintPaper(640, 360, 8), 640, 360, false);

            var cfg = AssetDatabase.LoadAssetAtPath<LoadingScreenSettings>(SettingsPath);
            if (cfg == null)
            {
                cfg = ScriptableObject.CreateInstance<LoadingScreenSettings>();
                AssetDatabase.CreateAsset(cfg, SettingsPath);
            }
            cfg.variants = new[]
            {
                new LoadingScreenSettings.Variant { name = "Garden window", paper = paper, sketch = sketch, painted = painted, paintedFaded = faded },
                new LoadingScreenSettings.Variant { name = "Garden at dusk", paper = paperDusk, sketch = sketchDusk, painted = dusk, paintedFaded = duskFaded, paperTint = new Color(.90f, .82f, .70f, 1f) }
            };
            EditorUtility.SetDirty(cfg);
            AssetDatabase.SaveAssets();
            Debug.Log("Arte de carga horneado en " + Dir);
        }

        // ---------- Composición (mapa de regiones) ----------

        static float HillTop(float u) => .56f + .04f * Mathf.Sin(u * 5f + .5f) + .015f * Mathf.Sin(u * 13f);
        static float GroundLine(float u) => .36f + .02f * Mathf.Sin(u * 6f);

        static Id Classify(float u, float v)
        {
            float gl = GroundLine(u);
            // Edificio a la derecha: fachada, frontón y tejado
            if (u > .60f && u < .90f && v > gl - .02f && v < .60f)
            {
                // Puerta central y ventanas altas: la fachada deja de ser un bloque liso
                if (u > .735f && u < .765f && v < .47f) return Id.Window;
                if (v > .47f && v < .56f && (Mathf.Abs(u - .655f) < .011f || Mathf.Abs(u - .705f) < .011f || Mathf.Abs(u - .795f) < .011f || Mathf.Abs(u - .845f) < .011f)) return Id.Window;
                return Id.Facade;
            }
            float apex = .60f + .075f * Mathf.Clamp01(1f - Mathf.Abs(u - .75f) / .11f);
            if (u > .64f && u < .86f && v >= .60f && v < apex) return Id.Roof;
            // Ciprés a la izquierda
            float cy = Mathf.Clamp01((v - .12f) / .78f);
            float half = .055f * Mathf.Pow(Mathf.Sin(Mathf.PI * cy), .7f);
            float cx = .20f + .012f * Mathf.Sin(v * 14f);
            if (v > .12f && v < .90f && Mathf.Abs(u - cx) < half) return Id.Cypress;
            if (v < gl)
            {
                float t = Mathf.Clamp01(v / gl);
                float pc = .45f + .25f * Mathf.Pow(t, 1.2f), ph = .13f * (1f - t) + .012f;
                if (Mathf.Abs(u - pc) < ph) return Id.Path;
                if (Ellipse(u, v, .30f, .15f, .12f, .06f) || Ellipse(u, v, .80f, .12f, .14f, .05f)) return Id.Bed;
                return Id.Grass;
            }
            return v < HillTop(u) ? Id.Hills : Id.Sky;
        }

        static bool Ellipse(float u, float v, float cx, float cy, float rx, float ry)
        {
            float dx = (u - cx) / rx, dy = (v - cy) / ry;
            return dx * dx + dy * dy < 1f;
        }

        /// <summary>Mapa de regiones con los bordes deformados por ruido: nada queda recto ni mecánico.</summary>
        static Id[] BuildIdMap(bool flip)
        {
            var ids = new Id[W * H];
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    float u = (x + .5f) / W, v = (y + .5f) / H;
                    if (flip) u = 1f - u;
                    float wu = u +(Mathf.PerlinNoise(u * 14f, v * 14f) - .5f) * .012f;
                    float wv = v + (Mathf.PerlinNoise(u * 14f + 9f, v * 14f + 4f) - .5f) * .012f;
                    ids[y * W + x] = Classify(wu, wv);
                }
            return ids;
        }

        // ---------- Capas ----------

        /// <summary>Máscara irregular del borde del lienzo: 1 dentro, 0 fuera, con margen pintado a mano.</summary>
        static float EdgeMask(int x, int y)
        {
            float margin = 12f + (Mathf.PerlinNoise(x * .03f, y * .03f) - .5f) * 10f;
            float d = Mathf.Min(Mathf.Min(x, W - 1 - x), Mathf.Min(y, H - 1 - y)) - margin;
            return Mathf.Clamp01(d / 2.5f);
        }

        static Color32[] PaintSketch(Id[] ids)
        {
            var px = new Color32[W * H];
            var charcoal = Hex(0x2B221B);
            var primer = Hex(0xF1E8D2);
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    float a = 0f;
                    var c = primer;
                    float grain = .94f + .06f * Mathf.PerlinNoise(x * .35f, y * .35f);
                    c = new Color(c.r * grain, c.g * grain, c.b * grain);
                    a = .96f;
                    // Contornos: píxeles donde cambia la región (grosor ~2 px) con huecos de lápiz
                    var id = ids[y * W + x];
                    bool edge = false;
                    for (int d = 1; d <= 2 && !edge; d++)
                    {
                        if (x + d < W && ids[y * W + x + d] != id) edge = true;
                        else if (y + d < H && ids[(y + d) * W + x] != id) edge = true;
                    }
                    float line = edge ? Mathf.Clamp01(.35f + Mathf.PerlinNoise(x * .22f, y * .22f) * .8f) : 0f;
                    // Sombreado a rayas diagonales en el ciprés y bajo el tejado
                    if (id == Id.Cypress && ((x + y) % 7 == 0) && Mathf.PerlinNoise(x * .05f, y * .05f) > .42f) line = Mathf.Max(line, .38f);
                    if (id == Id.Facade && (x % 19 == 0) && y < H * .6f) line = Mathf.Max(line, .22f); // columnas
                    if (id == Id.Grass && Mathf.PerlinNoise(x * .9f, y * .12f) > .78f) line = Mathf.Max(line, .22f);
                    var col = Color.Lerp(c, charcoal, line * .85f);
                    float m = EdgeMask(x, y);
                    px[y * W + x] = new Color32((byte)(col.r * 255), (byte)(col.g * 255), (byte)(col.b * 255), (byte)(a * m * 255));
                }
            return px;
        }

        static Color32[] PaintScene(Id[] ids, bool faded, int seed, bool dusk)
        {
            var rng = new System.Random(seed);
            var px = new Color[W * H];

            // Fondo por región con degradados suaves (cielo: cerúleo arriba, crema en el horizonte)
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    float u = (x + .5f) / W, v = (y + .5f) / H;
                    var pal = Palette(ids[y * W + x], faded, dusk);
                    Color c = pal[0];
                    if (ids[y * W + x] == Id.Sky)
                    {
                        float k = Mathf.SmoothStep(.55f, 1f, v);
                        c = Color.Lerp(faded ? pal[2] : pal[3], pal[0], k);
                    }
                    // Luz cálida desde arriba a la derecha (Monet): suave y sin saturar
                    // Día: luz alta a la derecha. Atardecer: sol bajo al otro lado, más cálido y cerca del horizonte
                    var lightPos = dusk ? new Vector2(.15f, .45f) : new Vector2(.82f, .86f);
                    float gd = Vector2.Distance(new Vector2(u * W / H, v), new Vector2(lightPos.x * W / H, lightPos.y)) / (dusk ? .38f : .32f);
                    float g = Mathf.Clamp01(1f - gd); g = g * g * (3f - 2f * g);
                    var lightCol = dusk ? (faded ? Hex(0xDCCFBC) : Hex(0xF2B87A)) : (faded ? Hex(0xE6E0CC) : Hex(0xF2DD8A));
                    c = Color.Lerp(c, lightCol, g * (faded ? .22f : (dusk ? .45f : .35f)));
                    px[y * W + x] = c;
                }
            var baseLayer = (Color[])px.Clone();

            // Pinceladas con dirección propia según región, recortadas a su región (bordes legibles y algo irregulares)
            int dabs = W * H / 75;
            for (int d = 0; d < dabs; d++)
            {
                float x = (float)rng.NextDouble() * W, y = (float)rng.NextDouble() * H;
                var id = ids[Mathf.Clamp((int)y, 0, H - 1) * W + Mathf.Clamp((int)x, 0, W - 1)];
                var pal = Palette(id, faded, dusk);
                var local = baseLayer[Mathf.Clamp((int)y, 0, H - 1) * W + Mathf.Clamp((int)x, 0, W - 1)];
                var pick = pal[rng.Next(pal.Length)];
                float mix = id == Id.Sky ? .5f : .6f;
                var col = Color.Lerp(local, pick, mix);
                float j = 1f + ((float)rng.NextDouble() - .5f) * .12f;
                col = new Color(col.r * j, col.g * j, col.b * j, 1f);

                float width; int steps; float alpha = .42f;
                switch (id)
                {
                    case Id.Sky: width = 14f + (float)rng.NextDouble() * 10f; steps = 10; break;
                    case Id.Hills: width = 10f + (float)rng.NextDouble() * 8f; steps = 9; break;
                    case Id.Cypress: width = 5f + (float)rng.NextDouble() * 5f; steps = 11; alpha = .5f; break;
                    case Id.Grass: width = 4f + (float)rng.NextDouble() * 5f; steps = 7; alpha = .5f; break;
                    case Id.Bed: width = 4f + (float)rng.NextDouble() * 4f; steps = 4; alpha = .6f; break;
                    default: width = 7f + (float)rng.NextDouble() * 6f; steps = 8; break;
                }
                for (int s = 0; s < steps; s++)
                {
                    float u = x / W, v = y / H;
                    float ang = Angle(id, u, v, seed, dusk ? .25f : .75f); // el atardecer está volteado: el frontón queda a la izquierda
                    MaskedStamp(px, ids, x, y, width * .5f, col, alpha, id);
                    x += Mathf.Cos(ang) * width * .32f; y += Mathf.Sin(ang) * width * .32f;
                }
            }

            Blur(px);
            var o = new Color32[px.Length];
            for (int i = 0; i < o.Length; i++)
            {
                int x = i % W, y = i / W;
                var c = px[i];
                o[i] = new Color32((byte)(c.r * 255f), (byte)(c.g * 255f), (byte)(c.b * 255f), (byte)(EdgeMask(x, y) * 255f));
            }
            return o;
        }

        static float Angle(Id id, float u, float v, float seed, float apexU)
        {
            float n = Mathf.PerlinNoise(u * 4f + seed, v * 4f) - .5f;
            switch (id)
            {
                case Id.Sky: return Mathf.Sin(u * 9f + v * 3f + seed) * .45f + n * .8f;       // ondas horizontales, cielo que respira
                case Id.Hills: return Mathf.Sin(u * 7f + seed) * .35f + n * .5f;
                case Id.Facade: return Mathf.PI * .5f + n * .25f;                               // trazos verticales (columnas)
                case Id.Roof: return n * .3f + (u < apexU ? .35f : -.35f);                      // siguen la pendiente
                case Id.Cypress: return Mathf.PI * .5f + Mathf.Sin(v * 14f) * .5f + n * .6f;   // llama ondulante
                case Id.Grass: return Mathf.PI * .5f + n * 1.2f;                                // hierba hacia arriba
                case Id.Path: return .5f + n * .5f;                                             // hacia el edificio
                default: return n * 6f;                                                         // flores: pinceladas sueltas
            }
        }

        static void MaskedStamp(Color[] px, Id[] ids, float cx, float cy, float r, Color col, float alpha, Id only)
        {
            int x0 = Mathf.Max(0, Mathf.FloorToInt(cx - r)), x1 = Mathf.Min(W - 1, Mathf.CeilToInt(cx + r));
            int y0 = Mathf.Max(0, Mathf.FloorToInt(cy - r)), y1 = Mathf.Min(H - 1, Mathf.CeilToInt(cy + r));
            for (int y = y0; y <= y1; y++)
                for (int x = x0; x <= x1; x++)
                {
                    if (ids[y * W + x] != only) continue;
                    float dx = x + .5f - cx, dy = y + .5f - cy;
                    float d = Mathf.Sqrt(dx * dx + dy * dy) / r;
                    if (d >= 1f) continue;
                    float a = alpha * (1f - d * d) * (1f - d * d);
                    px[y * W + x] = Color.Lerp(px[y * W + x], col, a);
                }
        }

        static void Blur(Color[] px)
        {
            var src = (Color[])px.Clone();
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    Color sum = Color.black; int n = 0;
                    for (int dy = -1; dy <= 1; dy++)
                        for (int dx = -1; dx <= 1; dx++)
                        {
                            int xx = x + dx, yy = y + dy;
                            if (xx < 0 || yy < 0 || xx >= W || yy >= H) continue;
                            sum += src[yy * W + xx]; n++;
                        }
                    px[y * W + x] = sum / n;
                }
        }

        /// <summary>Papel de acuarela: casi blanco con manchas suaves y fibras cortas; el tinte final lo pone la variante.</summary>
        static Color32[] PaintPaper(int w, int h, int seed)
        {
            var rng = new System.Random(seed);
            var px = new Color[w * h];
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    float n = Mathf.PerlinNoise(x * .015f + seed, y * .015f) * .5f + Mathf.PerlinNoise(x * .2f, y * .2f) * .12f;
                    float k = .9f + n * .12f;
                    px[y * w + x] = new Color(k, k, k * .985f);
                }
            for (int f = 0; f < w * h / 260; f++)
            {
                float x = (float)rng.NextDouble() * w, y = (float)rng.NextDouble() * h;
                float ang = (float)rng.NextDouble() * Mathf.PI * 2f;
                int len = 4 + rng.Next(10);
                float dark = .93f + (float)rng.NextDouble() * .04f;
                for (int s = 0; s < len; s++)
                {
                    int ix = (int)x, iy = (int)y;
                    if (ix >= 0 && iy >= 0 && ix < w && iy < h) px[iy * w + ix] *= dark;
                    x += Mathf.Cos(ang); y += Mathf.Sin(ang);
                }
            }
            var o = new Color32[px.Length];
            for (int i = 0; i < o.Length; i++) o[i] = new Color32((byte)(Mathf.Clamp01(px[i].r) * 255), (byte)(Mathf.Clamp01(px[i].g) * 255), (byte)(Mathf.Clamp01(px[i].b) * 255), 255);
            return o;
        }

        static Sprite Save(string name, Color32[] px, int w, int h, bool alpha)
        {
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
            tex.SetPixels32(px);
            tex.Apply();
            string path = $"{Dir}/{name}.png";
            AssetDatabase.DeleteAsset(path);
            File.WriteAllBytes(path, tex.EncodeToPNG());
            Object.DestroyImmediate(tex);
            AssetDatabase.ImportAsset(path);
            var imp = (TextureImporter)AssetImporter.GetAtPath(path);
            imp.textureType = TextureImporterType.Sprite;
            imp.mipmapEnabled = false;
            imp.alphaIsTransparency = alpha;
            imp.filterMode = FilterMode.Bilinear;
            imp.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Sprite>(path);
        }
    }
}
