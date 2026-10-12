using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Data
{
    /// <summary>Mutación al azar de una planta al empezar a crecer; las semillas la heredan.</summary>
    public enum Mutation { None, Giant, Luminous, Twin }

    public static class Mutations
    {
        /// <summary>Las mutaciones reales (sin None), en el orden de la colección.</summary>
        public static readonly Mutation[] All = { Mutation.Giant, Mutation.Twin, Mutation.Luminous };

        /// <summary>Probabilidad de mutar según la calidad de la pintura.</summary>
        public static float Chance(PaintingQuality quality) => quality switch
        {
            PaintingQuality.Normal => 0.05f,
            PaintingQuality.Good => 0.08f,
            PaintingQuality.Excellent => 0.11f,
            _ => 0.15f
        };

        /// <summary>Tira el dado: None, o una de las tres con la misma probabilidad.</summary>
        public static Mutation Roll(PaintingQuality quality) =>
            Random.value < Chance(quality) ? All[Random.Range(0, All.Length)] : Mutation.None;

        public static string Name(this Mutation mutation) => mutation.ToString();

        /// <summary>Efecto en una frase corta.</summary>
        public static string Effect(this Mutation mutation) => mutation switch
        {
            Mutation.Giant => "Grows bigger, +1 harvest",
            Mutation.Twin => "Two plants, double harvest",
            Mutation.Luminous => "Glows, harvest pays double",
            _ => string.Empty
        };
    }
}
