using System;
using UnityEngine;

namespace TheLivingCanvas.Economy
{
    /// <summary>Monedas del jugador. Sin guardado todavía (Fase 18).</summary>
    public class Wallet : MonoBehaviour
    {
        [SerializeField] int coins;

        public int Coins => coins;

        /// <summary>Cambio en las monedas: (total nuevo, diferencia).</summary>
        public event Action<int, int> Changed;

        public void Add(int amount)
        {
            if (amount <= 0) return;
            coins += amount;
            Changed?.Invoke(coins, amount);
        }

        public bool CanAfford(int amount) => coins >= amount;

        public bool TrySpend(int amount)
        {
            if (amount < 0 || coins < amount) return false;
            coins -= amount;
            Changed?.Invoke(coins, -amount);
            return true;
        }
    }
}
