using UnityEngine;

namespace TheLivingCanvas.Data
{
    public enum BrushKind
    {
        /// <summary>Pincel redondo: estampa el color por donde pasa.</summary>
        Round,
        /// <summary>Rellena de golpe la zona de la plantilla en la que se hace clic.</summary>
        Fill,
        /// <summary>Veladura: capa semitransparente que se mezcla con lo que hay debajo (amarillo sobre rojo = naranja).</summary>
        Glaze
    }

    /// <summary>Un pincel: qué hace (su tipo) y cómo se llama en la paleta.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Brush", fileName = "Brush")]
    public class BrushDefinition : ScriptableObject
    {
        [SerializeField] string id;
        [SerializeField] string displayName;
        [SerializeField] BrushKind kind;

        public string Id => id;
        public string DisplayName => displayName;
        public BrushKind Kind => kind;

#if UNITY_EDITOR
        public void EditorSetup(string newId, string newDisplayName, BrushKind newKind)
        {
            id = newId;
            displayName = newDisplayName;
            kind = newKind;
        }
#endif
    }
}
