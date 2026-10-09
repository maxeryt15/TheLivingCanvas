using TheLivingCanvas.Interaction;
using UnityEngine;

namespace TheLivingCanvas.Economy
{
    /// <summary>Mortero: interactuar abre el panel para moler la cosecha en pigmento.</summary>
    public class MortarStation : MonoBehaviour, IInteractable
    {
        [SerializeField] MortarUI mortar;

        public string Prompt => "Grind crops into pigment";
        public bool CanInteract => !mortar.IsOpen;

        public void Interact(PlayerInteractor interactor) => mortar.Open();
    }
}
