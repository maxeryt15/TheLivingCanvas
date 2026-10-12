using System.Collections.Generic;
using TheLivingCanvas.Core;
using TheLivingCanvas.Data;
using TheLivingCanvas.Seasons;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Al poner un lienzo en el caballete: elegir el tipo de lienzo (si el jugador tiene varios)
    /// y qué cultivo pintar entre los que sabe. Las dos elecciones comparten el mismo panel de filas.
    /// </summary>
    public class CropPickerUI : ModalPanel
    {
        [SerializeField] RectTransform rowContainer;
        [Tooltip("Fila desactivada que se clona por opción (RawImage 'Icon', Text 'Name', Button 'Buy' con Text).")]
        [SerializeField] GameObject rowTemplate;

        [SerializeField] SeasonClock seasons;

        readonly List<GameObject> rows = new();

        protected override void Awake()
        {
            base.Awake();
            rowTemplate.SetActive(false);
        }

        /// <summary>Elegir el tipo de lienzo; después sigue el paso del cultivo.</summary>
        public void Open(CanvasInteractable easel, IReadOnlyList<CanvasType> canvasTypes)
        {
            if (!TryOpen()) return;
            Clear("Which canvas?");
            foreach (var canvasType in canvasTypes)
                AddRow(Texture2D.whiteTexture, canvasType.DisplayName, "Use", () => PickCanvas(easel, canvasType));
        }

        /// <summary>Elegir el cultivo que se pinta en un lienzo de <paramref name="canvasType"/>.</summary>
        public void Open(CanvasInteractable easel, CanvasType canvasType, IReadOnlyList<CropDefinition> crops)
        {
            if (!TryOpen()) return;
            Clear("What will you paint?");
            foreach (var crop in crops)
                AddRow(crop.Icon, CropLabel(crop), "Paint", () => PickCrop(easel, canvasType, crop));
        }

        string CropLabel(CropDefinition crop) => crop.IsInSeason(seasons.Current)
            ? $"{crop.DisplayName} · in season! +{CropDefinition.InSeasonBonus} harvest"
            : $"{crop.DisplayName} · best in {crop.FavoriteSeason}";

        void Clear(string title)
        {
            panel.transform.Find("Title").GetComponent<Text>().text = title;
            foreach (var row in rows)
                Destroy(row);
            rows.Clear();
        }

        void AddRow(Texture icon, string label, string buttonText, UnityEngine.Events.UnityAction onClick)
        {
            var row = Instantiate(rowTemplate, rowContainer);
            row.SetActive(true);
            row.transform.Find("Icon").GetComponent<RawImage>().texture = icon;
            row.transform.Find("Name").GetComponent<Text>().text = label;
            var button = row.transform.Find("Buy").GetComponent<Button>();
            button.GetComponentInChildren<Text>().text = buttonText;
            button.onClick.AddListener(onClick);
            rows.Add(row);
        }

        void PickCanvas(CanvasInteractable easel, CanvasType canvasType)
        {
            Close();
            easel.ChooseCrop(interactor, canvasType);
        }

        void PickCrop(CanvasInteractable easel, CanvasType canvasType, CropDefinition crop)
        {
            Close();
            easel.StartPainting(interactor, canvasType, crop);
        }
    }
}
