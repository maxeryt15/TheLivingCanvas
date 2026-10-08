using UnityEngine;

namespace TheLivingCanvas.Inventory
{
    /// <summary>Algo que el jugador lleva encima. Placeholder: nombre, detalle, icono y cantidad.</summary>
    public abstract class InventoryItem
    {
        public abstract string DisplayName { get; }
        /// <summary>Línea secundaria (ej. la calidad o la cantidad).</summary>
        public virtual string Detail => string.Empty;
        public abstract Texture Icon { get; }

        /// <summary>Objetos con la misma clave se apilan en una sola casilla (null = no apilable).</summary>
        public virtual string StackKey => null;
        public int Quantity { get; internal set; } = 1;

        /// <summary>Aviso al recibirlo, ej. "+3 Sunflower".</summary>
        public virtual string ToastText => $"+{Quantity} {DisplayName}";
    }
}
