using System.Collections.Generic;
using TheLivingCanvas.Core;
using TheLivingCanvas.Data;
using TheLivingCanvas.Seasons;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Al poner un lienzo en el caballete: elegir el tipo de lienzo (si el jugador tiene varios), el estilo
    /// (si tiene alguno) y qué cultivo pintar entre los que sabe. Las elecciones comparten el mismo panel de filas.
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

        /// <summary>Elegir el estilo del cuadro: Classic (sin estilo) o uno comprado.</summary>
        public void Open(CanvasInteractable easel, CanvasType canvasType, IReadOnlyList<StyleDefinition> styles)
        {
            if (!TryOpen()) return;
            Clear("Which style?");
            AddRow(Texture2D.whiteTexture, "Classic · plain brushwork", "Use", () => PickStyle(easel, canvasType, null));
            foreach (var style in styles)
                AddRow(Texture2D.whiteTexture, $"{style.DisplayName} · {style.Description}", "Use", () => PickStyle(easel, canvasType, style));
        }

        /// <summary>Elegir el cultivo que se pinta en un lienzo de <paramref name="canvasType"/> con ese estilo.</summary>
        public void Open(CanvasInteractable easel, CanvasType canvasType, StyleDefinition style, IReadOnlyList<CropDefinition> crops)
        {
            if (!TryOpen()) return;
            Clear("What will you paint?");
            foreach (var crop in crops)
                AddRow(crop.Icon, CropLabel(crop), "Paint", () => PickCrop(easel, canvasType, style, crop));
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
            easel.ChooseStyle(interactor, canvasType);
        }

        void PickStyle(CanvasInteractable easel, CanvasType canvasType, StyleDefinition style)
        {
            Close();
            easel.ChooseCrop(interactor, canvasType, style);
        }

        void PickCrop(CanvasInteractable easel, CanvasType canvasType, StyleDefinition style, CropDefinition crop)
        {
            Close();
            easel.StartPainting(interactor, canvasType, style, crop);
        }
    }
}
