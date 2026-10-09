using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Economy
{
    /// <summary>Recarga de un color que ya se tiene: más unidades de pigmento. Se puede comprar sin límite.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Shop/Refill Offer", fileName = "Offer_Refill")]
    public class RefillOffer : PigmentOffer
    {
        public override bool IsAvailable(GameObject buyer)
        {
            var brush = FindAnyObjectByType<PaintBrushController>();
            return brush != null && brush.HasPigment(Pigment);
        }

        public override void Deliver(GameObject buyer) => buyer.GetComponent<PigmentStock>().Add(Pigment, Units);
    }
}
