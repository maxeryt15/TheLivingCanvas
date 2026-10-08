using System.IO;
using UnityEditor;
using UnityEngine;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>
    /// Genera las máscaras de zonas de las plantillas (PNG, un canal por zona).
    /// Girasol: B = centro, R = pétalos, G = tallo y hojas. Mismo aspecto que el lienzo (5:4).
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

            var texture = new Texture2D(Width, Height, TextureFormat.RGBA32, false);
            texture.SetPixels32(pixels);
            texture.Apply();
            File.WriteAllBytes(assetPath, texture.EncodeToPNG());
            Object.DestroyImmediate(texture);

            AssetDatabase.ImportAsset(assetPath, ImportAssetOptions.ForceUpdate);
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
