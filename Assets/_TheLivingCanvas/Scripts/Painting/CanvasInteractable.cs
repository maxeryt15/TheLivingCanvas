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

        PaintModeController paintMode;

        public Transform ViewPoint => viewPoint;
        public PaintSurface Surface => surface;
        public string Prompt => "Pintar";

        void Awake() => paintMode = FindAnyObjectByType<PaintModeController>();

        public void Interact(PlayerInteractor interactor) => paintMode.Enter(this);
    }
}
