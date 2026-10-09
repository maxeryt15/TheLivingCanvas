using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using UnityEngine;

namespace TheLivingCanvas.Growth
{
    /// <summary>
    /// Una pintura terminada puesta plana en el suelo: la parcela de la que crece el cultivo.
    /// Con la planta adulta se cosecha (Interact): da la cosecha según la calidad y, salvo en calidad
    /// Normal, una semilla con la pintura desvanecida. La parcela se consume.
    /// </summary>
    public class PaintingPlot : MonoBehaviour, IInteractable
    {
        static readonly int BaseMap = Shader.PropertyToID("_BaseMap");

        [SerializeField] MeshRenderer paintingRenderer;
        [Tooltip("Se desactivan mientras es una vista previa, para no chocar con el jugador.")]
        [SerializeField] Collider[] colliders;

        CropPlant plant;

        public PaintingItem Painting { get; private set; }
        public string Prompt => $"Harvest {Painting.CropName.ToLowerInvariant()}";
        public bool CanInteract => plant != null && plant.IsGrown;

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
        public void StartGrowing()
        {
            var crop = Painting.Crop;
            if (crop.PlantPrefab == null) return;
            // Encima de la pintura; la flor mira hacia quien la colocó (-Z de la parcela).
            plant = Instantiate(crop.PlantPrefab, transform);
            plant.transform.localPosition = new Vector3(0f, 0.035f, 0f);
            plant.transform.localRotation = Quaternion.identity;
            plant.Grow(Painting.Result, crop.GrowthDuration);
        }

        public void Interact(PlayerInteractor interactor)
        {
            if (!CanInteract) return;
            var inventory = interactor.GetComponent<PlayerInventory>();
            inventory.Add(new CropItem(Painting.Crop, Painting.Variant, CropPlant.HarvestAmount(Painting.Result.Quality)));
            if (SeedItem.CanSeed(Painting))
                inventory.Add(new SeedItem(Painting));
            Destroy(gameObject); // la pintura se consume
        }
    }
}
