using TheLivingCanvas.Inventory;
using UnityEngine;

namespace TheLivingCanvas.Growth
{
    /// <summary>
    /// Una pintura terminada puesta plana en el suelo: es la parcela de la que crecerá el cultivo (G2).
    /// </summary>
    public class PaintingPlot : MonoBehaviour
    {
        static readonly int BaseMap = Shader.PropertyToID("_BaseMap");

        [SerializeField] MeshRenderer paintingRenderer;
        [Tooltip("Se desactivan mientras es una vista previa, para no chocar con el jugador.")]
        [SerializeField] Collider[] colliders;

        public PaintingItem Painting { get; private set; }

        public void Show(PaintingItem painting)
        {
            Painting = painting;
            paintingRenderer.material.SetTexture(BaseMap, painting.Image);
        }

        public void SetPreview(bool preview)
        {
            foreach (var c in colliders)
                c.enabled = !preview;
        }
    }
}
