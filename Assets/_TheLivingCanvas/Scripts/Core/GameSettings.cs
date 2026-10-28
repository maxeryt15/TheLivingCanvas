using System;
using UnityEngine;

namespace TheLivingCanvas.Core
{
    /// <summary>Opciones del jugador en PlayerPrefs (aparte de la partida): al cambiarlas se aplican al momento.</summary>
    public static class GameSettings
    {
        const string SensitivityKey = "settings.sensitivity";
        const string VolumeKey = "settings.volume";
        const string FullscreenKey = "settings.fullscreen";
        const string UiScaleKey = "settings.uiScale";

        public const float MinSensitivity = 0.25f;
        public const float MaxSensitivity = 3f;
        public const float MinUiScale = 0.8f;
        public const float MaxUiScale = 1.5f;

        /// <summary>Se dispara al cambiar el tamaño de la interfaz (lo aplica UiScaleApplier).</summary>
        public static event Action UiScaleChanged;

        /// <summary>Multiplicador de la sensibilidad de la mirada.</summary>
        public static float Sensitivity
        {
            get => Mathf.Clamp(PlayerPrefs.GetFloat(SensitivityKey, 1f), MinSensitivity, MaxSensitivity);
            set => PlayerPrefs.SetFloat(SensitivityKey, value);
        }

        public static float Volume
        {
            get => Mathf.Clamp01(PlayerPrefs.GetFloat(VolumeKey, 1f));
            set
            {
                PlayerPrefs.SetFloat(VolumeKey, value);
                AudioListener.volume = value;
            }
        }

        /// <summary>Volumen de la música, multiplicado por el volumen general.</summary>
        public static float MusicVolume
        {
            get => Mathf.Clamp01(PlayerPrefs.GetFloat("settings.music", 1f));
            set { PlayerPrefs.SetFloat("settings.music", value); AudioChanged?.Invoke(); }
        }

        /// <summary>Volumen de los efectos de sonido (y de la interfaz), multiplicado por el volumen general.</summary>
        public static float SfxVolume
        {
            get => Mathf.Clamp01(PlayerPrefs.GetFloat("settings.sfx", 1f));
            set { PlayerPrefs.SetFloat("settings.sfx", value); AudioChanged?.Invoke(); }
        }

        /// <summary>Se dispara al cambiar el volumen de música o efectos.</summary>
        public static event Action AudioChanged;

        /// <summary>Se dispara al cambiar una opción de mirada (invertir eje Y).</summary>
        public static event Action LookChanged;

        public static bool InvertY
        {
            get => PlayerPrefs.GetInt("settings.invertY", 0) == 1;
            set { PlayerPrefs.SetInt("settings.invertY", value ? 1 : 0); LookChanged?.Invoke(); }
        }

        public static bool VSync
        {
            get => PlayerPrefs.GetInt("settings.vsync", QualitySettings.vSyncCount > 0 ? 1 : 0) == 1;
            set { PlayerPrefs.SetInt("settings.vsync", value ? 1 : 0); QualitySettings.vSyncCount = value ? 1 : 0; }
        }

        /// <summary>Índice de QualitySettings (Low/Medium/High...).</summary>
        public static int Quality
        {
            get => Mathf.Clamp(PlayerPrefs.GetInt("settings.quality", QualitySettings.GetQualityLevel()), 0, QualitySettings.names.Length - 1);
            set { PlayerPrefs.SetInt("settings.quality", value); QualitySettings.SetQualityLevel(value, true); }
        }

        /// <summary>Resolución guardada como "ancho x alto"; vacía = la actual del sistema.</summary>
        public static Vector2Int ResolutionSaved
        {
            get => new Vector2Int(PlayerPrefs.GetInt("settings.resW", Screen.width), PlayerPrefs.GetInt("settings.resH", Screen.height));
        }

        public static void SetResolution(int width, int height)
        {
            PlayerPrefs.SetInt("settings.resW", width);
            PlayerPrefs.SetInt("settings.resH", height);
            Screen.SetResolution(width, height, Fullscreen ? FullScreenMode.FullScreenWindow : FullScreenMode.Windowed);
        }

        public static bool Fullscreen
        {
            get => PlayerPrefs.GetInt(FullscreenKey, Screen.fullScreen ? 1 : 0) == 1;
            set
            {
                PlayerPrefs.SetInt(FullscreenKey, value ? 1 : 0);
                Screen.fullScreen = value;
            }
        }

        /// <summary>Tamaño de la interfaz: 1 es el original, mayor agranda los canvas de pantalla.</summary>
        public static float UiScale
        {
            get => Mathf.Clamp(PlayerPrefs.GetFloat(UiScaleKey, 1f), MinUiScale, MaxUiScale);
            set
            {
                PlayerPrefs.SetFloat(UiScaleKey, value);
                UiScaleChanged?.Invoke();
            }
        }

        /// <summary>Reduce el movimiento de la interfaz: las animaciones se limitan a un fundido corto.</summary>
        public static bool ReducedMotion
        {
            get => PlayerPrefs.GetInt("settings.reducedMotion", 0) == 1;
            set => PlayerPrefs.SetInt("settings.reducedMotion", value ? 1 : 0);
        }

        /// <summary>Muestra subtítulos de las líneas sueltas (los diálogos con caja se muestran siempre).</summary>
        public static bool Subtitles
        {
            get => PlayerPrefs.GetInt("settings.subtitles", 1) == 1;
            set => PlayerPrefs.SetInt("settings.subtitles", value ? 1 : 0);
        }

        /// <summary>Texto de interfaz más grande y con contraste máximo (negro/blanco) donde la paleta pintada lo debilita.</summary>
        public static bool HighContrastText
        {
            get => PlayerPrefs.GetInt("settings.highContrastText", 0) == 1;
            set => PlayerPrefs.SetInt("settings.highContrastText", value ? 1 : 0);
        }

        /// <summary>Aplica al empezar el volumen y la pantalla guardados (la sensibilidad la aplica quien tiene la cámara).</summary>
        public static void ApplySaved()
        {
            AudioListener.volume = Volume;
            if (PlayerPrefs.HasKey("settings.quality")) QualitySettings.SetQualityLevel(Quality, true);
            if (PlayerPrefs.HasKey("settings.vsync")) QualitySettings.vSyncCount = VSync ? 1 : 0;
#if !UNITY_EDITOR
            if (PlayerPrefs.HasKey("settings.resW")) SetResolution(ResolutionSaved.x, ResolutionSaved.y);
            else
#endif
            if (PlayerPrefs.HasKey(FullscreenKey)) Screen.fullScreen = Fullscreen;
        }
    }
}
