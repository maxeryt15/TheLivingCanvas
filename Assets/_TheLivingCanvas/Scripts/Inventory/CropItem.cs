using TheLivingCanvas.Data;
using UnityEngine;

namespace TheLivingCanvas.Inventory
{
    /// <summary>Cosecha de un cultivo (ej. Sunflower ×3, Blue Sunflower ×2). Apilable por cultivo y variante.</summary>
    public class CropItem : InventoryItem
    {
        public CropItem(CropDefinition crop, CropVariant variant, int quantity)
        {
            Crop = crop;
            Variant = variant;
            Quantity = quantity;
        }

        public CropDefinition Crop { get; }
        /// <summary>null = el cultivo normal.</summary>
        public CropVariant Variant { get; }
        public Rarity Rarity => Variant?.rarity ?? Rarity.Common;
        /// <summary>Monedas por unidad: el precio del cultivo según la rareza.</summary>
        public int UnitPrice => Mathf.RoundToInt(Crop.SellPrice * Rarity.PriceMultiplier());

        public override string DisplayName => Variant?.displayName ?? Crop.DisplayName;
        public override string Detail => Rarity == Rarity.Common ? $"x{Quantity}" : $"x{Quantity} · {Rarity}";
        public override Texture Icon => Crop.Icon;
        public override string StackKey => Variant == null ? $"crop:{Crop.Id}" : $"crop:{Crop.Id}:{Variant.id}";
        public override string ToastText => Rarity == Rarity.Common ? base.ToastText : $"{base.ToastText} ({Rarity}!)";
    }
}
