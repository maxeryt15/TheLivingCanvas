using UnityEngine;

namespace TheLivingCanvas.Data
{
    /// <summary>Un personaje no jugable: su nombre, lo que dice al saludar y sus encargos.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Npc", fileName = "Npc")]
    public class NpcDefinition : ScriptableObject
    {
        [SerializeField] string displayName;
        [SerializeField] string[] greetingLines;
        [SerializeField] CommissionDefinition[] commissions;

        public string DisplayName => displayName;
        public string[] GreetingLines => greetingLines;
        /// <summary>Sus encargos, en orden.</summary>
        public CommissionDefinition[] Commissions => commissions;

#if UNITY_EDITOR
        /// <summary>Solo para generar los assets desde herramientas de editor.</summary>
        public void EditorSetup(string newDisplayName, string[] newGreetingLines, CommissionDefinition[] newCommissions)
        {
            displayName = newDisplayName;
            greetingLines = newGreetingLines;
            commissions = newCommissions;
        }
#endif
    }
}
