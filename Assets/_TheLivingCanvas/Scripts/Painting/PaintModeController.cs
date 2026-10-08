using TheLivingCanvas.Core;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Player;
using UnityEngine;
using UnityEngine.InputSystem;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Entra y sale del modo pintura: cámara fija frente al lienzo, cursor libre y jugador quieto.
    /// Se sale con Paint/Exit (Esc / B) o pulsando Interact otra vez.
    /// </summary>
    public class PaintModeController : MonoBehaviour
    {
        [SerializeField] CameraModeController cameraMode;
        [SerializeField] PlayerInteractor interactor;
        [SerializeField] CursorLock cursorLock;
        [SerializeField] InputActionReference exitAction;
        [Tooltip("UI que solo se ve mientras se pinta.")]
        [SerializeField] GameObject paintHud;

        // La misma pulsación de E que entra (o sale) no debe disparar la acción contraria.
        int lastToggleFrame = -1;

        public CanvasInteractable ActiveCanvas { get; private set; }
        public bool IsPainting => ActiveCanvas != null;

        void OnEnable()
        {
            exitAction.action.performed += OnExitRequested;
            interactor.InteractAction.action.performed += OnExitRequested;
        }

        void OnDisable()
        {
            exitAction.action.performed -= OnExitRequested;
            interactor.InteractAction.action.performed -= OnExitRequested;
        }

        void Start() => paintHud.SetActive(false);

        public void Enter(CanvasInteractable canvas)
        {
            if (IsPainting || Time.frameCount == lastToggleFrame) return;
            ActiveCanvas = canvas;
            lastToggleFrame = Time.frameCount;

            cameraMode.EnterFixedView(canvas.ViewPoint);
            interactor.enabled = false;
            cursorLock.PointerMode = true;
            exitAction.action.Enable();
            paintHud.SetActive(true);
        }

        public void Exit()
        {
            if (!IsPainting || Time.frameCount == lastToggleFrame) return;
            ActiveCanvas = null;
            lastToggleFrame = Time.frameCount;

            exitAction.action.Disable();
            cameraMode.ExitFixedView();
            interactor.enabled = true;
            cursorLock.PointerMode = false;
            paintHud.SetActive(false);
        }

        void OnExitRequested(InputAction.CallbackContext _) => Exit();
    }
}
