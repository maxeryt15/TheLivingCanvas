using System;
using UnityEngine;

namespace TheLivingCanvas.Data
{
    public enum Rarity
    {
        Common,
        Uncommon,
        Rare
    }

    public static class RarityExtensions
    {
        /// <summary>Multiplicador del precio de venta.</summary>
        public static float PriceMultiplier(this Rarity rarity) => rarity switch
        {
            Rarity.Uncommon => 1.5f,
            Rarity.Rare => 2.5f,
            _ => 1f
        };
    }

    /// <summary>
    /// Variante de un cultivo que sale al pintar una zona clave en un color concreto
    /// (ej. pétalos azules = Blue Sunflower). Tiene nombre y rareza propios.
    /// </summary>
    [Serializable]
    public class CropVariant
    {
        public string id;
        public string displayName;
        [Tooltip("Zona de la plantilla que decide la variante.")]
        public string zoneName;
        [Tooltip("Color que hay que pintar en esa zona.")]
        public PigmentDefinition pigment;
        public Rarity rarity = Rarity.Uncommon;
    }
}
