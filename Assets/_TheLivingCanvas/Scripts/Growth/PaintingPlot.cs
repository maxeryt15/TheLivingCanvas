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

        /// <summary>La pintura ya está en el suelo: de ella crece la planta 3D de su cultivo.</summary>
        public CropPlant StartGrowing()
        {
            var crop = Painting.Crop;
            if (crop.PlantPrefab == null) return null;
            // Encima de la pintura; la flor mira hacia quien la colocó (-Z de la parcela).
            var plant = Instantiate(crop.PlantPrefab, transform);
            plant.transform.localPosition = new Vector3(0f, 0.035f, 0f);
            plant.transform.localRotation = Quaternion.identity;
            plant.Grow(Painting.Result, crop.GrowthDuration);
            return plant;
        }
    }
}
