using UnityEngine;

namespace TheLivingCanvas.Core
{
    /// <summary>
    /// Encoge un panel alto (ej. la paleta) lo justo para que quepa en la altura del canvas: con la interfaz
    /// agrandada (GameSettings.UiScale) no se sale de la pantalla. Nunca lo agranda.
    /// </summary>
    [RequireComponent(typeof(RectTransform))]
    public class FitToScreenHeight : MonoBehaviour
    {
        [Tooltip("Margen libre arriba y abajo, en unidades del canvas.")]
        [SerializeField] float margin = 20f;

        RectTransform rect;
        RectTransform canvasRect;

        void Awake()
        {
            rect = (RectTransform)transform;
            canvasRect = (RectTransform)GetComponentInParent<Canvas>().rootCanvas.transform;
        }

        void LateUpdate()
        {
            float available = canvasRect.rect.height - 2f * margin;
            float height = rect.rect.height;
            float scale = height > 0f ? Mathf.Min(1f, available / height) : 1f;
            if (!Mathf.Approximately(rect.localScale.x, scale)) rect.localScale = new Vector3(scale, scale, 1f);
        }
    }
}
