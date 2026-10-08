using UnityEngine;

namespace TheLivingCanvas.Data
{
    /// <summary>Un color pintable. En la Fase 8 se convertirá en un recurso (obtención, consumo).</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Pigment", fileName = "Pigment")]
    public class PigmentDefinition : ScriptableObject
    {
        [SerializeField] string id;
        [SerializeField] string displayName;
        [SerializeField] Color color = Color.white;

        public string Id => id;
        public string DisplayName => displayName;
        public Color Color => color;

#if UNITY_EDITOR
        /// <summary>Solo para generar los assets desde herramientas de editor.</summary>
        public void EditorSetup(string newId, string newDisplayName, Color newColor)
        {
            id = newId;
            displayName = newDisplayName;
            color = newColor;
        }
#endif
    }
}
