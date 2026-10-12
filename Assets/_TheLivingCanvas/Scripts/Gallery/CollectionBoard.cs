using TheLivingCanvas.Data;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Progression;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Gallery
{
    /// <summary>Tablón de la galería: muestra cuántos cultivos, variantes y mutaciones se han descubierto; interactuar abre la colección.</summary>
    public class CollectionBoard : MonoBehaviour, IInteractable
    {
        [SerializeField] CollectionUI collectionUI;
        [SerializeField] ArtistLevel artistLevel;
        [SerializeField] CropDefinition[] crops;
        [SerializeField] Text label;

        public string Prompt => "View collection";
        public bool CanInteract => !collectionUI.IsOpen;

        void OnEnable()
        {
            artistLevel.Changed += Refresh;
            Refresh();
        }

        void OnDisable() => artistLevel.Changed -= Refresh;

        public void Interact(PlayerInteractor interactor) => collectionUI.Open(artistLevel, crops);

        /// <summary>Descubiertos y total (cada cultivo cuenta uno, más una por cada una de sus variantes y por cada mutación).</summary>
        public static (int found, int total) Count(ArtistLevel artistLevel, CropDefinition[] crops)
        {
            int found = 0, total = 0;
            foreach (var crop in crops)
            {
                total++;
                if (artistLevel.IsDiscovered(crop)) found++;
                foreach (var variant in crop.Variants)
                {
                    total++;
                    if (artistLevel.IsDiscovered(crop, variant)) found++;
                }
            }
            foreach (var mutation in Mutations.All)
            {
                total++;
                if (artistLevel.IsDiscovered(mutation)) found++;
            }
            return (found, total);
        }

        void Refresh()
        {
            var (found, total) = Count(artistLevel, crops);
            label.text = $"Collection\n{found} / {total}";
        }
    }
}
