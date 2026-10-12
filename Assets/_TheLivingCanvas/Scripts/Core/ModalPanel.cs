using System.Collections;
using TheLivingCanvas.Audio;
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

        const float OpenSeconds = 0.15f;
        const float CloseSeconds = 0.12f;
        const float ClosedScale = 0.96f;

        int openedFrame = -1;
        CanvasGroup group;
        Coroutine fade;

        /// <summary>Estado lógico: pasa a false al llamar a Close, aunque el panel siga desvaneciéndose.</summary>
        public bool IsOpen { get; private set; }

        protected virtual void Awake()
        {
            group = panel.GetComponent<CanvasGroup>();
            if (group == null) group = panel.AddComponent<CanvasGroup>();
            group.alpha = 0f;
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
            IsOpen = true;
            panel.SetActive(true);
            StartFade(1f);
            interactor.enabled = false; // E cierra en lugar de interactuar
            cursorLock.PointerMode = true;
            cameraMode.SetLookInputEnabled(false);
            exitAction.action.Enable();
            SfxPlayer.Play(Sfx.UiOpen);
            return true;
        }

        public virtual void Close()
        {
            if (!IsOpen) return;
            IsOpen = false;
            StartFade(0f);
            exitAction.action.Disable();
            interactor.enabled = true;
            cursorLock.PointerMode = false;
            cameraMode.SetLookInputEnabled(true);
            SfxPlayer.Play(Sfx.UiClose);
        }

        /// <summary>Desvanece el panel hasta <paramref name="target"/> (0 o 1) con una ligera escala; usa tiempo sin escalar (la pausa pone timeScale a 0).</summary>
        void StartFade(float target)
        {
            if (fade != null) StopCoroutine(fade);
            fade = StartCoroutine(Fade(target));
        }

        IEnumerator Fade(float target)
        {
            bool opening = target > 0f;
            group.blocksRaycasts = opening; // un panel que se cierra ya no recibe clics
            float speed = 1f / (opening ? OpenSeconds : CloseSeconds);
            var panelTransform = panel.transform;
            while (!Mathf.Approximately(group.alpha, target))
            {
                group.alpha = Mathf.MoveTowards(group.alpha, target, speed * Time.unscaledDeltaTime);
                panelTransform.localScale = Vector3.one * Mathf.Lerp(ClosedScale, 1f, group.alpha);
                yield return null;
            }
            fade = null;
            if (!opening) panel.SetActive(false);
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
