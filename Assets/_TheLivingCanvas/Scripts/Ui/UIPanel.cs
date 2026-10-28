using System.Collections;
using TheLivingCanvas.Audio;
using TheLivingCanvas.Core;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Player;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// Base de los paneles del jugador (sustituye a ModalPanel). Mismo contrato: al abrirse libera el cursor,
    /// para cámara e interacción; se cierra con Exit (Esc / B), Interact (E / A) o su botón Close.
    /// Los tiempos salen de UITheme y usan tiempo sin escalar (la pausa pone timeScale a 0).
    /// </summary>
    public abstract class UIPanel : MonoBehaviour
    {
        [SerializeField] protected PlayerInteractor interactor;
        [SerializeField] protected CursorLock cursorLock;
        [SerializeField] protected CameraModeController cameraMode;
        [SerializeField] InputActionReference exitAction;
        [SerializeField] protected GameObject panel;
        [SerializeField] Button closeButton;

        const float ClosedScale = 0.96f;

        int openedFrame = -1;
        CanvasGroup group;
        Coroutine fade;

        public bool IsOpen { get; private set; }

        protected virtual void Awake()
        {
            group = panel.GetComponent<CanvasGroup>();
            if (group == null) group = panel.AddComponent<CanvasGroup>();
            group.alpha = 0f;
            panel.SetActive(false);
            if (closeButton != null) closeButton.onClick.AddListener(Close);
        }

        protected virtual void OnEnable()
        {
            if (exitAction != null) exitAction.action.performed += OnCloseRequested;
            if (interactor != null) interactor.InteractAction.action.performed += OnInteractRequested;
        }

        protected virtual void OnDisable()
        {
            if (exitAction != null) exitAction.action.performed -= OnCloseRequested;
            if (interactor != null) interactor.InteractAction.action.performed -= OnInteractRequested;
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

        void StartFade(float target)
        {
            if (fade != null) StopCoroutine(fade);
            fade = StartCoroutine(Fade(target));
        }

        IEnumerator Fade(float target)
        {
            var theme = UITheme.Current;
            bool opening = target > 0f;
            group.blocksRaycasts = opening;
            float speed = 1f / Mathf.Max(0.01f, opening ? theme.panelOpen : theme.panelClose);
            var t = panel.transform;
            while (!Mathf.Approximately(group.alpha, target))
            {
                group.alpha = Mathf.MoveTowards(group.alpha, target, speed * Time.unscaledDeltaTime);
                t.localScale = Vector3.one * Mathf.Lerp(ClosedScale, 1f, group.alpha);
                yield return null;
            }
            fade = null;
            if (!opening) panel.SetActive(false);
        }

        void OnCloseRequested(InputAction.CallbackContext _)
        {
            if (Time.frameCount != openedFrame) Close();
        }

        void OnInteractRequested(InputAction.CallbackContext _)
        {
            if (Time.frameCount != openedFrame) OnInteractPressed();
        }

        protected virtual void OnInteractPressed() => Close();
    }
}
