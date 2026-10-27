using System.Collections;
using TheLivingCanvas.Core;
using TheLivingCanvas.Growth;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Painting;
using TheLivingCanvas.Player;
using TheLivingCanvas.Save;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.UI;
using UnityEngine.UI;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// Pausa del museo (Esc / Start): para el tiempo, libera el cursor y ofrece Resume, Settings, Main Menu y Quit.
    /// Se construye por código (como el HUD) y usa el panel de ajustes compartido. Solo se abre con el cursor bloqueado:
    /// el Esc que cierra otro panel, sale de pintar o cancela una colocación no la abre.
    /// </summary>
    public class PauseScreen : MonoBehaviour
    {
        const float FadeSeconds = 0.18f, ConfirmSeconds = 4f;
        const string LeaveText = "Main Menu", LeaveConfirm = "Click again to leave";

        CursorLock cursorLock;
        CameraModeController cameraMode;
        PlayerInteractor interactor;
        PaintModeController paintMode;
        PaintingPlacer placer;
        SaveManager saveManager;

        CanvasGroup group;
        GameObject menuGroup;
        SettingsPanel settings;
        Button resumeButton, leaveButton;
        TextMeshProUGUI leaveLabel;
        Coroutine fade;
        bool isOpen, busyLastFrame;
        int openedFrame = -1;
        float confirmUntil = -1f;

        public bool IsOpen => isOpen;

        void Awake() => Build();

        void Start()
        {
            cursorLock = FindAnyObjectByType<CursorLock>();
            cameraMode = FindAnyObjectByType<CameraModeController>();
            interactor = FindAnyObjectByType<PlayerInteractor>();
            paintMode = FindAnyObjectByType<PaintModeController>();
            placer = FindAnyObjectByType<PaintingPlacer>();
            saveManager = FindAnyObjectByType<SaveManager>();
            GameSettings.ApplySaved();
            if (cameraMode != null) cameraMode.SetLookSensitivity(GameSettings.Sensitivity);
            if (cursorLock == null || interactor == null)
                Debug.LogWarning("PauseScreen: faltan CursorLock o PlayerInteractor en la escena; la pausa no se abrirá.");
        }

        void Update()
        {
            if (cursorLock == null || interactor == null) return;
            bool busy = cursorLock.PointerMode || (paintMode != null && paintMode.IsPainting) || (placer != null && placer.IsPlacing)
                || (DialogueBox.Instance != null && DialogueBox.Instance.IsOpen) || DialogueBox.ClosedFrame == Time.frameCount
                || JournalScreen.ClosedFrame == Time.frameCount;
            bool pressed = PausePressed();

            if (isOpen)
            {
                if (pressed && Time.frameCount != openedFrame) OnBack();
            }
            else if (!busy && !busyLastFrame && pressed && !SceneLoader.IsLoading && !ScreenTransition.IsCovered) Open();
            busyLastFrame = busy;

            if (confirmUntil >= 0f && Time.unscaledTime >= confirmUntil) ResetConfirm();
        }

        static bool PausePressed() =>
            (Keyboard.current != null && Keyboard.current.escapeKey.wasPressedThisFrame)
            || (Gamepad.current != null && (Gamepad.current.startButton.wasPressedThisFrame || Gamepad.current.buttonEast.wasPressedThisFrame));

        // ---------- Abrir / cerrar ----------

        void Open()
        {
            EnsureEventSystem();
            isOpen = true;
            openedFrame = Time.frameCount;
            Time.timeScale = 0f;
            interactor.enabled = false;
            cursorLock.PointerMode = true;
            if (cameraMode != null) cameraMode.SetLookInputEnabled(false);
            settings.Root.SetActive(false);
            menuGroup.SetActive(true);
            group.gameObject.SetActive(true);
            group.blocksRaycasts = true;
            StartFade(1f);
            UIEvents.Play(UISound.OpenMenu);
            if (EventSystem.current != null) EventSystem.current.SetSelectedGameObject(resumeButton.gameObject);
        }

        void Resume()
        {
            if (!isOpen) return;
            isOpen = false;
            Time.timeScale = 1f;
            interactor.enabled = true;
            cursorLock.PointerMode = false;
            if (cameraMode != null) cameraMode.SetLookInputEnabled(true);
            group.blocksRaycasts = false;
            ResetConfirm();
            PlayerPrefs.Save();
            StartFade(0f);
            UIEvents.Play(UISound.CloseMenu);
        }

        void OnBack()
        {
            if (settings.Root.activeSelf) CloseSettings();
            else Resume();
        }

        void OpenSettings()
        {
            menuGroup.SetActive(false);
            settings.Root.SetActive(true);
            if (EventSystem.current != null) EventSystem.current.SetSelectedGameObject(settings.First.gameObject);
        }

        void CloseSettings()
        {
            PlayerPrefs.Save();
            settings.Root.SetActive(false);
            menuGroup.SetActive(true);
            if (EventSystem.current != null) EventSystem.current.SetSelectedGameObject(resumeButton.gameObject);
        }

        void OnLeaveClicked()
        {
            if (confirmUntil < 0f)
            {
                confirmUntil = Time.unscaledTime + ConfirmSeconds;
                leaveLabel.text = LeaveConfirm;
                return;
            }
            if (saveManager != null) saveManager.Save(); // no se pierde lo hecho al volver al menú
            Resume();
            SceneLoader.Load(SceneLoader.MenuScene);
        }

        void ResetConfirm()
        {
            confirmUntil = -1f;
            if (leaveLabel != null) leaveLabel.text = LeaveText;
        }

        static void Quit()
        {
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }

        internal static void EnsureEventSystem()
        {
            if (EventSystem.current != null) return;
            var go = new GameObject("EventSystem", typeof(EventSystem), typeof(InputSystemUIInputModule));
            DontDestroyOnLoad(go);
        }

        void StartFade(float target)
        {
            if (fade != null) StopCoroutine(fade);
            fade = StartCoroutine(FadeRoutine(target));
        }

        IEnumerator FadeRoutine(float target)
        {
            float seconds = GameSettings.ReducedMotion ? 0.06f : FadeSeconds;
            while (!Mathf.Approximately(group.alpha, target))
            {
                group.alpha = Mathf.MoveTowards(group.alpha, target, Time.unscaledDeltaTime / seconds);
                yield return null;
            }
            if (target <= 0f) group.gameObject.SetActive(false);
            fade = null;
        }

        // ---------- Construcción ----------

        void Build()
        {
            var t = UITheme.Current;
            var canvas = UIFactory.Canvas("PauseCanvas", 500);
            canvas.transform.SetParent(transform, false);
            group = canvas.gameObject.AddComponent<CanvasGroup>();
            group.alpha = 0f;

            // Velo oscuro (sin rectángulo de menú: el mundo sigue viéndose detrás)
            var dim = UIFactory.Rect("Dim", canvas.transform);
            UIFactory.Stretch(dim);
            var dimImg = dim.gameObject.AddComponent<Image>();
            dimImg.color = new Color(t.ink.r * .6f, t.ink.g * .6f, t.ink.b * .7f, .72f);
            dimImg.raycastTarget = true;

            menuGroup = UIFactory.Rect("Menu", canvas.transform).gameObject;
            UIFactory.Stretch((RectTransform)menuGroup.transform);
            var title = UIFactory.Label("Title", menuGroup.transform, "Paused", UIFactory.TextStyle.Title);
            UIFactory.Place(title.rectTransform, new Vector2(.5f, .5f), new Vector2(.5f, .5f), new Vector2(0, 230), new Vector2(900, 130));

            resumeButton = MenuButton("Resume", 100, Resume);
            MenuButton("Settings", 10, OpenSettings);
            leaveButton = MenuButton(LeaveText, -80, OnLeaveClicked);
            leaveLabel = leaveButton.GetComponentInChildren<TextMeshProUGUI>();
            MenuButton("Quit", -170, Quit);

            settings = SettingsPanel.Create(canvas.transform, CloseSettings, v => { if (cameraMode != null) cameraMode.SetLookSensitivity(v); });
            canvas.gameObject.SetActive(false);
            group.gameObject.SetActive(false);
        }

        Button MenuButton(string label, float y, UnityEngine.Events.UnityAction onClick)
        {
            var b = UIFactory.Button(label + "Button", menuGroup.transform, label, new Vector2(420, 72));
            UIFactory.Place((RectTransform)b.transform, new Vector2(.5f, .5f), new Vector2(.5f, .5f), new Vector2(0, y), new Vector2(420, 72));
            b.onClick.AddListener(onClick);
            return b;
        }
    }
}
