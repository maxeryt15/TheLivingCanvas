using TheLivingCanvas.Interaction;
using TheLivingCanvas.Player;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace TheLivingCanvas.Core
{
    /// <summary>
    /// Base de los paneles que piden el cursor (tienda, selector de cultivo): al abrirse liberan el cursor,
    /// paran la cámara y la interacción; se cierran con el botón Close, Exit (Esc / B) o Interact (E / A).
    /// </summary>
    public abstract class ModalPanel : MonoBehaviour
    {
        [SerializeField] protected PlayerInteractor interactor;
        [SerializeField] protected CursorLock cursorLock;
        [SerializeField] protected CameraModeController cameraMode;
        [SerializeField] InputActionReference exitAction;
        [SerializeField] protected GameObject panel;
        [SerializeField] Button closeButton;

        int openedFrame = -1;

        public bool IsOpen => panel.activeSelf;

        protected virtual void Awake()
        {
            panel.SetActive(false);
            closeButton.onClick.AddListener(Close);
        }

        protected virtual void OnEnable()
        {
            exitAction.action.performed += OnCloseRequested;
            interactor.InteractAction.action.performed += OnInteractRequested;
        }

        protected virtual void OnDisable()
        {
            exitAction.action.performed -= OnCloseRequested;
            interactor.InteractAction.action.performed -= OnInteractRequested;
        }

        /// <summary>Muestra el panel; false si ya estaba abierto u otro panel tiene el cursor.</summary>
        protected bool TryOpen()
        {
            if (IsOpen || cursorLock.PointerMode) return false;
            openedFrame = Time.frameCount;
            panel.SetActive(true);
            interactor.enabled = false; // E cierra en lugar de interactuar
            cursorLock.PointerMode = true;
            cameraMode.SetLookInputEnabled(false);
            exitAction.action.Enable();
            return true;
        }

        public virtual void Close()
        {
            if (!IsOpen) return;
            panel.SetActive(false);
            exitAction.action.Disable();
            interactor.enabled = true;
            cursorLock.PointerMode = false;
            cameraMode.SetLookInputEnabled(true);
        }

        void OnCloseRequested(InputAction.CallbackContext _)
        {
            // La misma pulsación de E que abre no debe cerrar.
            if (Time.frameCount != openedFrame) Close();
        }

        void OnInteractRequested(InputAction.CallbackContext _)
        {
            if (Time.frameCount != openedFrame) OnInteractPressed();
        }

        /// <summary>Se pulsó Interact (E / A) con el panel abierto; por defecto cierra.</summary>
        protected virtual void OnInteractPressed() => Close();
    }
}
