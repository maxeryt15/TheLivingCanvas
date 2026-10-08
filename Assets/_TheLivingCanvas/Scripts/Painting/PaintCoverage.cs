using System.Collections.Generic;
using TheLivingCanvas.Data;
using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>Resultado del análisis de cobertura de una pintura (fracciones 0–1 del área analizada).</summary>
    public class CoverageResult
    {
        public int AnalyzedPixels;
        /// <summary>Fracción con pintura (todo lo que no es la tela).</summary>
        public float Painted;
        /// <summary>Fracción por pigmento (píxeles cercanos a ese color).</summary>
        public readonly Dictionary<PigmentDefinition, float> ByPigment = new();
        /// <summary>Pintura que no se parece a ningún pigmento: bordes suaves, mezclas, colores superpuestos.</summary>
        public float Mixed;
    }

    /// <summary>
    /// Clasifica cada píxel como tela, un pigmento de la paleta o "mezcla".
    /// Preparado para analizar solo una zona (máscara) en la Fase 4.
    /// </summary>
    public static class PaintCoverage
    {
        // Distancias RGB (0–255) al cuadrado.
        const int CanvasTolerance = 30 * 30;
        const int PigmentTolerance = 45 * 45;

        /// <param name="mask">Opcional: mismo tamaño que la pintura; solo se analizan los píxeles en true.</param>
        public static CoverageResult Analyze(PaintSurface surface, IReadOnlyList<PigmentDefinition> palette, bool[] mask = null)
        {
            var pixels = surface.Pixels;
            Color32 canvas = surface.BaseColor;
            var pigmentColors = new Color32[palette.Count];
            var pigmentCounts = new int[palette.Count];
            for (int p = 0; p < palette.Count; p++)
                pigmentColors[p] = palette[p].Color;

            int analyzed = 0, painted = 0, mixed = 0;
            for (int i = 0; i < pixels.Length; i++)
            {
                if (mask != null && !mask[i]) continue;
                analyzed++;
                Color32 c = pixels[i];
                if (DistanceSq(c, canvas) <= CanvasTolerance) continue;
                painted++;

                int best = -1, bestDistance = int.MaxValue;
                for (int p = 0; p < pigmentColors.Length; p++)
                {
                    int d = DistanceSq(c, pigmentColors[p]);
                    if (d < bestDistance) { bestDistance = d; best = p; }
                }
                if (best >= 0 && bestDistance <= PigmentTolerance) pigmentCounts[best]++;
                else mixed++;
            }

            var result = new CoverageResult { AnalyzedPixels = analyzed };
            if (analyzed == 0) return result;
            float inv = 1f / analyzed;
            result.Painted = painted * inv;
            result.Mixed = mixed * inv;
            for (int p = 0; p < palette.Count; p++)
                result.ByPigment[palette[p]] = pigmentCounts[p] * inv;
            return result;
        }

        static int DistanceSq(Color32 a, Color32 b)
        {
            int dr = a.r - b.r, dg = a.g - b.g, db = a.b - b.b;
            return dr * dr + dg * dg + db * db;
        }
    }
}
