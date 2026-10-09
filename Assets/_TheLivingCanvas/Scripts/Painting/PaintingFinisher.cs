using System.Text;
using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Botón "Finish painting": evalúa el lienzo activo. Si falta pintura en alguna zona lo dice con
    /// amabilidad y se sigue pintando; si pasa, marca el lienzo como terminado (listo para recogerlo)
    /// y sale del modo pintura.
    /// </summary>
    public class PaintingFinisher : MonoBehaviour
    {
        [SerializeField] PaintModeController paintMode;
        [SerializeField] PaintFeedbackUI feedback;

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

            canvas.MarkFinished(result);
            paintMode.Exit();
            var variant = canvas.Crop.FindVariant(result);
            string name = (variant?.displayName ?? canvas.Crop.DisplayName).ToLowerInvariant();
            string rarity = variant != null ? $"  ·  {variant.rarity} variant!" : string.Empty;
            feedback.Show($"Your {name} painting is finished! Quality: {result.Quality}{rarity}\nTake it from the easel.", success: true);
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
