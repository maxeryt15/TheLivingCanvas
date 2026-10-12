using System.Collections.Generic;
using System.Linq;
using TheLivingCanvas.Core;
using TheLivingCanvas.Data;
using TheLivingCanvas.Economy;
using TheLivingCanvas.Growth;
using TheLivingCanvas.Inventory;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Npcs
{
    /// <summary>Panel del marchante: una fila por pintura original del inventario; "Sell" la vende y el panel sigue abierto.</summary>
    public class ArtDealerUI : ModalPanel
    {
        /// <summary>Vender paga un poco más que plantar y cosechar, pero se pierde la semilla.</summary>
        const float SellBonus = 1.5f;

        [SerializeField] PlayerInventory inventory;
        [SerializeField] Wallet wallet;
        [SerializeField] RectTransform rowContainer;
        [Tooltip("Fila desactivada que se clona por pintura (RawImage 'Icon', Text 'Name', Button 'Buy' con Text).")]
        [SerializeField] GameObject rowTemplate;
        [SerializeField] Text messageLabel;

        readonly List<GameObject> rows = new();

        /// <summary>Monedas que paga el marchante: cultivo × rareza × cosecha por calidad × lienzo × bonus.</summary>
        public static int PriceOf(PaintingItem p)
        {
            var rarity = p.Variant?.rarity ?? Rarity.Common;
            return Mathf.RoundToInt(p.Crop.SellPrice * rarity.PriceMultiplier()
                * CropPlant.HarvestAmount(p.Result.Quality) * p.CanvasType.HarvestMultiplier * SellBonus);
        }

        protected override void Awake()
        {
            base.Awake();
            rowTemplate.SetActive(false);
        }

        public void Open()
        {
            if (!TryOpen()) return;
            Refresh("I only buy originals.");
        }

        /// <summary>Rehace la lista con las pinturas originales que quedan; message va arriba.</summary>
        void Refresh(string message)
        {
            var paintings = inventory.Items.OfType<PaintingItem>().Where(p => p is not SeedItem).ToList();
            messageLabel.text = message + (paintings.Count == 0 ? "\nYou have no original paintings to sell." : string.Empty);

            foreach (var row in rows)
                Destroy(row);
            rows.Clear();

            foreach (var painting in paintings)
            {
                var row = Instantiate(rowTemplate, rowContainer);
                row.SetActive(true);
                row.transform.Find("Icon").GetComponent<RawImage>().texture = painting.Icon;
                row.transform.Find("Name").GetComponent<Text>().text = $"{painting.DisplayName}\n<size=18>{painting.Detail}</size>";
                int price = PriceOf(painting);
                var sell = row.transform.Find("Buy").GetComponent<Button>();
                sell.GetComponentInChildren<Text>().text = $"Sell {price}";
                sell.onClick.AddListener(() =>
                {
                    if (!inventory.Remove(painting)) return; // ya no está (fila vieja)
                    wallet.Add(price);
                    Refresh($"Sold {painting.DisplayName} for {price} coins.");
                });
                rows.Add(row);
            }
        }
    }
}
