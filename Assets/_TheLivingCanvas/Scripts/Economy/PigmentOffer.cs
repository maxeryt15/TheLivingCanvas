using TheLivingCanvas.Data;
using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Economy
{
    /// <summary>Un pigmento nuevo para la paleta, con algo de pigmento para empezar. Se compra una sola vez.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Shop/Pigment Offer", fileName = "Offer_Pigment")]
    public class PigmentOffer : ShopOffer
    {
        [SerializeField] PigmentDefinition pigment;
        [Tooltip("Unidades de pigmento que vienen con el color.")]
        [SerializeField] int units = 30;

        Texture2D swatch;

        public PigmentDefinition Pigment => pigment;

        /// <summary>Sin icono propio: una muestra del color (creada en runtime, no se guarda).</summary>
        public override Texture Icon
        {
            get
            {
                if (base.Icon != null) return base.Icon;
                if (swatch == null)
                {
                    swatch = new Texture2D(1, 1) { hideFlags = HideFlags.DontSave };
                    swatch.SetPixel(0, 0, pigment.Color);
                    swatch.Apply();
                }
                return swatch;
            }
        }

        public override bool IsAvailable(GameObject buyer)
        {
            var brush = FindAnyObjectByType<PaintBrushController>();
            return brush != null && !brush.HasPigment(pigment);
        }

        public override void Deliver(GameObject buyer)
        {
            FindAnyObjectByType<PaintBrushController>().AddPigment(pigment);
            buyer.GetComponent<PigmentStock>().Add(pigment, units);
        }

#if UNITY_EDITOR
        public void EditorSetPigment(PigmentDefinition newPigment) => pigment = newPigment;
#endif
    }
}
