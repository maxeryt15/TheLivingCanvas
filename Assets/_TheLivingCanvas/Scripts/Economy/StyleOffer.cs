using TheLivingCanvas.Data;
using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Economy
{
    /// <summary>Un estilo de pintura nuevo para el caballete. Se compra una sola vez.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Shop/Style Offer", fileName = "Offer_Style")]
    public class StyleOffer : ShopOffer
    {
        [SerializeField] StyleDefinition style;

        public override bool IsAvailable(GameObject buyer) => !buyer.GetComponent<Sketchbook>().KnowsStyle(style);

        public override void Deliver(GameObject buyer) => buyer.GetComponent<Sketchbook>().LearnStyle(style);

#if UNITY_EDITOR
        public void EditorSetStyle(StyleDefinition newStyle) => style = newStyle;
#endif
    }
}
