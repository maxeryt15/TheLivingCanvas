using TheLivingCanvas.Data;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Un caballete. Vacío: interactuar elige qué cultivo pintar (si se sabe más de uno), pone un lienzo
    /// en blanco del inventario y entra en el modo pintura. En blanco o a medias: interactuar sigue pintando.
    /// Terminado: interactuar recoge la pintura al inventario y el caballete queda vacío.
    /// </summary>
    public class CanvasInteractable : MonoBehaviour, IInteractable
    {
        [Tooltip("Punto desde el que la cámara mira el lienzo de frente al pintar.")]
        [SerializeField] Transform viewPoint;
        [SerializeField] PaintSurface surface;
        [SerializeField] CanvasGuide guide;

        PaintModeController paintMode;
        CropPickerUI cropPicker;
        PlayerInventory inventory;
        MeshRenderer canvasRenderer;
        PaintingResult finishedResult;
        bool hasCanvas;

        public Transform ViewPoint => viewPoint;
        public PaintSurface Surface => surface;
        public CanvasGuide Guide => guide;
        /// <summary>Cultivo del lienzo puesto (null con el caballete vacío).</summary>
        public CropDefinition Crop { get; private set; }
        public bool IsFinished => finishedResult != null;
        public string Prompt =>
            IsFinished ? "Take painting"
            : hasCanvas ? $"Paint {Crop.DisplayName.ToLowerInvariant()}"
            : inventory != null && inventory.Count(BlankCanvasItem.Key) > 0 ? "Paint (uses 1 blank canvas)"
            : "No blank canvas - buy one at the shop";
        public bool CanInteract => true;

        void Awake()
        {
            paintMode = FindAnyObjectByType<PaintModeController>();
            cropPicker = FindAnyObjectByType<CropPickerUI>();
            inventory = FindAnyObjectByType<PlayerInventory>();
            canvasRenderer = surface.GetComponent<MeshRenderer>();
        }

        void Start() => SetHasCanvas(false);

        public void Interact(PlayerInteractor interactor)
        {
            if (IsFinished) TakePainting(interactor);
            else if (hasCanvas) paintMode.Enter(this);
            else if (interactor.GetComponent<PlayerInventory>().Count(BlankCanvasItem.Key) > 0)
            {
                var known = interactor.GetComponent<Sketchbook>().KnownCrops;
                if (known.Count == 1) StartPainting(interactor, known[0]);
                else if (known.Count > 1) cropPicker.Open(this, known);
            }
        }

        /// <summary>Pone un lienzo en blanco para <paramref name="crop"/> y entra en el modo pintura.</summary>
        public void StartPainting(PlayerInteractor interactor, CropDefinition crop)
        {
            if (hasCanvas || !interactor.GetComponent<PlayerInventory>().TryConsume(BlankCanvasItem.Key)) return;
            Crop = crop;
            guide.SetTemplate(crop.Template);
            surface.ResetToBlank();
            SetHasCanvas(true);
            // El boceto tenue se ve también desde el mundo, antes de empezar a pintar.
            ShowSketch();
            paintMode.Enter(this);
        }

        /// <summary>La pintura pasó la evaluación: queda lista para recogerla.</summary>
        public void MarkFinished(PaintingResult result)
        {
            finishedResult = result;
            guide.Show(showOutline: false, showHints: false); // sin boceto: se ve la pintura tal cual
        }

        void TakePainting(PlayerInteractor interactor)
        {
            var inventory = interactor.GetComponent<PlayerInventory>();
            inventory.Add(new PaintingItem(Crop, finishedResult, surface.CreateSnapshot()));

            // El caballete queda vacío hasta que se ponga otro lienzo.
            finishedResult = null;
            Crop = null;
            SetHasCanvas(false);
        }

        void SetHasCanvas(bool value)
        {
            hasCanvas = value;
            canvasRenderer.enabled = value;
        }

        void ShowSketch() => guide.Show(showOutline: true, showHints: false);
    }
}
