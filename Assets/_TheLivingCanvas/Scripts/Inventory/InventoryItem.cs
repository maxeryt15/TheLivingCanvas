using UnityEngine;

namespace TheLivingCanvas.Inventory
{
    /// <summary>Algo que el jugador lleva encima. Placeholder: solo nombre, detalle e icono.</summary>
    public abstract class InventoryItem
    {
        public abstract string DisplayName { get; }
        /// <summary>Línea secundaria (ej. la calidad).</summary>
        public virtual string Detail => string.Empty;
        public abstract Texture Icon { get; }
    }
}
