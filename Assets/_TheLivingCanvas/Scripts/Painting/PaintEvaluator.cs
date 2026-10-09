using System.Collections.Generic;
using TheLivingCanvas.Data;
using UnityEngine;

namespace TheLivingCanvas.Painting
{
    public enum PaintingQuality
    {
        Normal,
        Good,
        Excellent,
        Masterpiece
    }

    /// <summary>Cómo quedó una zona de la plantilla.</summary>
    public class ZoneResult
    {
        public ZoneRequirement Requirement;
        /// <summary>Fracción de la zona con pintura (0–1).</summary>
        public float Coverage;
        /// <summary>Parecido medio de la pintura de la zona al color sugerido (0–1).</summary>
        public float ColorFit;
        /// <summary>Color medio pintado en la zona (tiñe el cultivo 3D).</summary>
        public Color DominantColor;
        public bool Passed => Coverage >= Requirement.minCoverage;
    }

    /// <summary>Resultado de evaluar una pintura contra su plantilla.</summary>
    public class PaintingResult
    {
        public readonly List<ZoneResult> Zones = new();
        /// <summary>Fracción del área fuera de las zonas que tiene pintura.</summary>
        public float Spill;
        public float Score;
        public PaintingQuality Quality;
        /// <summary>Modo indulgente: basta con cubrir cada zona; el color no bloquea.</summary>
        public bool CanComeToLife;

        /// <summary>
        /// Copia "desvanecida" (para las semillas): un nivel de calidad menos y los colores de cada zona
        /// <paramref name="fade"/> (0–1) más pálidos, así el cultivo 3D también sale más pálido.
        /// </summary>
        public PaintingResult Faded(float fade)
        {
            var copy = new PaintingResult
            {
                Spill = Spill,
                Score = Score,
                Quality = Quality == PaintingQuality.Normal ? PaintingQuality.Normal : Quality - 1,
                CanComeToLife = CanComeToLife
            };
            foreach (var zone in Zones)
                copy.Zones.Add(new ZoneResult
                {
                    Requirement = zone.Requirement,
                    Coverage = zone.Coverage,
                    ColorFit = zone.ColorFit,
                    DominantColor = Fade(zone.DominantColor, fade)
                });
            return copy;
        }

        /// <summary>Hacia un tono gris claro: menos saturado y más luminoso.</summary>
        public static Color Fade(Color color, float fade)
        {
            float gray = color.grayscale;
            var washed = Color.Lerp(new Color(gray, gray, gray, color.a), Color.white, 0.4f);
            return Color.Lerp(color, washed, fade);
        }
    }

    /// <summary>
    /// Evalúa la pintura de un lienzo zona por zona: cobertura, parecido al color sugerido,
    /// color dominante y pintura derramada fuera. No castiga no saber dibujar: la cobertura pesa más.
    /// </summary>
    public static class PaintEvaluator
    {
        const int CanvasTolerance = 30 * 30;        // distancia RGB² para considerar "tela sin pintar"
        const float ColorFitRange = 220f;            // distancia RGB a la que el parecido llega a 0
        const float FullCoverage = 0.9f;             // a partir de aquí la cobertura cuenta como completa
        const float MaxSpillPenalty = 0.15f;
        const float MasterpieceMinColorFit = 0.6f;   // Masterpiece exige buen color en todas las zonas

        static readonly Dictionary<(PaintTemplate, int, int), int[]> zoneMapCache = new();

        public static PaintingResult Evaluate(PaintSurface surface, PaintTemplate template)
        {
            int w = surface.Width, h = surface.Height;
            var key = (template, w, h);
            if (!zoneMapCache.TryGetValue(key, out int[] zoneMap))
                zoneMapCache[key] = zoneMap = template.BuildZoneMap(w, h);

            var zones = template.Zones;
            int n = zones.Length;
            var zonePixels = new int[n];
            var paintedPixels = new int[n];
            var fitSum = new float[n];
            var colorSum = new Vector3[n];
            int outsidePixels = 0, outsidePainted = 0;

            var pixels = surface.Pixels;
            Color32 canvas = surface.BaseColor;
            var suggested = new Color32[n];
            for (int z = 0; z < n; z++)
                suggested[z] = zones[z].suggestedPigment != null ? zones[z].suggestedPigment.Color : canvas;

            for (int i = 0; i < pixels.Length; i++)
            {
                Color32 c = pixels[i];
                bool painted = DistanceSq(c, canvas) > CanvasTolerance;
                int z = zoneMap[i];
                if (z < 0)
                {
                    outsidePixels++;
                    if (painted) outsidePainted++;
                    continue;
                }

                zonePixels[z]++;
                if (!painted) continue;
                paintedPixels[z]++;
                fitSum[z] += 1f - Mathf.Clamp01(Mathf.Sqrt(DistanceSq(c, suggested[z])) / ColorFitRange);
                colorSum[z] += new Vector3(c.r, c.g, c.b);
            }

            var result = new PaintingResult { CanComeToLife = true };
            float weighted = 0f, totalWeight = 0f;
            for (int z = 0; z < n; z++)
            {
                var zone = new ZoneResult { Requirement = zones[z] };
                if (zonePixels[z] > 0)
                    zone.Coverage = (float)paintedPixels[z] / zonePixels[z];
                if (paintedPixels[z] > 0)
                {
                    zone.ColorFit = fitSum[z] / paintedPixels[z];
                    Vector3 mean = colorSum[z] / paintedPixels[z] / 255f;
                    zone.DominantColor = new Color(mean.x, mean.y, mean.z);
                }
                else
                {
                    zone.DominantColor = suggested[z];
                }

                result.Zones.Add(zone);
                result.CanComeToLife &= zone.Passed;

                // La cobertura pesa el 70 %; el color, el 30 % restante.
                float coverageScore = Mathf.Clamp01(zone.Coverage / FullCoverage);
                weighted += zones[z].weight * coverageScore * (0.7f + 0.3f * zone.ColorFit);
                totalWeight += zones[z].weight;
            }

            result.Spill = outsidePixels > 0 ? (float)outsidePainted / outsidePixels : 0f;
            float spillPenalty = Mathf.Min(result.Spill * 0.5f, MaxSpillPenalty);
            result.Score = Mathf.Clamp01((totalWeight > 0f ? weighted / totalWeight : 0f) - spillPenalty);
            result.Quality = result.Score switch
            {
                < 0.55f => PaintingQuality.Normal,
                < 0.75f => PaintingQuality.Good,
                < 0.9f => PaintingQuality.Excellent,
                _ => PaintingQuality.Masterpiece
            };
            if (result.Quality == PaintingQuality.Masterpiece && !result.Zones.TrueForAll(z => z.ColorFit >= MasterpieceMinColorFit))
                result.Quality = PaintingQuality.Excellent;
            return result;
        }

        static int DistanceSq(Color32 a, Color32 b)
        {
            int dr = a.r - b.r, dg = a.g - b.g, db = a.b - b.b;
            return dr * dr + dg * dg + db * db;
        }
    }
}
