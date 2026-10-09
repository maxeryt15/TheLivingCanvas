using System.Linq;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using UnityEngine;

namespace TheLivingCanvas.Economy
{
    /// <summary>
    /// Caja de venta: al interactuar vende toda la cosecha que lleva el jugador al precio de cada cultivo
    /// (las variantes raras valen más).
    /// Las pinturas y semillas no se venden.
    /// </summary>
    public class SellCrate : MonoBehaviour, IInteractable
    {
        PlayerInventory inventory;

        public string Prompt => $"Sell crops (+{Value(inventory)} coins)";
        public bool CanInteract => Value(inventory) > 0;

        void Awake() => inventory = FindAnyObjectByType<PlayerInventory>();

        public void Interact(PlayerInteractor interactor)
        {
            var playerInventory = interactor.GetComponent<PlayerInventory>();
            var crops = playerInventory.Items.OfType<CropItem>().ToList();
            int total = 0;
            foreach (var crop in crops)
            {
                total += crop.Quantity * crop.UnitPrice;
                playerInventory.Remove(crop);
            }
            interactor.GetComponent<Wallet>().Add(total);
        }

        static int Value(PlayerInventory inventory) =>
            inventory == null ? 0 : inventory.Items.OfType<CropItem>().Sum(c => c.Quantity * c.UnitPrice);
    }
}
