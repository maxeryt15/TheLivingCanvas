using System;
using System.Text;
using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Botón "Finish painting": evalúa el lienzo activo. Si falta pintura en alguna zona lo dice con
    /// amabilidad y se sigue pintando; si pasa, anuncia el resultado y dispara <see cref="Completed"/>
    /// (la transición pintura → cultivo, Fase 4C/4D, se suscribe ahí).
    /// </summary>
    public class PaintingFinisher : MonoBehaviour
    {
        [SerializeField] PaintModeController paintMode;
        [SerializeField] PaintFeedbackUI feedback;

        public event Action<CanvasInteractable, PaintingResult> Completed;

        public void Finish()
        {
            var canvas = paintMode.ActiveCanvas;
            if (canvas == null || canvas.Crop == null) return;

            var result = PaintEvaluator.Evaluate(canvas.Surface, canvas.Crop.Template);
            if (!result.CanComeToLife)
            {
                feedback.Show(MissingPaintMessage(result), success: false);
                return;
            }

            feedback.Show($"Your {canvas.Crop.DisplayName.ToLowerInvariant()} is ready to come to life!\nQuality: {result.Quality}", success: true);
            Completed?.Invoke(canvas, result);
        }

        static string MissingPaintMessage(PaintingResult result)
        {
            var builder = new StringBuilder("Almost there!");
            foreach (var zone in result.Zones)
                if (!zone.Passed)
                    builder.Append('\n').Append(zone.Requirement.missingPaintHint);
            return builder.ToString();
        }
    }
}
