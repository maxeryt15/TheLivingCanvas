using UnityEngine;

namespace TheLivingCanvas.Inventory
{
    /// <summary>Lienzo en blanco: el caballete gasta uno al empezar cada pintura. Se compra en la tienda.</summary>
    public class BlankCanvasItem : InventoryItem
    {
        public const string Key = "canvas:blank";

        public BlankCanvasItem(int quantity) => Quantity = quantity;

        public override string DisplayName => "Blank canvas";
        public override string Detail => $"x{Quantity}";
        public override Texture Icon => Texture2D.whiteTexture;
        public override string StackKey => Key;
    }
}
