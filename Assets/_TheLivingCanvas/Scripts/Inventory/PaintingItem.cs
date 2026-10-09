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
        /// <summary>0 = la pintura original; cada semilla replantada suma 1.</summary>
        public int Generation { get; protected set; }

        public override string DisplayName => $"{Crop.DisplayName} painting";
        public override string Detail => Result.Quality.ToString();
        public override Texture Icon => Image;
        public override string ToastText => $"+1 {DisplayName} ({Detail})";
    }

    /// <summary>
    /// Semilla obtenida al cosechar: guarda la pintura de la que nació y, al plantarla, vuelve a crear
    /// esa parcela. Cada generación se desvanece: un nivel de calidad menos y colores más pálidos.
    /// Una cosecha de calidad Normal ya no da semilla.
    /// </summary>
    public class SeedItem : PaintingItem
    {
        /// <summary>Cuánto palidece la pintura (y el cultivo) por generación (0–1).</summary>
        const float FadePerGeneration = 0.3f;

        public SeedItem(PaintingItem parent)
            : base(parent.Crop, parent.Result.Faded(FadePerGeneration), FadeImage(parent.Image))
        {
            Generation = parent.Generation + 1;
        }

        /// <summary>false si la pintura ya está en lo más bajo (Normal) y no deja semilla.</summary>
        public static bool CanSeed(PaintingItem painting) => painting.Result.Quality > PaintingQuality.Normal;

        public override string DisplayName => $"{Crop.DisplayName} seed";

        static Texture2D FadeImage(Texture2D source)
        {
            var pixels = source.GetPixels32();
            for (int i = 0; i < pixels.Length; i++)
                pixels[i] = PaintingResult.Fade(pixels[i], FadePerGeneration);
            var faded = new Texture2D(source.width, source.height, TextureFormat.RGBA32, false)
            {
                name = "FadedPainting",
                wrapMode = TextureWrapMode.Clamp
            };
            faded.SetPixels32(pixels);
            faded.Apply(false);
            return faded;
        }
    }
}
