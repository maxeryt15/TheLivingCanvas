using TheLivingCanvas.Painting;
using UnityEngine;

namespace TheLivingCanvas.Economy
{
    /// <summary>Mejora única: los lienzos nuevos de todos los caballetes se pintan a mayor resolución.</summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/Shop/Canvas Upgrade Offer", fileName = "Offer_Upgrade")]
    public class CanvasUpgradeOffer : ShopOffer
    {
        [Tooltip("Resolución de la pintura tras la mejora (misma proporción que el lienzo).")]
        [SerializeField] Vector2Int resolution = new(960, 768);

        public override bool IsAvailable(GameObject buyer)
        {
            foreach (var easel in FindObjectsByType<CanvasInteractable>(FindObjectsSortMode.None))
                if (easel.CanvasResolution != resolution) return true;
            return false;
        }

        public override void Deliver(GameObject buyer)
        {
            foreach (var easel in FindObjectsByType<CanvasInteractable>(FindObjectsSortMode.None))
                easel.CanvasResolution = resolution;
        }

#if UNITY_EDITOR
        public void EditorSetResolution(Vector2Int newResolution) => resolution = newResolution;
#endif
    }
}
