using TheLivingCanvas.Growth;
using TheLivingCanvas.Painting;
using TheLivingCanvas.Save;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace TheLivingCanvas.Core
{
    /// <summary>
    /// Menú de pausa (Esc / Start): para el tiempo y ofrece opciones mínimas, partida nueva (con confirmación) y salir.
    /// Solo se abre con el cursor bloqueado: el Esc que cierra un panel, sale de pintar o cancela una colocación no lo abre.
    /// </summary>
    public class PauseMenu : ModalPanel
    {
        const float ConfirmSeconds = 4f;
        const string NewGameText = "New game";
        const string ConfirmText = "Click again to start over";

        [SerializeField] PaintModeController paintMode;
        [SerializeField] PaintingPlacer placer;
        [SerializeField] SaveManager saveManager;
        [SerializeField] Slider sensitivitySlider;
        [SerializeField] Slider volumeSlider;
        [SerializeField] Slider uiScaleSlider;
        [SerializeField] Toggle fullscreenToggle;
        [SerializeField] Button controlsButton;
        [Tooltip("Panel con la lista de controles, encima del menú; se cierra con su botón Back.")]
        [SerializeField] GameObject controlsPanel;
        [SerializeField] Button controlsBackButton;
        [SerializeField] Button resumeButton;
        [SerializeField] Button newGameButton;
        [SerializeField] Text newGameLabel;
        [SerializeField] Button quitButton;

        bool busyLastFrame;
        float confirmUntil = -1f; // Time.unscaledTime: con la pausa timeScale vale 0

        protected override void Awake()
        {
            base.Awake();
            resumeButton.onClick.AddListener(Close);
            newGameButton.onClick.AddListener(OnNewGameClicked);
            quitButton.onClick.AddListener(Quit);
            controlsPanel.SetActive(false);
            controlsButton.onClick.AddListener(() => controlsPanel.SetActive(true));
            controlsBackButton.onClick.AddListener(() => controlsPanel.SetActive(false));

            sensitivitySlider.minValue = GameSettings.MinSensitivity;
            sensitivitySlider.maxValue = GameSettings.MaxSensitivity;
            sensitivitySlider.onValueChanged.AddListener(OnSensitivityChanged);
            volumeSlider.minValue = 0f;
            volumeSlider.maxValue = 1f;
            volumeSlider.onValueChanged.AddListener(value => GameSettings.Volume = value);
            uiScaleSlider.minValue = GameSettings.MinUiScale;
            uiScaleSlider.maxValue = GameSettings.MaxUiScale;
            uiScaleSlider.onValueChanged.AddListener(value => GameSettings.UiScale = value);
            fullscreenToggle.onValueChanged.AddListener(value => GameSettings.Fullscreen = value);
        }

        void Start()
        {
            GameSettings.ApplySaved();
            cameraMode.SetLookSensitivity(GameSettings.Sensitivity);
            sensitivitySlider.SetValueWithoutNotify(GameSettings.Sensitivity);
            volumeSlider.SetValueWithoutNotify(GameSettings.Volume);
            uiScaleSlider.SetValueWithoutNotify(GameSettings.UiScale);
            fullscreenToggle.SetIsOnWithoutNotify(GameSettings.Fullscreen);
        }

        void Update()
        {
            // El Esc que cierra algo ya lo hizo en el input de este frame; busyLastFrame lo detecta.
            bool busy = cursorLock.PointerMode || paintMode.IsPainting || placer.IsPlacing;
            if (!busy && !busyLastFrame && PausePressed()) Open();
            busyLastFrame = busy;

            if (confirmUntil >= 0f && Time.unscaledTime >= confirmUntil) ResetConfirm();
        }

        static bool PausePressed() =>
            (Keyboard.current != null && Keyboard.current.escapeKey.wasPressedThisFrame)
            || (Gamepad.current != null && Gamepad.current.startButton.wasPressedThisFrame);

        void Open()
        {
            if (!TryOpen()) return;
            Time.timeScale = 0f;
        }

        public override void Close()
        {
            if (!IsOpen) return;
            base.Close();
            controlsPanel.SetActive(false);
            Time.timeScale = 1f;
            ResetConfirm();
        }

        void OnSensitivityChanged(float value)
        {
            GameSettings.Sensitivity = value;
            cameraMode.SetLookSensitivity(value);
        }

        void OnNewGameClicked()
        {
            if (confirmUntil < 0f)
            {
                confirmUntil = Time.unscaledTime + ConfirmSeconds;
                newGameLabel.text = ConfirmText;
                return;
            }
            saveManager.StartNewGame();
        }

        void ResetConfirm()
        {
            confirmUntil = -1f;
            newGameLabel.text = NewGameText;
        }

        static void Quit()
        {
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }
    }
}
