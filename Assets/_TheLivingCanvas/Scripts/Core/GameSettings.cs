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

        /// <summary>Aplica al empezar el volumen y la pantalla guardados (la sensibilidad la aplica quien tiene la cámara).</summary>
        public static void ApplySaved()
        {
            AudioListener.volume = Volume;
            if (PlayerPrefs.HasKey(FullscreenKey)) Screen.fullScreen = Fullscreen;
        }
    }
}
