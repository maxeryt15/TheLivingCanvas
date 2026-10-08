using System;
using System.Collections.Generic;
using UnityEngine;

namespace TheLivingCanvas.Inventory
{
    /// <summary>Inventario placeholder del jugador: una lista sin límite ni guardado (Fase 18).</summary>
    public class PlayerInventory : MonoBehaviour
    {
        readonly List<InventoryItem> items = new();

        public IReadOnlyList<InventoryItem> Items => items;

        /// <summary>Se dispara con el objeto recién añadido.</summary>
        public event Action<InventoryItem> ItemAdded;

        public void Add(InventoryItem item)
        {
            items.Add(item);
            ItemAdded?.Invoke(item);
        }
    }
}
