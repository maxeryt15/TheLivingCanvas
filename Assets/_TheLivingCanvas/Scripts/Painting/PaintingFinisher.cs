using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using TheLivingCanvas.Audio;
using TheLivingCanvas.Feedback;
using TheLivingCanvas.Progression;
using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Botón "Finish painting": evalúa el lienzo activo. Si falta pintura en alguna zona lo dice con
    /// amabilidad y se sigue pintando. Si pasa, gasta el pigmento que lleva la pintura (o avisa de cuál falta),
    /// marca el lienzo como terminado (listo para recogerlo), da la XP de artista y sale del modo pintura.
    /// </summary>
    public class PaintingFinisher : MonoBehaviour
    {
        [SerializeField] PaintModeController paintMode;
        [SerializeField] PaintFeedbackUI feedback;
        [SerializeField] PaintBrushController brush;
        [SerializeField] PigmentStock stock;
        [SerializeField] ArtistLevel artistLevel;

        /// <summary>Se dispara al terminar una pintura con éxito (no si falta pintura o pigmento).</summary>
        public event Action Finished;

        public void Finish()
        {
            var canvas = paintMode.ActiveCanvas;
            if (canvas == null || canvas.Crop == null) return;

            var result = PaintEvaluator.Evaluate(canvas.Surface, canvas.Crop.Template, canvas.Crop.Variants, canvas.Style, canvas.CanvasType);
            if (!result.CanComeToLife)
            {
                feedback.Show(MissingPaintMessage(result), success: false);
                return;
            }

            // El tipo de lienzo y el estilo escalan el gasto antes de comprobar si alcanza (se redondea hacia arriba).
            float pigmentMultiplier = canvas.CanvasType.PigmentMultiplier * (canvas.Style != null ? canvas.Style.PigmentMultiplier : 1f);
            var usage = PaintUsage.Measure(canvas.Surface, brush.Palette)
                .ToDictionary(u => u.Key, u => Mathf.CeilToInt(u.Value * pigmentMultiplier));
            var shortage = stock.FindShortage(usage);
            if (shortage != null)
            {
                feedback.Show($"Not enough {shortage.DisplayName} (need {usage[shortage]}, have {stock.Get(shortage)}).\n"
                    + "Buy more at the shop, or erase some of it.", success: false);
                return;
            }
            stock.TrySpend(usage);

            canvas.MarkFinished(result);
            SfxPlayer.Play(Sfx.PaintFinish);
            // La salpicadura sale del centro del lienzo hacia el lado desde el que se pinta.
            var center = canvas.Surface.transform.position;
            PaintBurst.FinishSplash(center, canvas.ViewPoint.position - center, result.Zones.Select(z => z.DominantColor).ToArray());
            paintMode.Exit();
            var variant = canvas.Crop.FindVariant(result);
            string name = (variant?.displayName ?? canvas.Crop.DisplayName).ToLowerInvariant();
            string rarity = variant != null ? $"  ·  {variant.rarity} variant!" : string.Empty;
            string filled = result.CappedByFill
                ? "\n(Mostly filled: paint by hand for a Masterpiece.)" : string.Empty;
            var gain = artistLevel.AwardPainting(result.Quality, canvas.Crop, variant);
            feedback.Show($"Your {name} painting is finished! Quality: {result.Quality}{rarity}{filled}\n"
                + $"{XpMessage(gain, artistLevel.Level)}\nTake it from the easel.", success: true);
            Finished?.Invoke();
        }

        static string XpMessage(XpGain gain, int level)
        {
            var found = new List<string>();
            if (gain.NewCrop) found.Add("new crop!");
            if (gain.NewVariant) found.Add("new variant!");
            string message = $"+{gain.Xp} XP" + (found.Count > 0 ? $" ({string.Join(" ", found)})" : string.Empty);
            if (gain.LeveledUp)
                message += $"\nLevel up! You are now level {level} — new things unlocked.";
            return message;
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
