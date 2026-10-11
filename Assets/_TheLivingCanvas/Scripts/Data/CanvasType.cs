using UnityEngine;

namespace TheLivingCanvas.Data
{
    /// <summary>Un tipo de lienzo: sus modificadores sobre la cosecha, el pigmento gastado y el tamaño de la parcela.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Canvas Type", fileName = "Canvas")]
    public class CanvasType : ScriptableObject
    {
        [SerializeField] string id;
        [SerializeField] string displayName;
        [SerializeField, TextArea] string description;
        [Tooltip("Multiplica la cantidad cosechada.")]
        [SerializeField] int harvestMultiplier = 1;
        [Tooltip("Multiplica el pigmento que gasta la pintura al terminarla.")]
        [SerializeField] float pigmentMultiplier = 1f;
        [Tooltip("Escala de la parcela en el suelo (y de la planta que crece en ella).")]
        [SerializeField] float plotScale = 1f;

        public string Id => id;
        public string DisplayName => displayName;
        public string Description => description;
        public int HarvestMultiplier => harvestMultiplier;
        public float PigmentMultiplier => pigmentMultiplier;
        public float PlotScale => plotScale;

#if UNITY_EDITOR
        public void EditorSetup(string newId, string newDisplayName, string newDescription,
            int newHarvestMultiplier, float newPigmentMultiplier, float newPlotScale)
        {
            id = newId;
            displayName = newDisplayName;
            description = newDescription;
            harvestMultiplier = newHarvestMultiplier;
            pigmentMultiplier = newPigmentMultiplier;
            plotScale = newPlotScale;
        }
#endif
    }
}
