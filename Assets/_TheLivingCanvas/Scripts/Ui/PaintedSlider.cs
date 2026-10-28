using TheLivingCanvas.Core;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// Slider pintado: el mango es un pincel cuya punta marca el valor y la barra es pintura que se extiende al subir
    /// y se borra al bajar. La pintura sigue a la punta con un pequeño retraso (capa trasera más lenta = pintura húmeda).
    /// Con Reduced Motion todo sigue el valor al instante y el pincel no se inclina.
    /// </summary>
    [RequireComponent(typeof(Slider))]
    public class PaintedSlider : MonoBehaviour
    {
        public Image fillFront, fillBack, fillHighlight;
        public RectTransform handle;
        public float baseTilt = -26f;

        Slider slider;
        float shown, trail, tilt;

        void Awake() { slider = GetComponent<Slider>(); }

        void OnEnable() { Snap(); }

        /// <summary>Coloca pintura y pincel al instante en el valor actual (sin animar).</summary>
        public void Snap()
        {
            if (slider == null) slider = GetComponent<Slider>();
            shown = trail = slider.normalizedValue;
            tilt = GameSettings.ReducedMotion ? 0f : baseTilt;
            Apply();
        }

        void LateUpdate()
        {
            float target = slider.normalizedValue;
            float dt = Time.unscaledDeltaTime;
            if (GameSettings.ReducedMotion)
            {
                shown = trail = target;
                tilt = 0f;
            }
            else
            {
                float prev = shown;
                shown = Mathf.Lerp(shown, target, 1f - Mathf.Exp(-16f * dt));
                trail = Mathf.Lerp(trail, target, 1f - Mathf.Exp(-6f * dt));
                float vel = dt > 1e-5f ? (shown - prev) / dt : 0f;
                // Al pintar (subir) el mango se echa hacia atrás; al borrar (bajar) se inclina al otro lado.
                float want = baseTilt - Mathf.Clamp(vel * 22f, -16f, 16f);
                tilt = Mathf.Lerp(tilt, want, 1f - Mathf.Exp(-12f * dt));
            }
            Apply();
        }

        void Apply()
        {
            if (fillFront != null) fillFront.fillAmount = shown;
            if (fillHighlight != null) fillHighlight.fillAmount = Mathf.Max(0f, shown - .02f);
            if (fillBack != null) fillBack.fillAmount = Mathf.Max(trail, shown);
            if (handle != null)
            {
                handle.anchorMin = new Vector2(shown, handle.anchorMin.y);
                handle.anchorMax = new Vector2(shown, handle.anchorMax.y);
                handle.anchoredPosition = Vector2.zero;
                handle.localRotation = Quaternion.Euler(0f, 0f, tilt);
            }
        }
    }
}
