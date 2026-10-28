using System;
using System.IO;
using TheLivingCanvas.Ui;
using UnityEditor;
using UnityEngine;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Hornea las texturas pintadas del prompt (marca de la tecla y trazo de fondo) con el lenguaje de las texturas
    /// del museo: pinceladas cortas que siguen un remolino, con cresta de luz y sombra (estilo Van Gogh, amarillo y azul).
    /// Son PNG normales en UI/Painted: se pueden sustituir por los pintados a mano sin tocar código.
    /// </summary>
    public static class PaintedUiBake
    {
        const string Dir = "Assets/_TheLivingCanvas/UI/Painted";
        const string ThemePath = "Assets/_TheLivingCanvas/Resources/UITheme.asset";

        static readonly Color32[] Yellows = { C(0xD4A72C), C(0xE9C84A), C(0xF2DD8A), C(0xB98A22), C(0xC9922A) };
        static readonly Color32[] Blues = { C(0x526A83), C(0x3C5A8A), C(0x2C4673), C(0x6F8FBA), C(0x1F2F52) };
        static readonly Color32 Cream = C(0xF0E6C8), Terracotta = C(0xA85F47);

        static Color32 C(int rgb) => new Color32((byte)(rgb >> 16), (byte)(rgb >> 8), (byte)rgb, 255);

        /// <summary>Paleta de una variante del prompt. Los cuerpos son oscuros: el texto blanco con contorno negro se lee encima.</summary>
        class Skin
        {
            public string name;
            public Color32[] strokeBody, strokeAccent, blotCenter, blotRim, blotOuter;
            public Color32 light, spot, shade;
        }

        static Color32[] P(params int[] rgb) { var a = new Color32[rgb.Length]; for (int i = 0; i < rgb.Length; i++) a[i] = C(rgb[i]); return a; }

        static readonly Skin[] Skins =
        {
            // Classic = diseño original (noche estrellada: azul y amarillo); conserva los nombres de archivo de siempre.
            new Skin { name = "", strokeBody = new[] { Blues[2], Blues[4], Blues[1], Blues[2], Blues[4], Blues[0] }, strokeAccent = new[] { Yellows[3], Yellows[4] },
                blotCenter = new[] { Yellows[3], Yellows[4] }, blotRim = Blues, blotOuter = Yellows, light = Cream, spot = Terracotta, shade = Blues[4] },
            // Girasoles: ocres, pardos tostados y verde oliva
            new Skin { name = "Sunflowers", strokeBody = P(0x5A4010, 0x3E2D12, 0x6B4E14, 0x4A3A10, 0x3E2D12, 0x4F4A22),
                strokeAccent = P(0xD4A72C, 0xE9C84A, 0xC9922A), blotCenter = P(0xB98A22, 0xC9922A, 0xA87A1C),
                blotRim = P(0x5A4010, 0x65785A, 0x6B4E14, 0x3E2D12), blotOuter = P(0xD4A72C, 0xE9C84A, 0xC9922A, 0xB98A22),
                light = C(0xF2DD8A), spot = C(0x65785A), shade = C(0x2E2008) },
            // Campo de trigo con cipreses: verdes profundos, oro y cielo azul
            new Skin { name = "Wheatfield", strokeBody = P(0x2F4A33, 0x3C5A3A, 0x24382A, 0x2F4A33, 0x24382A, 0x3A5560),
                strokeAccent = P(0xC9922A, 0xD4A72C, 0x6F8FBA), blotCenter = P(0xB98A22, 0xC9922A),
                blotRim = P(0x2F4A33, 0x3C5A3A, 0x3A5560, 0x24382A), blotOuter = P(0xD4A72C, 0xC9922A, 0xE9C84A),
                light = C(0xE9DDA8), spot = C(0x6F8FBA), shade = C(0x17261C) },
            // Terraza de café de noche: azul noche con naranjas de farol
            new Skin { name = "CafeTerrace", strokeBody = P(0x1F2440, 0x2A2F55, 0x181C36, 0x1F2440, 0x2A2F55, 0x2C3A5A),
                strokeAccent = P(0xE08A2E, 0xD4A72C, 0xF2DD8A), blotCenter = P(0xB8681F, 0xC9782A, 0xA85F2A),
                blotRim = P(0x1F2440, 0x2A2F55, 0x3C5A8A), blotOuter = P(0xE08A2E, 0xD4A72C, 0xC9782A),
                light = C(0xF2DD8A), spot = C(0xA85F47), shade = C(0x0E1020) },
            // Lirios: violetas y azules con verde de tallo y ocre
            new Skin { name = "Irises", strokeBody = P(0x3A2E6B, 0x2C2A5E, 0x4B3A7E, 0x2C2A5E, 0x3A2E6B, 0x34406E),
                strokeAccent = P(0x65785A, 0xC9922A, 0x7E8F5A), blotCenter = P(0x5A4A96, 0x4B3A7E, 0x66559F),
                blotRim = P(0x2C2A5E, 0x3A2E6B, 0x34406E, 0x4B3A7E), blotOuter = P(0x6F8FBA, 0x65785A, 0xC9922A),
                light = C(0xCFC4EA), spot = C(0xD4A72C), shade = C(0x14122E) },
            // Dormitorio en Arlés: verde azulado, terracota y crema de pared
            new Skin { name = "BedroomArles", strokeBody = P(0x2F5560, 0x3C6672, 0x254651, 0x2F5560, 0x254651, 0x4A5F58),
                strokeAccent = P(0xA85F47, 0xC9922A, 0xE0CDB0), blotCenter = P(0xA85F47, 0x96513A, 0xB86C50),
                blotRim = P(0x2F5560, 0x3C6672, 0x254651, 0x4A5F58), blotOuter = P(0xA85F47, 0xC9922A, 0xE0CDB0),
                light = C(0xE0CDB0), spot = C(0xD4A72C), shade = C(0x10282F) },
            // Almendro en flor: azul cielo profundo con blanco rosado y verde
            new Skin { name = "AlmondBlossom", strokeBody = P(0x2E5A7A, 0x3C6E8F, 0x244A66, 0x2E5A7A, 0x244A66, 0x3A6A66),
                strokeAccent = P(0xE8CFC8, 0x65785A, 0xD9B5AE), blotCenter = P(0x3C6E8F, 0x2E5A7A, 0x4A7C9A),
                blotRim = P(0x244A66, 0x2E5A7A, 0x3A6A66), blotOuter = P(0xE8CFC8, 0xD9B5AE, 0x9CC0D4),
                light = C(0xF6E6E0), spot = C(0x65785A), shade = C(0x0F2536) },
        };

        [MenuItem("TheLivingCanvas/UI/6 Bake Painted Prompt Textures")]
        static void Bake()
        {
            Directory.CreateDirectory(Dir);
            var theme = AssetDatabase.LoadAssetAtPath<UITheme>(ThemePath);
            var covers = new Sprite[Skins.Length];
            var skins = new System.Collections.Generic.List<UITheme.PromptSkin>();
            var sheet = new System.Collections.Generic.List<(Color32[] px, int w, int h)>();
            for (int i = 0; i < Skins.Length; i++)
            {
                var k = Skins[i];
                string suffix = k.name.Length > 0 ? "_" + k.name : "";
                var blotPx = Paint(BrushStrokes.Dab(5, 160, 112), 160, 112, true, 11 + i * 7, k);
                var strokePx = Paint(BrushStrokes.Stroke(7, 768, 128), 768, 128, false, 29 + i * 7, k);
                var blot = Save("T_UI_KeyBlot" + suffix, blotPx, 160, 112);
                var stroke = Save("T_UI_PromptStroke" + suffix, strokePx, 768, 128);
                sheet.Add((blotPx, 160, 112)); sheet.Add((strokePx, 768, 128));

                // Cubierta de pantalla completa para las transiciones: el mismo trazo, sobre toda la superficie y sin recorte.
                covers[i] = Save("T_UI_Cover" + suffix, PaintCover(k, Looks[i], 640, 360, 71 + i * 13), 640, 360);                if (i == 0) { if (theme != null) { theme.keyBlot = blot; theme.promptStroke = stroke; } }
                else skins.Add(new UITheme.PromptSkin { name = k.name, blot = blot, stroke = stroke });
            }
            if (theme != null)
            {
                theme.promptSkins = skins.ToArray();
                theme.transitionCovers = covers;
                EditorUtility.SetDirty(theme);
                AssetDatabase.SaveAssets();
            }
            SavePreview(sheet);
            Debug.Log("Texturas del prompt horneadas en " + Dir + " (" + Skins.Length + " variantes)");
        }

        enum Flow { Swirl, Radial, Waves, Horizontal, Vertical, Bands, Diagonal }

        /// <summary>Composición de la cubierta de pantalla de cada cuadro: degradado, foco de luz y dirección de las pinceladas.</summary>
        class Look { public Color32 top, bottom, glow; public Vector2 glowPos; public float glowR, glowS; public Flow flow; }

        static Look L(int top, int bottom, int glow, float gx, float gy, float r, float s, Flow f) =>
            new Look { top = C(top), bottom = C(bottom), glow = C(glow), glowPos = new Vector2(gx, gy), glowR = r, glowS = s, flow = f };

        // Mismo orden que Skins. v crece hacia arriba (fila 0 = abajo): gy alto = zona alta de la pantalla.
        static readonly Look[] Looks =
        {
            L(0x1F2F52, 0x2C4673, 0xD4A72C, .78f, .72f, .26f, .38f, Flow.Swirl),      // noche estrellada: remolino y luna
            L(0x4A3410, 0x6B4E14, 0xE9C84A, .50f, .50f, .42f, .40f, Flow.Radial),     // girasoles: disco de luz y pétalos radiales
            L(0x3A5560, 0x34543A, 0xC9922A, .30f, .22f, .40f, .34f, Flow.Waves),      // trigo: cielo arriba, campo dorado abajo
            L(0x181C36, 0x2A2F55, 0xE08A2E, .50f, .38f, .36f, .50f, Flow.Horizontal), // café: farol cálido en la noche
            L(0x2C2A5E, 0x3A2E6B, 0x65785A, .50f, .05f, .45f, .32f, Flow.Vertical),  // lirios: tallos verticales
            L(0x2F5560, 0x7A4332, 0xE0CDB0, .25f, .72f, .32f, .22f, Flow.Bands),      // dormitorio: pared y suelo planos
            L(0x244A66, 0x2E5A7A, 0xE8CFC8, .20f, .75f, .38f, .36f, Flow.Diagonal),   // almendro: ramas en diagonal
        };

        /// <summary>Cubierta suave: degradado + foco + muchas pinceladas anchas y semitransparentes, de color cercano al fondo, y un desenfoque final.</summary>
        static Color32[] PaintCover(Skin k, Look look, int w, int h, int seed)
        {
            var rng = new System.Random(seed);
            float so = seed * 1.7f;
            var px = new Color[w * h];
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    float u = (x + .5f) / w, v = (y + .5f) / h;
                    Color c = Color.Lerp((Color)look.bottom, (Color)look.top, look.flow == Flow.Bands ? Mathf.SmoothStep(.46f, .54f, v) : v);
                    if (look.flow == Flow.Bands) c = Color.Lerp((Color)look.bottom, (Color)look.top, Mathf.SmoothStep(.44f, .56f, v)); // la línea del suelo
                    float gd = Vector2.Distance(new Vector2(u * w / h, v), new Vector2(look.glowPos.x * w / h, look.glowPos.y)) / look.glowR;
                    float g = Mathf.Clamp01(1f - gd); g = g * g * (3f - 2f * g);
                    px[y * w + x] = Color.Lerp(c, (Color)look.glow, g * look.glowS);
                }
            var baseLayer = (Color[])px.Clone();

            int dabs = w * h / 70;
            for (int d = 0; d < dabs; d++)
            {
                float x = (float)rng.NextDouble() * w, y = (float)rng.NextDouble() * h;
                float u = x / w, v = y / h;
                var local = baseLayer[Mathf.Clamp((int)y, 0, h - 1) * w + Mathf.Clamp((int)x, 0, w - 1)];
                float gd = Vector2.Distance(new Vector2(u * w / h, v), new Vector2(look.glowPos.x * w / h, look.glowPos.y)) / look.glowR;
                float near = Mathf.Clamp01(1f - gd);
                // Cerca del foco salen los acentos claros del cuadro; lejos, los tonos del propio fondo
                bool accent = rng.NextDouble() < (look.flow == Flow.Bands ? .015 + near * .12 : .05 + near * .5);
                Color32 pick = accent ? k.strokeAccent[rng.Next(k.strokeAccent.Length)] : k.strokeBody[rng.Next(k.strokeBody.Length)];
                Color col = Color.Lerp(local, (Color)pick, accent ? .5f : look.flow == Flow.Bands ? .1f : .38f); // bandas: el color del suelo/pared manda
                float j = 1f + ((float)rng.NextDouble() - .5f) * .1f;
                col = new Color(col.r * j, col.g * j, col.b * j, 1f);

                float width = 9f + (float)rng.NextDouble() * 12f;
                int steps = 9 + rng.Next(8);
                for (int s = 0; s < steps; s++)
                {
                    float ang = FlowAngle(look.flow, x / w, y / h, look.glowPos, so);
                    SoftStamp(px, w, h, x, y, width * .5f, col, .33f);
                    x += Mathf.Cos(ang) * width * .3f; y += Mathf.Sin(ang) * width * .3f;
                }
            }

            Blur(px, w, h); Blur(px, w, h);
            if (look.flow == Flow.Horizontal || look.flow == Flow.Bands) Blur(px, w, h); // pinceladas horizontales: más suaves
            var o = new Color32[px.Length];
            for (int i = 0; i < o.Length; i++) { var c = px[i]; o[i] = new Color32((byte)(c.r * 255f), (byte)(c.g * 255f), (byte)(c.b * 255f), 255); }
            return o;
        }

        static float FlowAngle(Flow f, float u, float v, Vector2 glow, float so)
        {
            float n = Mathf.PerlinNoise(u * 3f + so, v * 3f) - .5f;
            switch (f)
            {
                case Flow.Swirl: return Mathf.Atan2(v - .5f, u - .5f) + Mathf.PI * .5f + n * 1.2f + Mathf.Sin(u * 9f + so) * .3f;
                case Flow.Radial: return Mathf.Atan2(v - glow.y, u - glow.x) + Mathf.PI * .38f + n * .6f; // espiral como el disco de semillas
                case Flow.Waves: return Mathf.Sin(u * 11f + v * 4f + so) * .55f + n * .8f;
                case Flow.Horizontal: return n * .7f + Mathf.Sin(u * 5f + so) * .2f;
                case Flow.Vertical: return Mathf.PI * .5f + n * 1.0f + Mathf.Sin(u * 7f + so) * .3f;
                case Flow.Bands: return n * .25f;
                default: return -.6f + n * .9f;
            }
        }

        /// <summary>Estampa redonda suave (caída gaussiana-ish) con opacidad máxima alpha.</summary>
        static void SoftStamp(Color[] px, int w, int h, float cx, float cy, float r, Color col, float alpha)
        {
            int x0 = Mathf.Max(0, Mathf.FloorToInt(cx - r)), x1 = Mathf.Min(w - 1, Mathf.CeilToInt(cx + r));
            int y0 = Mathf.Max(0, Mathf.FloorToInt(cy - r)), y1 = Mathf.Min(h - 1, Mathf.CeilToInt(cy + r));
            for (int y = y0; y <= y1; y++)
                for (int x = x0; x <= x1; x++)
                {
                    float dx = x + .5f - cx, dy = y + .5f - cy;
                    float d = Mathf.Sqrt(dx * dx + dy * dy) / r;
                    if (d >= 1f) continue;
                    float a = alpha * (1f - d * d) * (1f - d * d);
                    px[y * w + x] = Color.Lerp(px[y * w + x], col, a);
                }
        }

        static void Blur(Color[] px, int w, int h)
        {
            var src = (Color[])px.Clone();
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    Color sum = Color.black; int n = 0;
                    for (int dy = -1; dy <= 1; dy++)
                        for (int dx = -1; dx <= 1; dx++)
                        {
                            int xx = x + dx, yy = y + dy;
                            if (xx < 0 || yy < 0 || xx >= w || yy >= h) continue;
                            sum += src[yy * w + xx]; n++;
                        }
                    px[y * w + x] = sum / n;
                }
        }

        /// <summary>Silueta opaca de w×h (para pintar superficies completas con Paint).</summary>
        static Sprite SolidSprite(int w, int h)
        {
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
            var px = new Color32[w * h];
            for (int i = 0; i < px.Length; i++) px[i] = new Color32(255, 255, 255, 255);
            tex.SetPixels32(px); tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(.5f, .5f), 100f);
        }

        static void SetSkin(int i) { PlayerPrefs.SetInt(UITheme.PromptSkinKey, i); PlayerPrefs.Save(); Debug.Log("Prompt skin: " + (i == -2 ? "ciclo automático" : i == -1 ? "Classic" : Skins[i + 1].name) + " (reentra en Play)"); }
        [MenuItem("TheLivingCanvas/UI/Prompt Skin/Cycle all (default)")] static void SkinCycle() => SetSkin(-2);
        [MenuItem("TheLivingCanvas/UI/Prompt Skin/Classic")] static void SkinClassic() => SetSkin(-1);
        [MenuItem("TheLivingCanvas/UI/Prompt Skin/Sunflowers")] static void SkinSunflowers() => SetSkin(0);
        [MenuItem("TheLivingCanvas/UI/Prompt Skin/Wheatfield")] static void SkinWheatfield() => SetSkin(1);
        [MenuItem("TheLivingCanvas/UI/Prompt Skin/Cafe Terrace")] static void SkinCafe() => SetSkin(2);
        [MenuItem("TheLivingCanvas/UI/Prompt Skin/Irises")] static void SkinIrises() => SetSkin(3);
        [MenuItem("TheLivingCanvas/UI/Prompt Skin/Bedroom in Arles")] static void SkinBedroom() => SetSkin(4);
        [MenuItem("TheLivingCanvas/UI/Prompt Skin/Almond Blossom")] static void SkinAlmond() => SetSkin(5);

        /// <summary>Hoja de contacto (una fila por variante: marca + trazo con una E y texto de prueba) para revisar la paleta de un vistazo.</summary>
        static void SavePreview(System.Collections.Generic.List<(Color32[] px, int w, int h)> sprites)
        {
            const int rowH = 140, w = 960;
            int rows = sprites.Count / 2;
            var sheet = new Texture2D(w, rowH * rows, TextureFormat.RGBA32, false);
            var bg = new Color32[w * rowH * rows];
            for (int i = 0; i < bg.Length; i++) bg[i] = new Color32(70, 70, 70, 255);
            sheet.SetPixels32(bg);
            for (int r = 0; r < rows; r++)
            {
                Blit(sheet, sprites[r * 2], 10, (rows - 1 - r) * rowH + 14);
                Blit(sheet, sprites[r * 2 + 1], 180, (rows - 1 - r) * rowH + 6);
            }
            sheet.Apply();
            string path = Path.Combine(Path.GetDirectoryName(Application.dataPath), "ArtSource/UI_PromptSkins_Preview.png");
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            File.WriteAllBytes(path, sheet.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(sheet);
        }

        static void Blit(Texture2D dst, (Color32[] px, int w, int h) s, int ox, int oy)
        {
            for (int y = 0; y < s.h; y++)
                for (int x = 0; x < s.w; x++)
                {
                    var c = s.px[y * s.w + x];
                    if (c.a == 0 || ox + x >= dst.width || oy + y >= dst.height) continue;
                    dst.SetPixel(ox + x, oy + y, c);
                }
        }

        /// <summary>Pinta con pinceladas sobre toda la textura y la recorta con la silueta (alfa) del sprite dado.</summary>
        static Color32[] Paint(Sprite silhouette, int w, int h, bool blot, int seed, Skin k)
        {
            var rng = new System.Random(seed);
            var px = new Color32[w * h];
            var baseColor = blot ? k.blotOuter[0] : k.strokeBody[0];
            for (int i = 0; i < px.Length; i++) px[i] = baseColor;

            float so = seed * 3.7f;
            int dabs = blot ? 170 : (int)(560f * w * h / (768f * 128f)); // cada pincelada ya son ~15 estampas; escala con el área
            float cx = w / 2f, cy = h / 2f;

            for (int d = 0; d < dabs; d++)
            {
                float x = (float)rng.NextDouble() * w, y = (float)rng.NextDouble() * h;
                float width = (blot ? 4.5f : 5.5f) + (float)rng.NextDouble() * (blot ? 4f : 7f);

                // Qué color toca: la marca es amarilla con azul en el borde y remolinos; el trazo, azul con amarillo suelto.
                float zone = Mathf.PerlinNoise(x * .03f + so, y * .03f + so);
                float blue;
                if (blot)
                {
                    float r = EllipseR(x, y, cx, cy, w, h);
                    blue = Mathf.SmoothStep(.5f, .95f, r) * .9f + (zone - .5f) * .5f;
                }
                else blue = .6f + zone * .35f; // trazo azul noche con pinceladas amarillas sueltas
                float pick = (float)rng.NextDouble();
                Color32 col;
                if (blot)
                {
                    float rr = EllipseR(x, y, cx, cy, w, h);
                    // Centro calmado y más oscuro (ocre profundo): la letra blanca se lee; el azul y el remolino quedan en el borde.
                    if (rr < .5f) col = k.blotCenter[rng.Next(k.blotCenter.Length)];
                    else if (pick < .05f) col = k.light;
                    else if (pick < .08f) col = k.spot;
                    else if (pick < blue) col = k.blotRim[rng.Next(k.blotRim.Length)];
                    else col = k.blotOuter[rng.Next(k.blotOuter.Length)];
                }
                else
                {
                    // Trazo del prompt: azul noche calmado para que el texto crema se lea; el amarillo vive en los bordes.
                    float edge = Mathf.Abs(y / h - .5f) * 2f;
                    if (pick < .04f + edge * edge * .1f) col = k.strokeAccent[rng.Next(k.strokeAccent.Length)]; // acentos en los bordes
                    else if (pick < .05f) col = k.spot;
                    else col = k.strokeBody[rng.Next(k.strokeBody.Length)];
                }
                col = Jitter(col, rng);

                // La pincelada sigue un campo de flujo (remolino en la marca, ondas horizontales en el trazo)
                int steps = 14 + rng.Next(8);
                for (int s = 0; s < steps; s++)
                {
                    // Pinceladas casi horizontales con ondulación: la marca de la tecla es ella misma una pincelada
                    float ang = blot
                        ? (Mathf.PerlinNoise(x * .03f + so, y * .05f) - .5f) * 1.3f
                        : (Mathf.PerlinNoise(x * .012f + so, y * .03f) - .5f) * 2.6f + Mathf.Sin(x * .02f + so) * .35f;
                    var dir = new Vector2(Mathf.Cos(ang), Mathf.Sin(ang));
                    var perp = new Vector2(-dir.y, dir.x);
                    Stamp(px, w, h, x, y, width * .5f, col);
                    Stamp(px, w, h, x + perp.x * width * .22f, y + perp.y * width * .22f, width * .17f, Color32.Lerp(col, k.light, blot ? .45f : .22f)); // cresta de luz
                    Stamp(px, w, h, x - perp.x * width * .3f, y - perp.y * width * .3f, width * .14f, Color32.Lerp(col, k.shade, .35f)); // sombra
                    x += dir.x * width * .3f; y += dir.y * width * .3f; // paso corto: pincelada continua, sin cuentas
                }
            }

            // Recorte con la silueta irregular del trazo/mancha
            var sil = silhouette.texture.GetPixels32();
            // Sólido para dar contraste al texto: por columna, todo entre el primer y el último píxel de la silueta
            // es opaco (las cerdas solo quedan en el borde exterior).
            for (int x = 0; x < w; x++)
            {
                int lo = -1, hi = -1;
                for (int y = 0; y < h; y++)
                    if (sil[y * w + x].a > 40) { if (lo < 0) lo = y; hi = y; }
                for (int y = 0; y < h; y++)
                {
                    float a = lo < 0 ? 0f : Mathf.Clamp01(Mathf.Min(y - lo + 1f, hi - y + 1f) / 2f);
                    px[y * w + x].a = (byte)(a * 255f);
                }
            }
            return px;
        }

        /// <summary>Distancia normalizada al centro en una elipse que inscribe la textura (0 centro, 1 borde).</summary>
        static float EllipseR(float x, float y, float cx, float cy, int w, int h)
        {
            float dx = (x - cx) / (w * .5f), dy = (y - cy) / (h * .5f);
            return Mathf.Sqrt(dx * dx + dy * dy);
        }

        static Color32 Jitter(Color32 c, System.Random rng)
        {
            float k = 1f + ((float)rng.NextDouble() - .5f) * .14f;
            return new Color32((byte)Mathf.Clamp(c.r * k, 0, 255), (byte)Mathf.Clamp(c.g * k, 0, 255), (byte)Mathf.Clamp(c.b * k, 0, 255), 255);
        }

        static void Stamp(Color32[] px, int w, int h, float cx, float cy, float r, Color32 col)
        {
            int x0 = Mathf.Max(0, Mathf.FloorToInt(cx - r)), x1 = Mathf.Min(w - 1, Mathf.CeilToInt(cx + r));
            int y0 = Mathf.Max(0, Mathf.FloorToInt(cy - r)), y1 = Mathf.Min(h - 1, Mathf.CeilToInt(cy + r));
            for (int y = y0; y <= y1; y++)
                for (int x = x0; x <= x1; x++)
                {
                    float dx = x + .5f - cx, dy = y + .5f - cy;
                    float d = Mathf.Sqrt(dx * dx + dy * dy);
                    if (d > r) continue;
                    float a = Mathf.Clamp01((r - d) / 0.9f); // borde de 1px antialias
                    var o = px[y * w + x];
                    px[y * w + x] = new Color32(
                        (byte)Mathf.Lerp(o.r, col.r, a), (byte)Mathf.Lerp(o.g, col.g, a), (byte)Mathf.Lerp(o.b, col.b, a), 255);
                }
        }

        static Sprite Save(string name, Color32[] px, int w, int h)
        {
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
            tex.SetPixels32(px);
            tex.Apply();
            string path = $"{Dir}/{name}.png";
            AssetDatabase.DeleteAsset(path); // importación limpia: si cambia el tamaño, el rect del sprite viejo quedaría fuera
            File.WriteAllBytes(path, tex.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(tex);
            AssetDatabase.ImportAsset(path);
            var imp = (TextureImporter)AssetImporter.GetAtPath(path);
            imp.textureType = TextureImporterType.Sprite;
            imp.mipmapEnabled = false;
            imp.alphaIsTransparency = true;
            imp.filterMode = FilterMode.Bilinear;
            imp.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Sprite>(path);
        }
    }
}
