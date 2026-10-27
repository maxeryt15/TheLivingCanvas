using UnityEngine;

namespace TheLivingCanvas.Interaction
{
    /// <summary>
    /// Puerta que lleva al jugador a otra area (entrar/salir del museo) mediante AreaTransition.
    /// Necesita un Collider (trigger vale) en el mismo objeto.
    /// </summary>
    public class AreaDoor : MonoBehaviour, IInteractable, IInteractionPriority
    {
        public InteractionPriority Priority => InteractionPriority.Environmental;
        [SerializeField] string prompt = "Enter museum";
        [SerializeField] Transform destination;
        [SerializeField] bool leadsInside;
        [SerializeField] AreaTransition transition;

        public string Prompt => prompt;
        public bool CanInteract => transition != null && !transition.Busy && destination != null;

        public void Interact(PlayerInteractor interactor)
        {
            if (transition != null) transition.Travel(destination, leadsInside);
        }
    }
}
