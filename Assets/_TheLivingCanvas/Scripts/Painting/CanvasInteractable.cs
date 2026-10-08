using TheLivingCanvas.Data;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Un caballete con lienzo. En blanco o a medias: interactuar entra en el modo pintura.
    /// Terminado: interactuar recoge la pintura al inventario y deja un lienzo nuevo en blanco.
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
        PaintingResult finishedResult;

        public Transform ViewPoint => viewPoint;
        public PaintSurface Surface => surface;
        public CanvasGuide Guide => guide;
        public CropDefinition Crop => crop;
        public bool IsFinished => finishedResult != null;
        public string Prompt => IsFinished ? "Take painting" : "Paint";
        public bool CanInteract => true;

        void Awake() => paintMode = FindAnyObjectByType<PaintModeController>();

        void Start()
        {
            // El boceto tenue se ve también desde el mundo, antes de empezar a pintar.
            guide.SetTemplate(crop != null ? crop.Template : null);
            ShowSketch();
        }

        public void Interact(PlayerInteractor interactor)
        {
            if (IsFinished) TakePainting(interactor);
            else paintMode.Enter(this);
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

            // Lienzo nuevo en el caballete.
            finishedResult = null;
            surface.ResetToBlank();
            ShowSketch();
        }

        void ShowSketch() => guide.Show(showOutline: true, showHints: false);
    }
}
