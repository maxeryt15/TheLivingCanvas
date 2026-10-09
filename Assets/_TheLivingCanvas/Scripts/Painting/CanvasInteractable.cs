using TheLivingCanvas.Data;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Un caballete. Vacío: interactuar pone un lienzo en blanco del inventario y entra en el modo pintura.
    /// En blanco o a medias: interactuar sigue pintando.
    /// Terminado: interactuar recoge la pintura al inventario y el caballete queda vacío.
    /// </summary>
    public class CanvasInteractable : MonoBehaviour, IInteractable
    {
        [Tooltip("Punto desde el que la cámara mira el lienzo de frente al pintar.")]
        [SerializeField] Transform viewPoint;
        [SerializeField] PaintSurface surface;
        [SerializeField] CanvasGuide guide;
        [Tooltip("Cultivo que se pinta en este lienzo (vertical slice: siempre el girasol).")]
        [SerializeField] CropDefinition crop;

        PaintModeController paintMode;
        PlayerInventory inventory;
        MeshRenderer canvasRenderer;
        PaintingResult finishedResult;
        bool hasCanvas;

        public Transform ViewPoint => viewPoint;
        public PaintSurface Surface => surface;
        public CanvasGuide Guide => guide;
        public CropDefinition Crop => crop;
        public bool IsFinished => finishedResult != null;
        public string Prompt =>
            IsFinished ? "Take painting"
            : hasCanvas ? "Paint"
            : inventory != null && inventory.Count(BlankCanvasItem.Key) > 0 ? "Paint (uses 1 blank canvas)"
            : "No blank canvas - buy one at the shop";
        public bool CanInteract => true;

        void Awake()
        {
            paintMode = FindAnyObjectByType<PaintModeController>();
            inventory = FindAnyObjectByType<PlayerInventory>();
            canvasRenderer = surface.GetComponent<MeshRenderer>();
        }

        void Start()
        {
            guide.SetTemplate(crop != null ? crop.Template : null);
            SetHasCanvas(false);
        }

        public void Interact(PlayerInteractor interactor)
        {
            if (IsFinished) TakePainting(interactor);
            else if (hasCanvas) paintMode.Enter(this);
            else if (interactor.GetComponent<PlayerInventory>().TryConsume(BlankCanvasItem.Key))
            {
                surface.ResetToBlank();
                SetHasCanvas(true);
                // El boceto tenue se ve también desde el mundo, antes de empezar a pintar.
                ShowSketch();
                paintMode.Enter(this);
            }
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
            inventory.Add(new PaintingItem(crop, finishedResult, surface.CreateSnapshot()));

            // El caballete queda vacío hasta que se ponga otro lienzo.
            finishedResult = null;
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
