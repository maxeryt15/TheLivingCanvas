using TheLivingCanvas.Data;
using TheLivingCanvas.Inventory;
using UnityEngine;

namespace TheLivingCanvas.Economy
{
    /// <summary>Oferta de lienzos en blanco de un tipo para el caballete.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Shop/Canvas Offer", fileName = "Offer_Canvas")]
    public class CanvasOffer : ShopOffer
    {
        [SerializeField] CanvasType canvasType;
        [SerializeField] int quantity = 1;

        public override Texture Icon => base.Icon != null ? base.Icon : Texture2D.whiteTexture;

        public override void Deliver(GameObject buyer) =>
            buyer.GetComponent<PlayerInventory>().Add(new BlankCanvasItem(canvasType, quantity));

#if UNITY_EDITOR
        public void EditorSetCanvasType(CanvasType newType) => canvasType = newType;
#endif
    }
}
