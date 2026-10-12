using System.Text;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Lectura de depuración del lienzo activo: evaluación por zonas si el lienzo tiene cultivo,
    /// si no cobertura por pigmento. Recalcula solo cuando la pintura cambió (máx. unas veces por segundo).
    /// Oculta por defecto (no es para el jugador): F3 la muestra u oculta.
    /// </summary>
    public class CoverageReadoutUI : MonoBehaviour
    {
        [SerializeField] PaintModeController paintMode;
        [SerializeField] PaintBrushController brush;
        [SerializeField] Text label;
        [SerializeField] float minInterval = 0.25f;

        readonly StringBuilder builder = new();
        PaintSurface lastSurface;
        int lastRevision = -1;
        float nextUpdateTime;
        CanvasGroup group;
        static bool visible;

        void Awake()
        {
            group = gameObject.AddComponent<CanvasGroup>();
            group.blocksRaycasts = false;
        }

        void OnEnable() => lastRevision = -1; // fuerza recalcular al volver a pintar

        void Update()
        {
            if (Keyboard.current != null && Keyboard.current.f3Key.wasPressedThisFrame)
            {
                visible = !visible;
                lastRevision = -1;
            }
            group.alpha = visible ? 1f : 0f;
            if (!visible || !paintMode.IsPainting || Time.unscaledTime < nextUpdateTime) return;
            var surface = paintMode.ActiveCanvas.Surface;
            if (surface == lastSurface && surface.Revision == lastRevision) return;

            lastSurface = surface;
            lastRevision = surface.Revision;
            nextUpdateTime = Time.unscaledTime + minInterval;

            var crop = paintMode.ActiveCanvas.Crop;
            label.text = crop != null
                ? Format(PaintEvaluator.Evaluate(surface, crop.Template, crop.Variants,
                    paintMode.ActiveCanvas.Style, paintMode.ActiveCanvas.CanvasType))
                : Format(PaintCoverage.Analyze(surface, brush.Palette));
        }

        /// <summary>Progreso por zona de la plantilla (para ajustar la evaluación).</summary>
        string Format(PaintingResult result)
        {
            builder.Clear();
            builder.Append("Evaluation (debug)\n");
            foreach (var zone in result.Zones)
            {
                builder.Append(zone.Passed ? "[ok] " : "[  ] ")
                    .Append(zone.Requirement.zoneName).Append(": ").Append(Percent(zone.Coverage))
                    .Append("  (color ").Append(Percent(zone.ColorFit)).Append(")\n");
            }
            builder.Append("Outside: ").Append(Percent(result.Spill)).Append('\n');
            builder.Append("Score: ").Append(Percent(result.Score)).Append(" · ").Append(result.Quality);
            return builder.ToString();
        }

        string Format(CoverageResult result)
        {
            builder.Clear();
            builder.Append("Coverage (debug)\n");
            builder.Append("Painted: ").Append(Percent(result.Painted)).Append('\n');
            foreach (var pair in result.ByPigment)
                if (pair.Value >= 0.0005f)
                    builder.Append(pair.Key.DisplayName).Append(": ").Append(Percent(pair.Value)).Append('\n');
            if (result.Mixed >= 0.0005f)
                builder.Append("Mixed / edges: ").Append(Percent(result.Mixed));
            return builder.ToString().TrimEnd('\n');
        }

        static string Percent(float value) => (value * 100f).ToString("0.0") + "%";
    }
}
