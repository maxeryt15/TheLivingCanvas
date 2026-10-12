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
        public static string Pay(CommissionDefinition commission, Wallet wallet, ArtistLevel artistLevel, PigmentStock stock, PaintBrushController brush) =>
            Pay(commission.RewardCoins, commission.RewardXp, commission.RewardPigment, commission.RewardPigmentAmount, wallet, artistLevel, stock, brush);

        /// <summary>Igual con las cantidades sueltas (también para los sets de la colección); el pigmento puede ser null.</summary>
        public static string Pay(int coins, int xp, PigmentDefinition pigment, int pigmentAmount, Wallet wallet, ArtistLevel artistLevel, PigmentStock stock, PaintBrushController brush)
        {
            var parts = new List<string>();
            if (coins > 0)
            {
                wallet.Add(coins);
                parts.Add($"+{coins} coins");
            }
            if (xp > 0)
            {
                parts.Add($"+{xp} XP");
                if (artistLevel.AddXp(xp)) parts.Add("Level up!");
            }
            if (pigment != null)
            {
                bool unlocked = brush.AddPigment(pigment); // false si ya estaba en la paleta
                stock.Add(pigment, pigmentAmount);
                parts.Add($"+{pigmentAmount} {pigment.DisplayName}" + (unlocked ? " (new color for your palette!)" : ""));
            }
            return "Reward: " + string.Join(" · ", parts);
        }
    }
}
