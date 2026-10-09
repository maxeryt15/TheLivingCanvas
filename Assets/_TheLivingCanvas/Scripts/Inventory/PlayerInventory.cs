using System;
using System.Collections.Generic;
using UnityEngine;

namespace TheLivingCanvas.Inventory
{
    /// <summary>Inventario placeholder del jugador: una lista sin límite ni guardado (Fase 18).</summary>
    public class PlayerInventory : MonoBehaviour
    {
        [Tooltip("Lienzos en blanco con los que empieza el jugador.")]
        [SerializeField] int startingCanvases = 3;

        readonly List<InventoryItem> items = new();

        public IReadOnlyList<InventoryItem> Items => items;

        /// <summary>Se dispara con lo recién recibido (antes de apilarlo).</summary>
        public event Action<InventoryItem> ItemAdded;
        /// <summary>Cualquier cambio en el contenido.</summary>
        public event Action Changed;

        void Awake()
        {
            // Sin aviso: ya los tenía al empezar.
            if (startingCanvases > 0)
                items.Add(new BlankCanvasItem(startingCanvases));
        }

        public void Add(InventoryItem item)
        {
            var stack = item.StackKey == null ? null : items.Find(i => i.StackKey == item.StackKey);
            if (stack != null) stack.Quantity += item.Quantity;
            else items.Add(item);

            ItemAdded?.Invoke(item);
            Changed?.Invoke();
        }

        /// <summary>Unidades apiladas con esa clave (0 si no hay).</summary>
        public int Count(string stackKey) => items.Find(i => i.StackKey == stackKey)?.Quantity ?? 0;

        /// <summary>Gasta <paramref name="amount"/> unidades de una pila; false si no hay suficientes.</summary>
        public bool TryConsume(string stackKey, int amount = 1)
        {
            var stack = items.Find(i => i.StackKey == stackKey);
            if (stack == null || stack.Quantity < amount) return false;
            stack.Quantity -= amount;
            if (stack.Quantity == 0) items.Remove(stack);
            Changed?.Invoke();
            return true;
        }

        public bool Remove(InventoryItem item)
        {
            if (!items.Remove(item)) return false;
            Changed?.Invoke();
            return true;
        }
    }
}
