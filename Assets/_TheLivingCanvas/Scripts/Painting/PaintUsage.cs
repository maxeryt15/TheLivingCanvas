using System.Collections.Generic;
using TheLivingCanvas.Data;
using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Cuánto pigmento lleva una pintura: cada píxel pintado se atribuye al color de la paleta más cercano
    /// (los bordes suaves mezclan colores) y se cuenta en unidades de <see cref="PixelsPerUnit"/> píxeles.
    /// Lo rellenado con el pincel Fill cuesta <see cref="FillCostMultiplier"/> veces más.
    /// </summary>
    public static class PaintUsage
    {
        /// <summary>Un girasol completo ronda 45 de amarillo, 8 de ocre y 10 de verde.</summary>
        public const int PixelsPerUnit = 1000;
        const int CanvasTolerance = 30 * 30; // igual que PaintEvaluator: "tela sin pintar"
        public const float FillCostMultiplier = 1.5f;

        /// <summary>Unidades por pigmento (solo los que redondean a 1 o más: las motas sueltas no cuentan).</summary>
        public static Dictionary<PigmentDefinition, int> Measure(PaintSurface surface, IReadOnlyList<PigmentDefinition> palette)
        {
            var counts = new float[palette.Count];
            var colors = new Color32[palette.Count];
            for (int p = 0; p < palette.Count; p++)
                colors[p] = palette[p].Color;

            Color32 canvas = surface.BaseColor;
            foreach (var c in surface.Pixels)
            {
                if (palette.Count == 0 || DistanceSq(c, canvas) <= CanvasTolerance) continue;
                int nearest = 0;
                int best = int.MaxValue;
                for (int p = 0; p < colors.Length; p++)
                {
                    int d = DistanceSq(c, colors[p]);
                    if (d < best)
                    {
                        best = d;
                        nearest = p;
                    }
                }
                counts[nearest] += c.a == PaintSurface.FillAlpha ? FillCostMultiplier : 1f;
            }

            var usage = new Dictionary<PigmentDefinition, int>();
            for (int p = 0; p < palette.Count; p++)
            {
                int units = Mathf.RoundToInt(counts[p] / PixelsPerUnit);
                if (units > 0) usage[palette[p]] = units;
            }
            return usage;
        }

        static int DistanceSq(Color32 a, Color32 b)
        {
            int dr = a.r - b.r, dg = a.g - b.g, db = a.b - b.b;
            return dr * dr + dg * dg + db * db;
        }
    }
}
