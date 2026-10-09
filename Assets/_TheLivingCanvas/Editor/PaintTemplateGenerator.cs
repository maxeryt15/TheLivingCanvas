using System.IO;
using UnityEditor;
using UnityEngine;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Genera las máscaras de zonas de las plantillas (PNG, un canal por zona) y los iconos de cosecha.
    /// Girasol: B = centro, R = pétalos, G = tallo y hojas. Tomate: R = tomates, G = tallo y hojas, B = tutor.
    /// Glowbell: R = campanillas, B = esferas luminosas, G = tallo, ramas y hojas.
    /// Mismo aspecto que el lienzo (5:4).
    /// </summary>
    public static class PaintTemplateGenerator
    {
        const int Width = 640;
        const int Height = 512;

        public static Texture2D GenerateSunflowerMask(string assetPath)
        {
            var center = new Vector2(320f, 318f);
            const float centerRadius = 50f;
            const int petalCount = 16;
            const float petalDistance = 92f, petalLength = 44f, petalWidth = 19f;

            var pixels = new Color32[Width * Height];
            for (int y = 0; y < Height; y++)
            {
                for (int x = 0; x < Width; x++)
                {
                    var p = new Vector2(x + 0.5f, y + 0.5f);
                    Color32 c = new(0, 0, 0, 255);

                    if (Vector2.Distance(p, center) <= centerRadius)
                        c.b = 255;
                    else if (InPetals(p, center, petalCount, petalDistance, petalLength, petalWidth))
                        c.r = 255;
                    else if (InStemOrLeaves(p, center))
                        c.g = 255;

                    pixels[y * Width + x] = c;
                }
            }
            return SaveMask(pixels, assetPath);
        }

        /// <summary>
        /// Tomatera atada a un tutor: cuatro tomates (encima de todo), tallo con hojas y el tutor detrás.
        /// </summary>
        public static Texture2D GenerateTomatoMask(string assetPath)
        {
            var pixels = new Color32[Width * Height];
            for (int y = 0; y < Height; y++)
            {
                for (int x = 0; x < Width; x++)
                {
                    var p = new Vector2(x + 0.5f, y + 0.5f);
                    Color32 c = new(0, 0, 0, 255);

                    if (InTomatoes(p))
                        c.r = 255;
                    else if (InTomatoStemOrLeaves(p))
                        c.g = 255;
                    else if (p.x >= 414f && p.x <= 432f && p.y >= 30f && p.y <= 470f)
                        c.b = 255; // tutor

                    pixels[y * Width + x] = c;
                }
            }
            return SaveMask(pixels, assetPath);
        }

        static readonly Vector3[] Tomatoes = // (x, y, radio)
        {
            new(275f, 345f, 44f), new(372f, 278f, 40f), new(248f, 215f, 38f), new(352f, 168f, 36f)
        };

        static bool InTomatoes(Vector2 p)
        {
            foreach (var t in Tomatoes)
                if (Vector2.Distance(p, new Vector2(t.x, t.y)) <= t.z) return true;
            return false;
        }

        static bool InTomatoStemOrLeaves(Vector2 p)
        {
            // Tallo central y cáliz (estrellita) encima de cada tomate.
            if (p.x >= 312f && p.x <= 328f && p.y >= 30f && p.y <= 440f) return true;
            foreach (var t in Tomatoes)
                if (InEllipse(p, new Vector2(t.x, t.y + t.z - 4f), Vector2.right, 20f, 9f)) return true;

            return InLeaf(p, new Vector2(320f, 110f), 200f)
                || InLeaf(p, new Vector2(320f, 150f), -20f)
                || InLeaf(p, new Vector2(320f, 250f), 170f)
                || InLeaf(p, new Vector2(320f, 300f), 15f)
                || InLeaf(p, new Vector2(320f, 400f), 150f)
                || InLeaf(p, new Vector2(320f, 420f), 35f);
        }

        /// <summary>
        /// Glowbell: tallo con cuatro ramas arqueadas; de la punta de cada una cuelga una campanilla
        /// (cuerpo + borde acampanado) con una esfera luminosa debajo.
        /// </summary>
        public static Texture2D GenerateGlowbellMask(string assetPath)
        {
            var pixels = new Color32[Width * Height];
            for (int y = 0; y < Height; y++)
            {
                for (int x = 0; x < Width; x++)
                {
                    var p = new Vector2(x + 0.5f, y + 0.5f);
                    Color32 c = new(0, 0, 0, 255);

                    if (InGlowOrbs(p))
                        c.b = 255;
                    else if (InBells(p))
                        c.r = 255;
                    else if (InGlowbellStem(p))
                        c.g = 255;

                    pixels[y * Width + x] = c;
                }
            }
            return SaveMask(pixels, assetPath);
        }

        // (inicio en el tallo, punta de la rama de la que cuelga la campanilla)
        static readonly (Vector2 start, Vector2 tip)[] GlowbellBranches =
        {
            (new(320f, 250f), new(200f, 330f)), (new(320f, 300f), new(440f, 370f)),
            (new(320f, 180f), new(430f, 250f)), (new(320f, 370f), new(230f, 440f))
        };

        static bool InBells(Vector2 p)
        {
            foreach (var (_, tip) in GlowbellBranches)
                if (InBell(p, tip, 1f)) return true;
            return false;
        }

        /// <summary>Campanilla colgando de <paramref name="top"/>: cuerpo ovalado y borde más ancho abajo.</summary>
        static bool InBell(Vector2 p, Vector2 top, float scale) =>
            InEllipse(p, top - new Vector2(0f, 34f * scale), Vector2.up, 34f * scale, 24f * scale)
            || InEllipse(p, top - new Vector2(0f, 64f * scale), Vector2.right, 34f * scale, 10f * scale);

        static bool InGlowOrbs(Vector2 p)
        {
            foreach (var (_, tip) in GlowbellBranches)
                if (Vector2.Distance(p, tip - new Vector2(0f, 88f)) <= 14f) return true;
            return false;
        }

        static bool InGlowbellStem(Vector2 p)
        {
            if (p.x >= 312f && p.x <= 328f && p.y >= 30f && p.y <= 380f) return true;
            foreach (var (start, tip) in GlowbellBranches)
                if (InSegment(p, start, tip, 6f)) return true;
            return InLeaf(p, new Vector2(320f, 90f), 160f) || InLeaf(p, new Vector2(320f, 120f), 20f);
        }

        static bool InSegment(Vector2 p, Vector2 a, Vector2 b, float halfWidth)
        {
            Vector2 ab = b - a;
            float t = Mathf.Clamp01(Vector2.Dot(p - a, ab) / ab.sqrMagnitude);
            return Vector2.Distance(p, a + ab * t) <= halfWidth;
        }

        /// <summary>Icono placeholder del glowbell: campanilla azul con su esfera blanca debajo.</summary>
        public static Texture2D GenerateGlowbellIcon(string assetPath)
        {
            const int size = 128;
            var top = new Vector2(size * 0.5f, 118f);
            var blue = new Color32(45, 70, 160, 255);
            var white = new Color32(250, 250, 240, 255);
            var pixels = new Color32[size * size];
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    var p = new Vector2(x + 0.5f, y + 0.5f);
                    Color32 c = default; // transparente
                    if (Vector2.Distance(p, top - new Vector2(0f, 98f)) <= 16f) c = white;
                    else if (InBell(p, top, 1.2f)) c = blue;
                    pixels[y * size + x] = c;
                }
            }
            return SaveIcon(pixels, size, assetPath);
        }

        /// <summary>Icono placeholder del tomate: fruto rojo con cáliz verde sobre transparente.</summary>
        public static Texture2D GenerateTomatoIcon(string assetPath)
        {
            const int size = 128;
            var center = new Vector2(size * 0.5f, size * 0.45f);
            var red = new Color32(200, 40, 40, 255);
            var green = new Color32(70, 140, 55, 255);
            var pixels = new Color32[size * size];
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    var p = new Vector2(x + 0.5f, y + 0.5f);
                    Color32 c = default; // transparente
                    if (InEllipse(p, center + new Vector2(0f, 40f), Vector2.right, 26f, 9f)
                        || (Mathf.Abs(p.x - center.x) <= 4f && p.y >= center.y + 40f && p.y <= center.y + 58f))
                        c = green;
                    else if (InEllipse(p, center, Vector2.right, 46f, 40f))
                        c = red;
                    pixels[y * size + x] = c;
                }
            }
            return SaveIcon(pixels, size, assetPath);
        }

        /// <summary>Icono placeholder de la cosecha: centro marrón y anillo de pétalos amarillos sobre transparente.</summary>
        public static Texture2D GenerateSunflowerIcon(string assetPath)
        {
            const int size = 128;
            var center = new Vector2(size * 0.5f, size * 0.5f);
            var yellow = new Color32(250, 200, 40, 255);
            var brown = new Color32(110, 70, 30, 255);
            var pixels = new Color32[size * size];
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    var p = new Vector2(x + 0.5f, y + 0.5f);
                    Color32 c = default; // transparente
                    if (Vector2.Distance(p, center) <= 24f) c = brown;
                    else if (InPetals(p, center, 12, 38f, 22f, 10f)) c = yellow;
                    pixels[y * size + x] = c;
                }
            }
            return SaveIcon(pixels, size, assetPath);
        }

        /// <summary>Máscara legible desde CPU, sin filtrado ni compresión (los canales son datos).</summary>
        static Texture2D SaveMask(Color32[] pixels, string assetPath)
        {
            WritePng(pixels, Width, Height, assetPath);
            var importer = (TextureImporter)AssetImporter.GetAtPath(assetPath);
            importer.isReadable = true;
            importer.sRGBTexture = false;
            importer.mipmapEnabled = false;
            importer.filterMode = FilterMode.Point;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.npotScale = TextureImporterNPOTScale.None;
            importer.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Texture2D>(assetPath);
        }

        static Texture2D SaveIcon(Color32[] pixels, int size, string assetPath)
        {
            WritePng(pixels, size, size, assetPath);
            var importer = (TextureImporter)AssetImporter.GetAtPath(assetPath);
            importer.alphaIsTransparency = true;
            importer.mipmapEnabled = false;
            importer.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Texture2D>(assetPath);
        }

        static void WritePng(Color32[] pixels, int width, int height, string assetPath)
        {
            var texture = new Texture2D(width, height, TextureFormat.RGBA32, false);
            texture.SetPixels32(pixels);
            texture.Apply();
            File.WriteAllBytes(assetPath, texture.EncodeToPNG());
            Object.DestroyImmediate(texture);
            AssetDatabase.ImportAsset(assetPath, ImportAssetOptions.ForceUpdate);
        }

        static bool InPetals(Vector2 p, Vector2 center, int count, float distance, float length, float width)
        {
            for (int i = 0; i < count; i++)
            {
                float angle = i * Mathf.PI * 2f / count;
                var axis = new Vector2(Mathf.Cos(angle), Mathf.Sin(angle));
                if (InEllipse(p, center + axis * distance, axis, length, width)) return true;
            }
            return false;
        }

        static bool InStemOrLeaves(Vector2 p, Vector2 center)
        {
            bool stem = p.x >= 312f && p.x <= 328f && p.y >= 34f && p.y <= center.y;
            return stem
                || InLeaf(p, new Vector2(320f, 118f), 150f)
                || InLeaf(p, new Vector2(320f, 165f), 30f);
        }

        /// <summary>Hoja elíptica que sale del tallo en la dirección indicada (grados).</summary>
        static bool InLeaf(Vector2 p, Vector2 stemPoint, float angleDegrees)
        {
            float a = angleDegrees * Mathf.Deg2Rad;
            var axis = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
            return InEllipse(p, stemPoint + axis * 40f, axis, 52f, 17f);
        }

        /// <param name="axis">Dirección (normalizada) del semieje mayor.</param>
        static bool InEllipse(Vector2 p, Vector2 center, Vector2 axis, float semiMajor, float semiMinor)
        {
            Vector2 d = p - center;
            float along = Vector2.Dot(d, axis) / semiMajor;
            float across = (d.x * -axis.y + d.y * axis.x) / semiMinor;
            return along * along + across * across <= 1f;
        }
    }
}
