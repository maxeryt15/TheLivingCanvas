using System;
using System.Collections.Generic;
using System.Linq;
using TheLivingCanvas.Core;
using TheLivingCanvas.Data;
using TheLivingCanvas.Inventory;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Npcs
{
    /// <summary>Panel de entrega: una fila por pintura del inventario que cumple el encargo; "Give" la entrega.</summary>
    public class CommissionUI : ModalPanel
    {
        [SerializeField] PlayerInventory inventory;
        [SerializeField] RectTransform rowContainer;
        [Tooltip("Fila desactivada que se clona por pintura (RawImage 'Icon', Text 'Name', Button 'Buy' con Text).")]
        [SerializeField] GameObject rowTemplate;
        [SerializeField] Text messageLabel;

        readonly List<GameObject> rows = new();

        protected override void Awake()
        {
            base.Awake();
            rowTemplate.SetActive(false);
        }

        public void Open(CommissionDefinition commission, Action<PaintingItem> onGive)
        {
            if (!TryOpen()) return;

            var paintings = inventory.Items.OfType<PaintingItem>().Where(commission.Accepts).ToList();
            messageLabel.text = $"Wanted: {commission.Summary}"
                + (paintings.Count == 0 ? "\nYou don't have a matching painting yet." : string.Empty);

            foreach (var row in rows)
                Destroy(row);
            rows.Clear();

            foreach (var painting in paintings)
            {
                var row = Instantiate(rowTemplate, rowContainer);
                row.SetActive(true);
                row.transform.Find("Icon").GetComponent<RawImage>().texture = painting.Icon;
                row.transform.Find("Name").GetComponent<Text>().text = $"{painting.DisplayName}\n<size=18>{painting.Detail}</size>";
                var give = row.transform.Find("Buy").GetComponent<Button>();
                give.GetComponentInChildren<Text>().text = "Give";
                give.onClick.AddListener(() =>
                {
                    if (!inventory.Remove(painting)) return; // ya no está (fila vieja)
                    Close();
                    onGive(painting);
                });
                rows.Add(row);
            }
        }
    }
}
