using TheLivingCanvas.Data;
using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Inventory
{
    /// <summary>Una pintura terminada y recogida del caballete: su imagen, su cultivo y su calidad.</summary>
    public class PaintingItem : InventoryItem
    {
        public PaintingItem(CropDefinition crop, PaintingResult result, Texture2D image)
        {
            Crop = crop;
            Result = result;
            Image = image;
        }

        public CropDefinition Crop { get; }
        public PaintingResult Result { get; }
        public Texture2D Image { get; }

        public override string DisplayName => $"{Crop.DisplayName} painting";
        public override string Detail => Result.Quality.ToString();
        public override Texture Icon => Image;
    }
}
