using TheLivingCanvas.Data;
using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Economy
{
    /// <summary>Boceto de un cultivo: al comprarlo se puede elegir en el caballete. Se compra una sola vez.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Shop/Sketch Offer", fileName = "Offer_Sketch")]
    public class SketchOffer : ShopOffer
    {
        [SerializeField] CropDefinition crop;

        public override Texture Icon => base.Icon != null ? base.Icon : crop.Icon;

        public override bool IsAvailable(GameObject buyer) => !buyer.GetComponent<Sketchbook>().Knows(crop);

        public override void Deliver(GameObject buyer) => buyer.GetComponent<Sketchbook>().Learn(crop);

#if UNITY_EDITOR
        public void EditorSetCrop(CropDefinition newCrop) => crop = newCrop;
#endif
    }
}
