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

        /// <summary>Se dispara con lo recién recibido (antes de apilarlo).</summary>
        public event Action<InventoryItem> ItemAdded;
        /// <summary>Cualquier cambio en el contenido.</summary>
        public event Action Changed;

        public void Add(InventoryItem item)
        {
            var stack = item.StackKey == null ? null : items.Find(i => i.StackKey == item.StackKey);
            if (stack != null) stack.Quantity += item.Quantity;
            else items.Add(item);

            ItemAdded?.Invoke(item);
            Changed?.Invoke();
        }

        public bool Remove(InventoryItem item)
        {
            if (!items.Remove(item)) return false;
            Changed?.Invoke();
            return true;
        }
    }
}
