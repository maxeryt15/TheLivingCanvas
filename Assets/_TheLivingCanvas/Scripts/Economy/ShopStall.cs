using TheLivingCanvas.Interaction;
using UnityEngine;

namespace TheLivingCanvas.Economy
{
    /// <summary>Puesto de la tienda: interactuar abre el panel de compra.</summary>
    public class ShopStall : MonoBehaviour, IInteractable
    {
        [SerializeField] ShopUI shop;

        public string Prompt => "Shop";
        public bool CanInteract => !shop.IsOpen;

        public void Interact(PlayerInteractor interactor) => shop.Open(interactor.gameObject);
    }
}
