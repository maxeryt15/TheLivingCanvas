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
        /// <summary>Fracción de la pintura de las zonas hecha con el pincel Fill (0–1).</summary>
        public float FillShare;
        /// <summary>Habría sido Masterpiece, pero se hizo sobre todo con Fill.</summary>
        public bool CappedByFill;
        /// <summary>Estilo con que se pintó (null = Classic); las semillas lo heredan.</summary>
        public StyleDefinition Style;

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
                CanComeToLife = CanComeToLife,
                Style = Style
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
    /// Evalúa la pintura de un lienzo zona por zona: cobertura, parecido al color, color dominante y pintura
    /// derramada fuera. No castiga no saber dibujar: la cobertura pesa más. El parecido se mide contra el color
    /// aceptado (el sugerido o el de una variante de esa zona) más cercano al color medio pintado, así una
    /// variante bien pintada también puede ser Masterpiece.
    /// </summary>
    public static class PaintEvaluator
    {
        const int CanvasTolerance = 30 * 30;        // distancia RGB² para considerar "tela sin pintar"
        const float ColorFitRange = 220f;            // distancia RGB a la que el parecido llega a 0
        const float FullCoverage = 0.9f;             // a partir de aquí la cobertura cuenta como completa
        const float MaxSpillPenalty = 0.15f;
        const float SwirlLongStrokeBonus = 0.1f;
        const float MasterpieceMinColorFit = 0.6f;   // Masterpiece exige buen color en todas las zonas
        const float MaxFillShareForMasterpiece = 0.5f; // una pintura hecha sobre todo con Fill llega como mucho a Excellent

        static readonly Dictionary<(PaintTemplate, int, int), int[]> zoneMapCache = new();

        /// <param name="variants">Variantes del cultivo: sus pigmentos cuentan como color correcto en su zona.</param>
        /// <param name="style">Estilo de la pintura (null = Classic): el de acuarela perdona parte del derrame.</param>
        public static PaintingResult Evaluate(PaintSurface surface, PaintTemplate template, IReadOnlyList<CropVariant> variants = null,
            StyleDefinition style = null)
        {
            int w = surface.Width, h = surface.Height;
            int[] zoneMap = ZoneMap(template, w, h);

            var zones = template.Zones;
            int n = zones.Length;
            var zonePixels = new int[n];
            var paintedPixels = new int[n];
            var colorSum = new Vector3[n];
            int outsidePixels = 0, outsidePainted = 0, filledPixels = 0;

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
                if (c.a == PaintSurface.FillAlpha) filledPixels++;
                colorSum[z] += new Vector3(c.r, c.g, c.b);
            }

            // Color objetivo de cada zona: el aceptado más cercano al color medio pintado.
            var target = new Color32[n];
            for (int z = 0; z < n; z++)
            {
                target[z] = suggested[z];
                if (paintedPixels[z] == 0 || variants == null) continue;
                Vector3 mean = colorSum[z] / paintedPixels[z];
                var meanColor = new Color32((byte)mean.x, (byte)mean.y, (byte)mean.z, 255);
                foreach (var variant in variants)
                {
                    if (variant.zoneName != zones[z].zoneName || variant.pigment == null) continue;
                    Color32 candidate = variant.pigment.Color;
                    if (DistanceSq(meanColor, candidate) < DistanceSq(meanColor, target[z]))
                        target[z] = candidate;
                }
            }

            var fitSum = new float[n];
            for (int i = 0; i < pixels.Length; i++)
            {
                int z = zoneMap[i];
                if (z < 0 || DistanceSq(pixels[i], canvas) <= CanvasTolerance) continue;
                fitSum[z] += 1f - Mathf.Clamp01(Mathf.Sqrt(DistanceSq(pixels[i], target[z])) / ColorFitRange);
            }

            var result = new PaintingResult { CanComeToLife = true, Style = style };
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
            float spillPenalty = Mathf.Min(result.Spill * 0.5f, MaxSpillPenalty) * (style != null ? style.SpillMultiplier : 1f);
            // Remolino premia los trazos largos y continuos (hasta +0.1).
            float swirlBonus = style != null && style.Kind == StyleKind.Swirl ? SwirlLongStrokeBonus * surface.LongStrokeShare : 0f;
            result.Score = Mathf.Clamp01((totalWeight > 0f ? weighted / totalWeight : 0f) - spillPenalty + swirlBonus);
            result.Quality = result.Score switch
            {
                < 0.55f => PaintingQuality.Normal,
                < 0.75f => PaintingQuality.Good,
                < 0.9f => PaintingQuality.Excellent,
                _ => PaintingQuality.Masterpiece
            };
            int totalPainted = 0;
            foreach (int count in paintedPixels) totalPainted += count;
            result.FillShare = totalPainted > 0 ? (float)filledPixels / totalPainted : 0f;
            if (result.Quality == PaintingQuality.Masterpiece)
            {
                bool colorOk = result.Zones.TrueForAll(z => z.ColorFit >= MasterpieceMinColorFit);
                result.CappedByFill = colorOk && result.FillShare > MaxFillShareForMasterpiece;
                if (!colorOk || result.CappedByFill)
                    result.Quality = PaintingQuality.Excellent;
            }
            return result;
        }

        /// <summary>Mapa de zonas de la plantilla a esa resolución (calculado una vez y reutilizado).</summary>
        public static int[] ZoneMap(PaintTemplate template, int width, int height)
        {
            var key = (template, width, height);
            if (!zoneMapCache.TryGetValue(key, out int[] zoneMap))
                zoneMapCache[key] = zoneMap = template.BuildZoneMap(width, height);
            return zoneMap;
        }

        static int DistanceSq(Color32 a, Color32 b)
        {
            int dr = a.r - b.r, dg = a.g - b.g, db = a.b - b.b;
            return dr * dr + dg * dg + db * db;
        }
    }
}
