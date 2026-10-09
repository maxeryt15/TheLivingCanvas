using System.Collections.Generic;
using TheLivingCanvas.Core;
using TheLivingCanvas.Data;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Painting
{
    /// <summary>Al poner un lienzo en el caballete: elegir qué cultivo pintar entre los que sabe el jugador.</summary>
    public class CropPickerUI : ModalPanel
    {
        [SerializeField] RectTransform rowContainer;
        [Tooltip("Fila desactivada que se clona por cultivo (RawImage 'Icon', Text 'Name', Button 'Buy' con Text).")]
        [SerializeField] GameObject rowTemplate;

        readonly List<GameObject> rows = new();

        protected override void Awake()
        {
            base.Awake();
            rowTemplate.SetActive(false);
        }

        public void Open(CanvasInteractable easel, IReadOnlyList<CropDefinition> crops)
        {
            if (!TryOpen()) return;
            foreach (var row in rows)
                Destroy(row);
            rows.Clear();

            foreach (var crop in crops)
            {
                var row = Instantiate(rowTemplate, rowContainer);
                row.SetActive(true);
                row.transform.Find("Icon").GetComponent<RawImage>().texture = crop.Icon;
                row.transform.Find("Name").GetComponent<Text>().text = crop.DisplayName;
                var paint = row.transform.Find("Buy").GetComponent<Button>();
                paint.GetComponentInChildren<Text>().text = "Paint";
                paint.onClick.AddListener(() => Pick(easel, crop));
                rows.Add(row);
            }
        }

        void Pick(CanvasInteractable easel, CropDefinition crop)
        {
            Close();
            easel.StartPainting(interactor, crop);
        }
    }
}
