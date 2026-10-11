using System.Collections.Generic;
using System.Linq;
using TheLivingCanvas.Core;
using TheLivingCanvas.Inventory;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Gallery
{
    /// <summary>Panel para colgar: una fila por pintura del inventario (las semillas no cuentan); "Hang" la cuelga en el marco.</summary>
    public class GalleryHangUI : ModalPanel
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

        public void Open(GalleryFrame frame)
        {
            if (!TryOpen()) return;

            var paintings = inventory.Items.OfType<PaintingItem>().Where(p => p is not SeedItem).ToList();
            messageLabel.text = paintings.Count == 0 ? "No paintings to hang. Finish one at the easel first!" : string.Empty;

            foreach (var row in rows)
                Destroy(row);
            rows.Clear();

            foreach (var painting in paintings)
            {
                var row = Instantiate(rowTemplate, rowContainer);
                row.SetActive(true);
                row.transform.Find("Icon").GetComponent<RawImage>().texture = painting.Icon;
                row.transform.Find("Name").GetComponent<Text>().text = $"{painting.DisplayName}\n<size=18>{painting.Detail}</size>";
                var hang = row.transform.Find("Buy").GetComponent<Button>();
                hang.GetComponentInChildren<Text>().text = "Hang";
                hang.onClick.AddListener(() =>
                {
                    frame.Hang(painting);
                    Close();
                });
                rows.Add(row);
            }
        }
    }
}
