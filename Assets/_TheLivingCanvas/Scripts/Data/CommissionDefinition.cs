using System.Linq;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Data
{
    /// <summary>Un encargo de un personaje: qué pintura quiere (cultivo y calidad mínima) y lo que dice al pedirla y al recibirla.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Commission", fileName = "Commission")]
    public class CommissionDefinition : ScriptableObject
    {
        [Tooltip("Cultivo pedido; vacío = cualquier cultivo.")]
        [SerializeField] CropDefinition crop;
        [Tooltip("Id de la variante pedida (ej. \"blue\"); vacío = cualquier variante del cultivo.")]
        [SerializeField] string variantId;
        [SerializeField] PaintingQuality minQuality;
        [SerializeField] string[] requestLines;
        [SerializeField] string[] thanksLines;
        [SerializeField] int rewardCoins;
        [SerializeField] int rewardXp;
        [Tooltip("Pigmento de recompensa (opcional).")]
        [SerializeField] PigmentDefinition rewardPigment;
        [SerializeField] int rewardPigmentAmount;
        [Tooltip("Estilo pedido (opcional); vacío = cualquier estilo, incluido Classic.")]
        [SerializeField] StyleDefinition style;
        [Tooltip("Pigmento que debe verse en la pintura (opcional); vacío = cualquiera.")]
        [SerializeField] PigmentDefinition requiredPigment;

        public StyleDefinition Style => style;
        public PigmentDefinition RequiredPigment => requiredPigment;
        public CropDefinition Crop => crop;
        public PaintingQuality MinQuality => minQuality;
        public string[] RequestLines => requestLines;
        public string[] ThanksLines => thanksLines;
        public int RewardCoins => rewardCoins;
        public int RewardXp => rewardXp;
        public PigmentDefinition RewardPigment => rewardPigment;
        public int RewardPigmentAmount => rewardPigmentAmount;

        /// <summary>Resumen para la interfaz, ej. "Blue Sunflower painting · Good or better".</summary>
        public string Summary
        {
            get
            {
                var variant = string.IsNullOrEmpty(variantId) ? null : System.Array.Find(crop.Variants, v => v.id == variantId);
                var styleText = style != null ? $" in {style.DisplayName} style" : "";
                var pigmentText = requiredPigment != null ? $" with {requiredPigment.DisplayName}" : "";
                return $"{(crop == null ? "Any" : variant?.displayName ?? crop.DisplayName)} painting{styleText}{pigmentText} · {minQuality} or better";
            }
        }

        /// <summary>Vale la variante pedida (o cualquiera si no se pide ninguna) con calidad suficiente; las semillas no son pinturas.</summary>
        public bool Accepts(PaintingItem painting) =>
            painting is not SeedItem && (crop == null || painting.Crop == crop) && painting.Result.Quality >= minQuality
            && (string.IsNullOrEmpty(variantId) || painting.Variant?.id == variantId)
            && (style == null || painting.Style == style)
            && (requiredPigment == null || UsesPigment(painting.Result));

        /// <summary>Alguna zona de la pintura tiene un color dominante cercano al pigmento pedido.</summary>
        bool UsesPigment(PaintingResult result) =>
            result.Zones.Any(zone => CropDefinition.ColorDistance(zone.DominantColor, requiredPigment.Color) <= CropDefinition.MaxVariantDistance);

#if UNITY_EDITOR
        /// <summary>Solo para generar los assets desde herramientas de editor.</summary>
        public void EditorSetup(CropDefinition newCrop, string newVariantId, PaintingQuality newMinQuality, string[] newRequestLines, string[] newThanksLines,
            int newRewardCoins, int newRewardXp, PigmentDefinition newRewardPigment = null, int newRewardPigmentAmount = 0,
            StyleDefinition newStyle = null, PigmentDefinition newRequiredPigment = null)
        {
            style = newStyle;
            requiredPigment = newRequiredPigment;
            crop = newCrop;
            variantId = newVariantId;
            minQuality = newMinQuality;
            requestLines = newRequestLines;
            thanksLines = newThanksLines;
            rewardCoins = newRewardCoins;
            rewardXp = newRewardXp;
            rewardPigment = newRewardPigment;
            rewardPigmentAmount = newRewardPigmentAmount;
        }
#endif
    }
}
