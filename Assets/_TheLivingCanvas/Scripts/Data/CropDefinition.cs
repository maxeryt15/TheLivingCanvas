using TheLivingCanvas.Growth;
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

        public string Id => id;
        public string DisplayName => displayName;
        public PaintTemplate Template => template;
        public float GrowthDuration => growthDuration;
        public CropPlant PlantPrefab => plantPrefab;

#if UNITY_EDITOR
        public void EditorSetup(string newId, string newDisplayName, PaintTemplate newTemplate, float newGrowthDuration, CropPlant newPlantPrefab)
        {
            id = newId;
            displayName = newDisplayName;
            template = newTemplate;
            growthDuration = newGrowthDuration;
            plantPrefab = newPlantPrefab;
        }
#endif
    }
}
