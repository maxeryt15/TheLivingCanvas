using TheLivingCanvas.Data;
using TheLivingCanvas.Interaction;
using UnityEngine;

namespace TheLivingCanvas.Npcs
{
    /// <summary>Personaje con el que se puede hablar: se gira hacia el jugador y abre el diálogo con su saludo.</summary>
    public class Npc : MonoBehaviour, IInteractable
    {
        [SerializeField] NpcDefinition definition;
        [SerializeField] DialogueUI dialogueUI;

        public string Prompt => $"Talk to {definition.DisplayName}";
        public bool CanInteract => !dialogueUI.IsOpen;

        public void Interact(PlayerInteractor interactor)
        {
            // Solo gira en el eje vertical para no inclinarse hacia la cámara.
            var toPlayer = interactor.transform.position - transform.position;
            toPlayer.y = 0f;
            if (toPlayer.sqrMagnitude > 0.0001f)
                transform.rotation = Quaternion.LookRotation(toPlayer);

            dialogueUI.Open(definition.DisplayName, definition.GreetingLines);
        }
    }
}
