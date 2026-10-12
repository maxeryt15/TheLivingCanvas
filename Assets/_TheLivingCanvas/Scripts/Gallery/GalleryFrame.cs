using TheLivingCanvas.Data;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Save;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Gallery
{
    /// <summary>
    /// Marco de la galería. Vacío: interactuar abre la lista de pinturas para colgar una (sale del inventario).
    /// Ocupado: interactuar la descuelga y la devuelve al inventario. Una placa muestra los datos de la pintura.
    /// </summary>
    public class GalleryFrame : MonoBehaviour, IInteractable, ISaveable
    {
        static readonly int BaseMap = Shader.PropertyToID("_BaseMap");
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");

        [SerializeField] GalleryHangUI hangUI;
        [SerializeField] PlayerInventory inventory;
        [Tooltip("Quad donde se muestra la pintura; mira hacia -Z local.")]
        [SerializeField] MeshRenderer picture;
        [Tooltip("Hueco máximo (ancho, alto) en metros; la pintura se ajusta dentro sin deformarse.")]
        [SerializeField] Vector2 maxPictureSize = new(1.4f, 1.1f);
        [SerializeField] GameObject plaque;
        [SerializeField] Text plaqueText;

        /// <summary>null = marco vacío.</summary>
        public PaintingItem Painting { get; private set; }

        public string Prompt => Painting == null ? "Hang a painting" : $"Take down {Painting.DisplayName.ToLowerInvariant()}";
        public bool CanInteract => !hangUI.IsOpen;

        void Awake() => Clear();

        public void Interact(PlayerInteractor interactor)
        {
            if (Painting == null) hangUI.Open(this);
            else TakeDown();
        }

        /// <summary>Cuelga la pintura: sale del inventario y se queda en el marco.</summary>
        public void Hang(PaintingItem painting)
        {
            if (Painting != null || !inventory.Remove(painting)) return;
            Show(painting);
        }

        void Show(PaintingItem painting)
        {
            Painting = painting;

            var image = painting.Image;
            float scale = Mathf.Min(maxPictureSize.x / image.width, maxPictureSize.y / image.height);
            picture.transform.localScale = new Vector3(image.width * scale, image.height * scale, 1f);
            picture.material.SetTexture(BaseMap, image);
            picture.material.SetColor(BaseColor, Color.white); // sin el tinte crema del lienzo vacío
            picture.gameObject.SetActive(true);

            plaqueText.text = $"{painting.CropName}\n{painting.Result.Quality} · {painting.CanvasType.DisplayName}"
                + (painting.Style != null ? $" · {painting.Style.DisplayName}" : string.Empty)
                + (painting.Mutation != Mutation.None ? $" · {painting.Mutation.Name()}" : string.Empty);
            plaque.SetActive(true);
        }

        public void WriteSave(SaveData data)
        {
            if (Painting != null) data.frames.Add(new FrameSave { id = name, painting = PaintingStore.ToSave(Painting) });
        }

        public void ReadSave(SaveData data, SaveRegistry registry)
        {
            foreach (var frame in data.frames)
            {
                if (frame.id != name) continue;
                var painting = PaintingStore.FromSave(frame.painting, registry);
                if (painting != null) Show(painting);
            }
        }

        void TakeDown()
        {
            inventory.Add(Painting);
            Clear();
        }

        void Clear()
        {
            Painting = null;
            picture.gameObject.SetActive(false);
            plaque.SetActive(false);
        }
    }
}
