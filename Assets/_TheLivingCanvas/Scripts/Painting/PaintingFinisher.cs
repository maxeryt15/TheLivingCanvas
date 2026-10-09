using System.Text;
using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Botón "Finish painting": evalúa el lienzo activo. Si falta pintura en alguna zona lo dice con
    /// amabilidad y se sigue pintando. Si pasa, gasta el pigmento que lleva la pintura (o avisa de cuál falta),
    /// marca el lienzo como terminado (listo para recogerlo) y sale del modo pintura.
    /// </summary>
    public class PaintingFinisher : MonoBehaviour
    {
        [SerializeField] PaintModeController paintMode;
        [SerializeField] PaintFeedbackUI feedback;
        [SerializeField] PaintBrushController brush;
        [SerializeField] PigmentStock stock;

        public void Finish()
        {
            var canvas = paintMode.ActiveCanvas;
            if (canvas == null || canvas.Crop == null) return;

            var result = PaintEvaluator.Evaluate(canvas.Surface, canvas.Crop.Template, canvas.Crop.Variants);
            if (!result.CanComeToLife)
            {
                feedback.Show(MissingPaintMessage(result), success: false);
                return;
            }

            var usage = PaintUsage.Measure(canvas.Surface, brush.Palette);
            var shortage = stock.FindShortage(usage);
            if (shortage != null)
            {
                feedback.Show($"Not enough {shortage.DisplayName} (need {usage[shortage]}, have {stock.Get(shortage)}).\n"
                    + "Buy more at the shop, or erase some of it.", success: false);
                return;
            }
            stock.TrySpend(usage);

            canvas.MarkFinished(result);
            paintMode.Exit();
            var variant = canvas.Crop.FindVariant(result);
            string name = (variant?.displayName ?? canvas.Crop.DisplayName).ToLowerInvariant();
            string rarity = variant != null ? $"  ·  {variant.rarity} variant!" : string.Empty;
            string filled = result.CappedByFill
                ? "\n(Mostly filled: paint by hand for a Masterpiece.)" : string.Empty;
            feedback.Show($"Your {name} painting is finished! Quality: {result.Quality}{rarity}{filled}\nTake it from the easel.", success: true);
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
