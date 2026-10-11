using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Economy
{
    /// <summary>Una herramienta de pintura nueva (cuentagotas, simetría). Se compra una sola vez.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Shop/Tool Offer", fileName = "Offer_Tool")]
    public class ToolOffer : ShopOffer
    {
        [SerializeField] PaintTool tool;

        public override bool IsAvailable(GameObject buyer)
        {
            var controller = FindAnyObjectByType<PaintBrushController>();
            return controller != null && !controller.HasTool(tool);
        }

        public override void Deliver(GameObject buyer) => FindAnyObjectByType<PaintBrushController>().AddTool(tool);

#if UNITY_EDITOR
        public void EditorSetTool(PaintTool newTool) => tool = newTool;
#endif
    }
}
