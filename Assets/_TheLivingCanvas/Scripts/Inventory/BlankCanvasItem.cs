using TheLivingCanvas.Data;
using UnityEngine;

namespace TheLivingCanvas.Inventory
{
    /// <summary>Lienzo en blanco de un tipo: el caballete gasta uno al empezar cada pintura. Se compra en la tienda.</summary>
    public class BlankCanvasItem : InventoryItem
    {
        public BlankCanvasItem(CanvasType type, int quantity)
        {
            Type = type;
            Quantity = quantity;
        }

        public CanvasType Type { get; }

        /// <summary>Clave de apilado de los lienzos de un tipo (una pila por tipo).</summary>
        public static string KeyFor(CanvasType type) => $"canvas:{type.Id}";

        public override string DisplayName => Type.DisplayName;
        public override string Detail => $"x{Quantity}";
        public override Texture Icon => Texture2D.whiteTexture;
        public override string StackKey => KeyFor(Type);
    }
}
