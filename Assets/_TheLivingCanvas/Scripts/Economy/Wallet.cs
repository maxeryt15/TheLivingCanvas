using System;
using TheLivingCanvas.Save;
using UnityEngine;

namespace TheLivingCanvas.Economy
{
    /// <summary>Monedas del jugador.</summary>
    public class Wallet : MonoBehaviour, ISaveable
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

        public void WriteSave(SaveData data) => data.coins = coins;

        public void ReadSave(SaveData data, SaveRegistry registry)
        {
            coins = Mathf.Max(0, data.coins);
            Changed?.Invoke(coins, 0); // diferencia 0: refresca el contador sin popup
        }
    }
}
