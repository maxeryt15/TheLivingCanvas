using System.Text;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Lectura de depuración de la cobertura del lienzo activo. Recalcula solo cuando la pintura
    /// cambió, como mucho unas pocas veces por segundo.
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

        public CoverageResult LastResult { get; private set; }

        void OnEnable() => lastRevision = -1; // fuerza recalcular al volver a pintar

        void Update()
        {
            if (!paintMode.IsPainting || Time.unscaledTime < nextUpdateTime) return;
            var surface = paintMode.ActiveCanvas.Surface;
            if (surface == lastSurface && surface.Revision == lastRevision) return;

            lastSurface = surface;
            lastRevision = surface.Revision;
            nextUpdateTime = Time.unscaledTime + minInterval;
            LastResult = PaintCoverage.Analyze(surface, brush.Palette);
            label.text = Format(LastResult);
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
