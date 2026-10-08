using TheLivingCanvas.Data;
using TheLivingCanvas.Interaction;
using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Un caballete con lienzo: al interactuar entra en el modo pintura.
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

        public Transform ViewPoint => viewPoint;
        public PaintSurface Surface => surface;
        public CanvasGuide Guide => guide;
        public CropDefinition Crop => crop;
        public string Prompt => "Paint";

        void Awake() => paintMode = FindAnyObjectByType<PaintModeController>();

        void Start()
        {
            // El boceto tenue se ve también desde el mundo, antes de empezar a pintar.
            guide.SetTemplate(crop != null ? crop.Template : null);
            guide.Show(showOutline: true, showHints: false);
        }

        public void Interact(PlayerInteractor interactor) => paintMode.Enter(this);
    }
}
