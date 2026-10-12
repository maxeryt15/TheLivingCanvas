using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Pincel en mano (solo en primera persona, mientras se pinta): su punta toca el lienzo donde está el cursor y el mango
    /// apunta hacia la cámara, abajo a la derecha. Se inclina un poco según la velocidad del cursor y se levanta unos milímetros
    /// al no pintar. Va en coordenadas de mundo; la punta toma el color del pigmento (gris con el borrador).
    /// </summary>
    public class HeldBrush : MonoBehaviour
    {
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");

        [SerializeField] PaintBrushController brush;
        [Tooltip("Hijo con las mallas del pincel (con la punta en el origen y el mango hacia +Y); se oculta fuera del lienzo.")]
        [SerializeField] GameObject visual;
        [SerializeField] Renderer tip;

        const float LiftMeters = 0.008f;
        const float LiftSmoothing = 18f;
        const float VelocitySmoothing = 12f;
        const float LeanSeconds = 0.2f; // inclinación por m/s de velocidad
        const float MaxLean = 0.3f;
        static readonly Color EraserTint = new(0.6f, 0.6f, 0.6f);

        MaterialPropertyBlock block;
        Color tipColor;
        Vector3 lastPoint;
        Vector3 smoothedVelocity;
        float lift;
        bool wasOverCanvas;

        void Awake()
        {
            block = new MaterialPropertyBlock();
            visual.SetActive(false);
        }

        void LateUpdate()
        {
            var cam = Camera.main;
            bool show = brush.HasHit && cam != null;
            visual.SetActive(show);
            if (!show)
            {
                wasOverCanvas = false;
                return;
            }

            float dt = Time.unscaledDeltaTime;
            Vector3 point = brush.HitPoint;
            if (!wasOverCanvas)
            {
                lastPoint = point; // entra en el lienzo: sin velocidad ni salto
                smoothedVelocity = Vector3.zero;
                lift = LiftMeters;
            }
            wasOverCanvas = true;
            if (dt > 0f)
                smoothedVelocity = Vector3.Lerp(smoothedVelocity, (point - lastPoint) / dt, 1f - Mathf.Exp(-VelocitySmoothing * dt));
            lastPoint = point;
            lift = Mathf.Lerp(lift, brush.IsStroking ? 0f : LiftMeters, 1f - Mathf.Exp(-LiftSmoothing * dt));

            // Mango hacia la cámara, a la derecha y abajo; el cuerpo se queda atrás respecto al movimiento de la punta.
            var view = cam.transform;
            Vector3 axis = (-view.forward * 0.6f + view.right * 0.55f - view.up * 0.55f).normalized;
            axis = (axis - Vector3.ClampMagnitude(smoothedVelocity * LeanSeconds, MaxLean)).normalized;
            transform.SetPositionAndRotation(point + brush.HitNormal * lift, Quaternion.FromToRotation(Vector3.up, axis));

            UpdateTipColor();
        }

        void UpdateTipColor()
        {
            Color color = brush.EraserActive ? EraserTint
                : brush.PickedColor ?? (brush.SelectedPigment != null ? brush.SelectedPigment.Color : EraserTint);
            if (color == tipColor) return;
            tipColor = color;
            block.SetColor(BaseColor, color);
            tip.SetPropertyBlock(block);
        }
    }
}
