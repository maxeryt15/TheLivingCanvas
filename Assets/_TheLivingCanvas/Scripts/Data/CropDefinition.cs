using TheLivingCanvas.Growth;
using TheLivingCanvas.Painting;
using TheLivingCanvas.Seasons;
using UnityEngine;

namespace TheLivingCanvas.Data
{
    /// <summary>Qué es un cultivo, qué hay que pintar para obtenerlo y cómo crece.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Crop", fileName = "Crop")]
    public class CropDefinition : ScriptableObject
    {
        [SerializeField] string id;
        [SerializeField] string displayName;
        [SerializeField] PaintTemplate template;
        [Tooltip("Segundos hasta alcanzar el tamaño final tras la transición (vertical slice: rápido).")]
        [SerializeField] float growthDuration = 20f;
        [Tooltip("Planta 3D que crece de la parcela.")]
        [SerializeField] CropPlant plantPrefab;
        [Tooltip("Icono de la cosecha en el inventario.")]
        [SerializeField] Texture2D icon;
        [Tooltip("Monedas por unidad cosechada al venderla.")]
        [SerializeField] int sellPrice = 10;
        [Tooltip("Pigmento que da al molerlo en el mortero (las variantes dan el suyo).")]
        [SerializeField] PigmentDefinition pigment;
        [SerializeField] int pigmentPerUnit = 10;
        [Tooltip("Variantes por color; si ninguna encaja, sale el cultivo normal (Common).")]
        [SerializeField] CropVariant[] variants = System.Array.Empty<CropVariant>();

        [Tooltip("Estación en la que rinde más: cosechar en ella da una unidad extra.")]
        [SerializeField] Season favoriteSeason;

        /// <summary>Unidades extra al cosechar en la estación favorita (se suman tras calidad × lienzo).</summary>
        public const int InSeasonBonus = 1;

        public string Id => id;
        public string DisplayName => displayName;
        public PaintTemplate Template => template;
        public float GrowthDuration => growthDuration;
        public CropPlant PlantPrefab => plantPrefab;
        public Texture2D Icon => icon;
        public int SellPrice => sellPrice;
        public CropVariant[] Variants => variants;
        public PigmentDefinition Pigment => pigment;
        public int PigmentPerUnit => pigmentPerUnit;
        public Season FavoriteSeason => favoriteSeason;

        public bool IsInSeason(Season season) => season == favoriteSeason;

        /// <summary>
        /// Variante que corresponde a la pintura, o null (cultivo normal). En cada zona clave se compara el color
        /// dominante pintado con el color sugerido y los de sus variantes: gana el más cercano, y además tiene que
        /// parecerse de verdad al pigmento de la variante (pintar los pétalos de verde no da un girasol rojo).
        /// </summary>
        public CropVariant FindVariant(PaintingResult painting)
        {
            CropVariant best = null;
            float bestDistance = float.MaxValue;
            foreach (var zone in painting.Zones)
            {
                float suggested = zone.Requirement.suggestedPigment != null
                    ? ColorDistance(zone.DominantColor, zone.Requirement.suggestedPigment.Color)
                    : float.MaxValue;
                foreach (var variant in variants)
                {
                    if (variant.zoneName != zone.Requirement.zoneName || variant.pigment == null) continue;
                    float distance = ColorDistance(zone.DominantColor, variant.pigment.Color);
                    if (distance <= MaxVariantDistance && distance < suggested && distance < bestDistance)
                    {
                        best = variant;
                        bestDistance = distance;
                    }
                }
            }
            return best;
        }

        /// <summary>Distancia RGB² máxima entre lo pintado y el pigmento de la variante (~0.25 por canal).</summary>
        const float MaxVariantDistance = 0.06f;

        static float ColorDistance(Color a, Color b) =>
            new Vector3(a.r - b.r, a.g - b.g, a.b - b.b).sqrMagnitude;

#if UNITY_EDITOR
        public void EditorSetup(string newId, string newDisplayName, PaintTemplate newTemplate, float newGrowthDuration,
            CropPlant newPlantPrefab, Texture2D newIcon, int newSellPrice)
        {
            id = newId;
            displayName = newDisplayName;
            template = newTemplate;
            growthDuration = newGrowthDuration;
            plantPrefab = newPlantPrefab;
            icon = newIcon;
            sellPrice = newSellPrice;
        }

        public void EditorSetFavoriteSeason(Season season) => favoriteSeason = season;

        public void EditorSetVariants(CropVariant[] newVariants) => variants = newVariants;

        public void EditorSetPigmentYield(PigmentDefinition newPigment, int newPigmentPerUnit)
        {
            pigment = newPigment;
            pigmentPerUnit = newPigmentPerUnit;
        }
#endif
    }
}
