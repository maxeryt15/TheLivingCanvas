using UnityEngine;

namespace TheLivingCanvas.Data
{
    public enum StyleKind
    {
        /// <summary>Acuarela: trazos translúcidos que se expanden al soltar, perdona el derrame y gasta menos pigmento.</summary>
        Wash,
        /// <summary>Postimpresionista (Fase 16B).</summary>
        Swirl
    }

    /// <summary>Un estilo de pintura que se elige por cuadro en el caballete. El comportamiento depende de su tipo; aquí van los números.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Style", fileName = "Style")]
    public class StyleDefinition : ScriptableObject
    {
        [SerializeField] string id;
        [SerializeField] string displayName;
        [SerializeField, TextArea] string description;
        [SerializeField] StyleKind kind;
        [Tooltip("Multiplica el pigmento que gasta la pintura.")]
        [SerializeField] float pigmentMultiplier = 1f;
        [Tooltip("Multiplica la penalización por pintura derramada fuera de las zonas.")]
        [SerializeField] float spillMultiplier = 1f;
        [Tooltip("Multiplica la duración del crecimiento del cultivo (menos de 1 = crece más rápido).")]
        [SerializeField] float growthMultiplier = 1f;
        [Tooltip("Cuánto se aclaran hacia el blanco los colores del cultivo 3D (0–1).")]
        [SerializeField, Range(0f, 1f)] float pastel;
        [Tooltip("Multiplica lo que paga el marchante por la pintura.")]
        [SerializeField] float sellMultiplier = 1f;

        public string Id => id;
        public string DisplayName => displayName;
        public string Description => description;
        public StyleKind Kind => kind;
        public float PigmentMultiplier => pigmentMultiplier;
        public float SpillMultiplier => spillMultiplier;
        public float GrowthMultiplier => growthMultiplier;
        public float Pastel => pastel;
        public float SellMultiplier => sellMultiplier;

#if UNITY_EDITOR
        public void EditorSetup(string newId, string newDisplayName, string newDescription, StyleKind newKind,
            float newPigment, float newSpill, float newGrowth, float newPastel, float newSell)
        {
            id = newId;
            displayName = newDisplayName;
            description = newDescription;
            kind = newKind;
            pigmentMultiplier = newPigment;
            spillMultiplier = newSpill;
            growthMultiplier = newGrowth;
            pastel = newPastel;
            sellMultiplier = newSell;
        }
#endif
    }
}
