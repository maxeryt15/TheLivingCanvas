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
        public override string ToastText => $"+1 {DisplayName} ({Detail})";
    }

    /// <summary>
    /// Semilla obtenida al cosechar: guarda la pintura de la que nació y, al plantarla,
    /// vuelve a crear esa misma parcela (y el mismo cultivo).
    /// </summary>
    public class SeedItem : PaintingItem
    {
        public SeedItem(PaintingItem painting) : base(painting.Crop, painting.Result, painting.Image) { }

        public override string DisplayName => $"{Crop.DisplayName} seed";
    }
}
