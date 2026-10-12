using System.Collections;
using TheLivingCanvas.Data;
using TheLivingCanvas.Economy;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Progression;
using TheLivingCanvas.Seasons;
using UnityEngine;

namespace TheLivingCanvas.Growth
{
    /// <summary>
    /// Una pintura terminada puesta plana en el suelo: la parcela de la que crece el cultivo.
    /// Con la planta adulta se cosecha (Interact): da la cosecha según la calidad (y la mutación, si la hay) y, salvo en calidad
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
        Mutation mutation;

        public PaintingItem Painting { get; private set; }
        string HarvestName => (mutation != Mutation.None ? $"{mutation.Name().ToLowerInvariant()} " : string.Empty) + Painting.CropName.ToLowerInvariant();
        public string Prompt => InSeason
            ? $"Harvest {HarvestName} (in season +{CropDefinition.InSeasonBonus})"
            : $"Harvest {HarvestName}";
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
            // Una pintura que ya trae mutación (semilla) la conserva; si no, se tira el dado.
            mutation = Painting.Mutation != Mutation.None ? Painting.Mutation : Mutations.Roll(Painting.Result.Quality);
            // Twin: dos plantas, a los lados; si no, una en el centro.
            plant = SpawnPlant(mutation == Mutation.Twin ? -TwinOffset : 0f);
            if (mutation == Mutation.Twin) SpawnPlant(TwinOffset);
        }

        const float TwinOffset = 0.18f;
        const float GiantScale = 1.4f;

        /// <summary>Encima de la pintura, desplazada en X local; la flor mira hacia quien la colocó (-Z de la parcela).</summary>
        CropPlant SpawnPlant(float offsetX)
        {
            var spawned = Instantiate(Painting.Crop.PlantPrefab, transform);
            spawned.transform.localPosition = new Vector3(offsetX, 0.035f, 0f);
            spawned.transform.localRotation = Quaternion.identity;
            if (mutation == Mutation.Giant) spawned.transform.localScale = Vector3.one * GiantScale;
            spawned.Grow(Painting.Result, Painting.Crop.GrowthDuration * (Painting.Style != null ? Painting.Style.GrowthMultiplier : 1f));
            if (Painting.Style != null && Painting.Style.Kind == StyleKind.Swirl)
                StartCoroutine(Swirl(spawned));
            if (mutation == Mutation.Luminous)
                StartCoroutine(Glow(spawned));
            return spawned;
        }

        /// <summary>Luminosa: ya crecida (Tint y Apply ya no tocan el color) brilla con su propio color y suma una luz suave.</summary>
        IEnumerator Glow(CropPlant glowing)
        {
            const float emission = 0.6f;
            while (glowing != null && !glowing.IsGrown) yield return null;
            if (glowing == null) yield break;
            var sum = Color.black;
            var renderers = glowing.GetComponentsInChildren<MeshRenderer>();
            foreach (var r in renderers)
            {
                var material = r.material;
                if (material.IsKeywordEnabled("_EMISSION")) continue; // ya brilla por su cuenta (campanillas del glowbell)
                material.EnableKeyword("_EMISSION");
                material.SetColor("_EmissionColor", material.color * emission);
                sum += material.color;
            }
            var lightObject = new GameObject("MutationLight");
            lightObject.transform.SetParent(glowing.transform, false);
            lightObject.transform.localPosition = Vector3.up * 0.3f;
            var light = lightObject.AddComponent<Light>();
            light.type = LightType.Point;
            light.color = Color.Lerp(sum / Mathf.Max(1, renderers.Length), Color.white, 0.5f);
            light.intensity = 0.8f;
            light.range = 1.5f;
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
            if (mutation == Mutation.Giant) amount += 1;
            else if (mutation == Mutation.Twin) amount *= 2;
            var harvest = new CropItem(Painting.Crop, Painting.Variant, amount);
            inventory.Add(harvest);
            if (mutation == Mutation.Luminous)
                interactor.GetComponent<Wallet>().Add(harvest.UnitPrice * amount); // la cosecha vale el doble
            if (mutation != Mutation.None)
                interactor.GetComponent<ArtistLevel>().DiscoverMutation(mutation);
            if (SeedItem.CanSeed(Painting))
                inventory.Add(new SeedItem(Painting, mutation));
            Destroy(gameObject); // la pintura se consume
        }
    }
}
