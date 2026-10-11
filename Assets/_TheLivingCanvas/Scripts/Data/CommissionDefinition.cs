using TheLivingCanvas.Inventory;
using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Data
{
    /// <summary>Un encargo de un personaje: qué pintura quiere (cultivo y calidad mínima) y lo que dice al pedirla y al recibirla.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Commission", fileName = "Commission")]
    public class CommissionDefinition : ScriptableObject
    {
        [SerializeField] CropDefinition crop;
        [SerializeField] PaintingQuality minQuality;
        [SerializeField] string[] requestLines;
        [SerializeField] string[] thanksLines;

        public CropDefinition Crop => crop;
        public PaintingQuality MinQuality => minQuality;
        public string[] RequestLines => requestLines;
        public string[] ThanksLines => thanksLines;

        /// <summary>Resumen para la interfaz, ej. "Sunflower painting · Good or better".</summary>
        public string Summary => $"{crop.DisplayName} painting · {minQuality} or better";

        /// <summary>Vale cualquier variante del cultivo con calidad suficiente; las semillas no son pinturas.</summary>
        public bool Accepts(PaintingItem painting) =>
            painting is not SeedItem && painting.Crop == crop && painting.Result.Quality >= minQuality;

#if UNITY_EDITOR
        /// <summary>Solo para generar los assets desde herramientas de editor.</summary>
        public void EditorSetup(CropDefinition newCrop, PaintingQuality newMinQuality, string[] newRequestLines, string[] newThanksLines)
        {
            crop = newCrop;
            minQuality = newMinQuality;
            requestLines = newRequestLines;
            thanksLines = newThanksLines;
        }
#endif
    }
}
