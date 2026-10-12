using System.Collections;
using TheLivingCanvas.Data;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Seasons;
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
        SeasonClock seasons;

        public PaintingItem Painting { get; private set; }
        public string Prompt => InSeason
            ? $"Harvest {Painting.CropName.ToLowerInvariant()} (in season +{CropDefinition.InSeasonBonus})"
            : $"Harvest {Painting.CropName.ToLowerInvariant()}";
        bool InSeason => Painting.Crop.IsInSeason(seasons.Current);
        public bool CanInteract => plant != null && plant.IsGrown;

        public void Show(PaintingItem painting, SeasonClock seasonClock)
        {
            Painting = painting;
            seasons = seasonClock;
            transform.localScale = Vector3.one * painting.CanvasType.PlotScale; // la planta, hija de la parcela, crece con ella
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
            plant.Grow(Painting.Result, crop.GrowthDuration * (Painting.Style != null ? Painting.Style.GrowthMultiplier : 1f));
            if (Painting.Style != null && Painting.Style.Kind == StyleKind.Swirl)
                StartCoroutine(Swirl(plant));
        }

        /// <summary>Remolino: ya crecida, la planta gira despacio sobre Y y su inclinación precesa en una espiral suave.</summary>
        IEnumerator Swirl(CropPlant swirling)
        {
            const float yawDegreesPerSecond = 10f;
            const float tiltDegrees = 3f;
            const float tiltRadiansPerSecond = 0.8f;
            while (swirling != null && !swirling.IsGrown) yield return null;
            float time = 0f;
            while (swirling != null)
            {
                time += Time.deltaTime;
                float phase = time * tiltRadiansPerSecond;
                swirling.transform.localRotation = Quaternion.Euler(tiltDegrees * Mathf.Sin(phase), 0f, tiltDegrees * Mathf.Cos(phase))
                    * Quaternion.Euler(0f, time * yawDegreesPerSecond, 0f);
                yield return null;
            }
        }

        public void Interact(PlayerInteractor interactor)
        {
            if (!CanInteract) return;
            var inventory = interactor.GetComponent<PlayerInventory>();
            int amount = CropPlant.HarvestAmount(Painting.Result.Quality) * Painting.CanvasType.HarvestMultiplier;
            if (InSeason) amount += CropDefinition.InSeasonBonus;
            inventory.Add(new CropItem(Painting.Crop, Painting.Variant, amount));
            if (SeedItem.CanSeed(Painting))
                inventory.Add(new SeedItem(Painting));
            Destroy(gameObject); // la pintura se consume
        }
    }
}
