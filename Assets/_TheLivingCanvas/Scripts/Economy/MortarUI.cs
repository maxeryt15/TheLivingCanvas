using System.Collections.Generic;
using System.Linq;
using TheLivingCanvas.Core;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Painting;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Economy
{
    /// <summary>
    /// Panel del mortero: una fila por montón de cosecha; "Grind" muele una unidad y da pigmento de su color
    /// (el de la variante, si lo es). Moler un color que aún no está en la paleta lo desbloquea.
    /// </summary>
    public class MortarUI : ModalPanel
    {
        [SerializeField] PlayerInventory inventory;
        [SerializeField] PigmentStock stock;
        [SerializeField] PaintBrushController brush;
        [SerializeField] RectTransform rowContainer;
        [Tooltip("Fila desactivada que se clona por montón (RawImage 'Icon', Text 'Name', Button 'Buy' con Text).")]
        [SerializeField] GameObject rowTemplate;
        [SerializeField] Text messageLabel;

        readonly List<GameObject> rows = new();

        protected override void Awake()
        {
            base.Awake();
            rowTemplate.SetActive(false);
        }

        public void Open()
        {
            if (!TryOpen()) return;
            messageLabel.text = string.Empty;
            Rebuild();
        }

        public void Grind(CropItem crop)
        {
            var pigment = crop.GrindPigment;
            if (pigment == null || !inventory.TryConsume(crop.StackKey)) return;
            int amount = crop.Crop.PigmentPerUnit;
            bool unlocked = brush.AddPigment(pigment); // false si ya estaba en la paleta
            stock.Add(pigment, amount);
            messageLabel.text = unlocked
                ? $"+{amount} {pigment.DisplayName}  ·  New color for your palette!"
                : $"+{amount} {pigment.DisplayName}";
            Rebuild();
        }

        void Rebuild()
        {
            foreach (var row in rows)
                Destroy(row);
            rows.Clear();

            var crops = inventory.Items.OfType<CropItem>().Where(c => c.GrindPigment != null).ToList();
            if (crops.Count == 0 && messageLabel.text.Length == 0)
                messageLabel.text = "No crops to grind. Harvest something first!";

            foreach (var crop in crops)
            {
                var row = Instantiate(rowTemplate, rowContainer);
                row.SetActive(true);
                row.transform.Find("Icon").GetComponent<RawImage>().texture = crop.Icon;
                row.transform.Find("Name").GetComponent<Text>().text =
                    $"{crop.DisplayName}  x{crop.Quantity}\n<size=18>Each one gives {crop.Crop.PigmentPerUnit} {crop.GrindPigment.DisplayName}</size>";
                var grind = row.transform.Find("Buy").GetComponent<Button>();
                grind.GetComponentInChildren<Text>().text = "Grind";
                grind.onClick.AddListener(() => Grind(crop));
                rows.Add(row);
            }
        }
    }
}
