using System.Collections.Generic;
using TheLivingCanvas.Data;
using TheLivingCanvas.Economy;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Painting;
using TheLivingCanvas.Progression;

namespace TheLivingCanvas.Npcs
{
    /// <summary>Entrega de recompensas de un encargo (compartida por los personajes y el tablón).</summary>
    public static class CommissionRewards
    {
        /// <summary>Entrega monedas, XP y pigmento del encargo; devuelve la línea que resume lo recibido.</summary>
        public static string Pay(CommissionDefinition commission, Wallet wallet, ArtistLevel artistLevel, PigmentStock stock, PaintBrushController brush)
        {
            var parts = new List<string>();
            if (commission.RewardCoins > 0)
            {
                wallet.Add(commission.RewardCoins);
                parts.Add($"+{commission.RewardCoins} coins");
            }
            if (commission.RewardXp > 0)
            {
                parts.Add($"+{commission.RewardXp} XP");
                if (artistLevel.AddXp(commission.RewardXp)) parts.Add("Level up!");
            }
            var pigment = commission.RewardPigment;
            if (pigment != null)
            {
                bool unlocked = brush.AddPigment(pigment); // false si ya estaba en la paleta
                stock.Add(pigment, commission.RewardPigmentAmount);
                parts.Add($"+{commission.RewardPigmentAmount} {pigment.DisplayName}" + (unlocked ? " (new color for your palette!)" : ""));
            }
            return "Reward: " + string.Join(" · ", parts);
        }
    }
}
