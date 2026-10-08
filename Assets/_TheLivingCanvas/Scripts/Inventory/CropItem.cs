using TheLivingCanvas.Data;
using UnityEngine;

namespace TheLivingCanvas.Inventory
{
    /// <summary>Cosecha de un cultivo (ej. Sunflower ×3). Apilable por cultivo.</summary>
    public class CropItem : InventoryItem
    {
        public CropItem(CropDefinition crop, int quantity)
        {
            Crop = crop;
            Quantity = quantity;
        }

        public CropDefinition Crop { get; }

        public override string DisplayName => Crop.DisplayName;
        public override string Detail => $"x{Quantity}";
        public override Texture Icon => Crop.Icon;
        public override string StackKey => $"crop:{Crop.Id}";
    }
}
