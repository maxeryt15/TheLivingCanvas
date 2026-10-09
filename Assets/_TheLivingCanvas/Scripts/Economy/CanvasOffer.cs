using TheLivingCanvas.Inventory;
using UnityEngine;

namespace TheLivingCanvas.Economy
{
    /// <summary>Oferta de lienzos en blanco para el caballete.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Shop/Canvas Offer", fileName = "Offer_Canvas")]
    public class CanvasOffer : ShopOffer
    {
        [SerializeField] int quantity = 1;

        public override Texture Icon => base.Icon != null ? base.Icon : Texture2D.whiteTexture;

        public override void Deliver(GameObject buyer) =>
            buyer.GetComponent<PlayerInventory>().Add(new BlankCanvasItem(quantity));
    }
}
