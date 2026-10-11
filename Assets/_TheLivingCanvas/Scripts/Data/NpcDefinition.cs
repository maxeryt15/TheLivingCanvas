using UnityEngine;

namespace TheLivingCanvas.Data
{
    /// <summary>Un personaje no jugable: su nombre y lo que dice al saludar.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Npc", fileName = "Npc")]
    public class NpcDefinition : ScriptableObject
    {
        [SerializeField] string displayName;
        [SerializeField] string[] greetingLines;

        public string DisplayName => displayName;
        public string[] GreetingLines => greetingLines;

#if UNITY_EDITOR
        /// <summary>Solo para generar los assets desde herramientas de editor.</summary>
        public void EditorSetup(string newDisplayName, string[] newGreetingLines)
        {
            displayName = newDisplayName;
            greetingLines = newGreetingLines;
        }
#endif
    }
}
