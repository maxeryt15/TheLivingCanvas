using TheLivingCanvas.Data;
using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Economy
{
    /// <summary>Un pincel nuevo para la paleta. Se compra una sola vez.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Shop/Brush Offer", fileName = "Offer_Brush")]
    public class BrushOffer : ShopOffer
    {
        [SerializeField] BrushDefinition brush;

        public override bool IsAvailable(GameObject buyer)
        {
            var controller = FindAnyObjectByType<PaintBrushController>();
            return controller != null && !controller.HasBrush(brush);
        }

        public override void Deliver(GameObject buyer) => FindAnyObjectByType<PaintBrushController>().AddBrush(brush);

#if UNITY_EDITOR
        public void EditorSetBrush(BrushDefinition newBrush) => brush = newBrush;
#endif
    }
}
