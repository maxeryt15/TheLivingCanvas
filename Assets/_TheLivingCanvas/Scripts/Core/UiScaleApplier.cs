using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Core
{
    /// <summary>
    /// Aplica GameSettings.UiScale a un CanvasScaler de pantalla: divide su resolución de referencia original
    /// entre la escala (más escala = interfaz más grande). Los canvas en el mundo no llevan este componente.
    /// </summary>
    [RequireComponent(typeof(CanvasScaler))]
    public class UiScaleApplier : MonoBehaviour
    {
        CanvasScaler scaler;
        Vector2 baseResolution;

        void Awake()
        {
            scaler = GetComponent<CanvasScaler>();
            baseResolution = scaler.referenceResolution;
            Apply();
            GameSettings.UiScaleChanged += Apply;
        }

        void OnDestroy() => GameSettings.UiScaleChanged -= Apply;

        void Apply() => scaler.referenceResolution = baseResolution / GameSettings.UiScale;
    }
}
