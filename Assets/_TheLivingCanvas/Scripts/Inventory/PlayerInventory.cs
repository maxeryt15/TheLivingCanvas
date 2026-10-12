using System;
using System.Collections.Generic;
using TheLivingCanvas.Data;
using TheLivingCanvas.Save;
using UnityEngine;

namespace TheLivingCanvas.Inventory
{
    /// <summary>Inventario placeholder del jugador: una lista sin límite.</summary>
    public class PlayerInventory : MonoBehaviour, ISaveable
    {
        [Tooltip("Tipo de los lienzos en blanco con los que empieza el jugador.")]
        [SerializeField] CanvasType startingCanvasType;
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
                items.Add(new BlankCanvasItem(startingCanvasType, startingCanvases));
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

        public void WriteSave(SaveData data)
        {
            foreach (var item in items)
            {
                switch (item)
                {
                    case BlankCanvasItem canvas:
                        data.inventory.Add(new ItemSave { kind = "canvas", id = canvas.Type.Id, quantity = canvas.Quantity });
                        break;
                    case CropItem crop:
                        data.inventory.Add(new ItemSave { kind = "crop", id = crop.Crop.Id, variant = crop.Variant?.id ?? string.Empty, quantity = crop.Quantity });
                        break;
                    case PaintingItem painting:
                        data.inventory.Add(new ItemSave { kind = "painting", quantity = 1, painting = PaintingStore.ToSave(painting) });
                        break;
                }
            }
        }

        public void ReadSave(SaveData data, SaveRegistry registry)
        {
            items.Clear(); // fuera los lienzos iniciales de Awake
            foreach (var entry in data.inventory)
            {
                var item = ItemFromSave(entry, registry);
                if (item != null) items.Add(item);
            }
            Changed?.Invoke(); // sin ItemAdded: no son recibos nuevos
        }

        static InventoryItem ItemFromSave(ItemSave entry, SaveRegistry registry)
        {
            switch (entry.kind)
            {
                case "canvas":
                    var canvasType = registry.FindCanvasType(entry.id);
                    return canvasType != null ? new BlankCanvasItem(canvasType, entry.quantity) : null;
                case "crop":
                    var crop = registry.FindCrop(entry.id);
                    if (crop == null) return null;
                    CropVariant variant = null; // variante desconocida = cultivo normal
                    if (!string.IsNullOrEmpty(entry.variant))
                        foreach (var candidate in crop.Variants)
                            if (candidate.id == entry.variant) variant = candidate;
                    return new CropItem(crop, variant, entry.quantity);
                case "painting":
                    return PaintingStore.FromSave(entry.painting, registry);
                default:
                    Debug.LogWarning($"[Save] Unknown inventory item kind '{entry.kind}'; skipped.");
                    return null;
            }
        }
    }
}
