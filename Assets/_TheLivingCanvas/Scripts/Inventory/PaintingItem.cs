using TheLivingCanvas.Data;
using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Inventory
{
    /// <summary>Una pintura terminada y recogida del caballete: su imagen, su cultivo, su variante, su lienzo y su calidad.</summary>
    public class PaintingItem : InventoryItem
    {
        /// <summary>La variante se decide aquí, con los colores recién pintados (las semillas la heredan).</summary>
        public PaintingItem(CropDefinition crop, CanvasType canvasType, PaintingResult result, Texture2D image)
            : this(crop, crop.FindVariant(result), canvasType, result, image) { }

        /// <summary>Reconstruye una pintura tal como se guardó (sin volver a decidir la variante).</summary>
        public PaintingItem(CropDefinition crop, CropVariant variant, CanvasType canvasType, PaintingResult result, Texture2D image,
            int generation, Mutation mutation)
            : this(crop, variant, canvasType, result, image)
        {
            Generation = generation;
            Mutation = mutation;
        }

        protected PaintingItem(CropDefinition crop, CropVariant variant, CanvasType canvasType, PaintingResult result, Texture2D image)
        {
            Crop = crop;
            Variant = variant;
            CanvasType = canvasType;
            Result = result;
            Image = image;
        }

        public CropDefinition Crop { get; }
        /// <summary>null = el cultivo normal.</summary>
        public CropVariant Variant { get; }
        /// <summary>El lienzo en que se pintó: decide la cosecha y el tamaño de la parcela.</summary>
        public CanvasType CanvasType { get; }
        public PaintingResult Result { get; }
        public Texture2D Image { get; }
        /// <summary>Nombre del PNG guardado (null hasta el primer guardado); lo asigna <see cref="Save.PaintingStore"/>.</summary>
        public string ImageFile { get; internal set; }
        /// <summary>0 = la pintura original; cada semilla replantada suma 1.</summary>
        public int Generation { get; protected set; }
        /// <summary>None en una pintura recién hecha; la semilla de una planta mutada la hereda.</summary>
        public Mutation Mutation { get; protected set; }

        /// <summary>Nombre del cultivo o de su variante (ej. "Blue Sunflower").</summary>
        public string CropName => Variant?.displayName ?? Crop.DisplayName;

        public override string DisplayName => $"{CropName} painting";
        /// <summary>null = Classic.</summary>
        public StyleDefinition Style => Result.Style;

        public override string Detail => $"{Result.Quality} · {CanvasType.DisplayName}" + (Style != null ? $" · {Style.DisplayName}" : string.Empty)
            + (Mutation != Mutation.None ? $" · {Mutation.Name()}" : string.Empty);
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

        /// <summary>La semilla hereda la mutación de la planta que la dio (<paramref name="mutation"/>).</summary>
        public SeedItem(PaintingItem parent, Mutation mutation)
            : base(parent.Crop, parent.Variant, parent.CanvasType, parent.Result.Faded(FadePerGeneration), FadeImage(parent.Image))
        {
            Generation = parent.Generation + 1;
            Mutation = mutation;
        }

        /// <summary>Reconstruye una semilla tal como se guardó (sin desvanecer otra vez).</summary>
        public SeedItem(CropDefinition crop, CropVariant variant, CanvasType canvasType, PaintingResult result, Texture2D image,
            int generation, Mutation mutation)
            : base(crop, variant, canvasType, result, image, generation, mutation) { }

        /// <summary>false si la pintura ya está en lo más bajo (Normal) y no deja semilla.</summary>
        public static bool CanSeed(PaintingItem painting) => painting.Result.Quality > PaintingQuality.Normal;

        public override string DisplayName => $"{CropName} seed";

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
