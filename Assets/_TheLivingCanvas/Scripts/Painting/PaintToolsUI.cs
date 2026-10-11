using System.Collections.Generic;
using TheLivingCanvas.Data;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Paleta lateral del modo pintura: una muestra por pigmento (generadas desde la paleta del
    /// pincel) con la cantidad que queda, tamaño del pincel y borrador. Refleja el estado de PaintBrushController.
    /// </summary>
    public class PaintToolsUI : MonoBehaviour
    {
        [SerializeField] PaintBrushController brush;
        [SerializeField] PigmentStock stock;
        [SerializeField] RectTransform swatchContainer;
        [Tooltip("Botón de muestra desactivado que se clona por cada pigmento (con un Text 'Amount').")]
        [SerializeField] Button swatchTemplate;
        [SerializeField] Slider sizeSlider;
        [Tooltip("Botón de pincel desactivado, en la fila del borrador: se clona por cada pincel delante del borrador.")]
        [SerializeField] Button brushTemplate;
        [SerializeField] Button eraserButton;
        [SerializeField] Button undoButton;
        [SerializeField] Button redoButton;
        [SerializeField] Button clearButton;
        [SerializeField] Button guideButton;
        [SerializeField] Button hintsButton;

        readonly Dictionary<PigmentDefinition, Outline> swatchHighlights = new();
        readonly Dictionary<PigmentDefinition, Text> swatchAmounts = new();
        readonly Dictionary<BrushDefinition, Outline> brushHighlights = new();
        Outline eraserHighlight;
        Outline guideHighlight;
        Outline hintsHighlight;

        void Awake()
        {
            swatchTemplate.gameObject.SetActive(false);
            foreach (var pigment in brush.Palette)
                AddSwatch(pigment);
            // Suscrito siempre (no solo con el panel visible): se compran pigmentos sin estar pintando.
            brush.PigmentAdded += AddSwatch;
            stock.Changed += RefreshAmounts;

            brushTemplate.gameObject.SetActive(false);
            foreach (var b in brush.Brushes)
                AddBrushButton(b);
            brush.BrushAdded += AddBrushButton;

            eraserHighlight = eraserButton.GetComponent<Outline>();
            eraserButton.onClick.AddListener(() => brush.SetEraser(!brush.EraserActive));

            sizeSlider.minValue = brush.MinBrushRadius;
            sizeSlider.onValueChanged.AddListener(brush.SetBrushRadius);

            undoButton.onClick.AddListener(brush.Undo);
            redoButton.onClick.AddListener(brush.Redo);
            clearButton.onClick.AddListener(brush.ClearCanvas);

            guideHighlight = guideButton.GetComponent<Outline>();
            hintsHighlight = hintsButton.GetComponent<Outline>();
            guideButton.onClick.AddListener(() => brush.SetShowGuide(!brush.ShowGuide));
            hintsButton.onClick.AddListener(() => brush.SetShowColorHints(!brush.ShowColorHints));
        }

        void OnDestroy()
        {
            brush.PigmentAdded -= AddSwatch;
            brush.BrushAdded -= AddBrushButton;
            stock.Changed -= RefreshAmounts;
        }

        void AddBrushButton(BrushDefinition b)
        {
            var button = Instantiate(brushTemplate, brushTemplate.transform.parent);
            button.name = $"Brush_{b.Id}";
            button.gameObject.SetActive(true);
            button.transform.SetSiblingIndex(eraserButton.transform.GetSiblingIndex()); // justo antes del borrador
            button.GetComponentInChildren<Text>().text = b.DisplayName;
            button.onClick.AddListener(() => brush.SelectBrush(b));
            brushHighlights[b] = button.GetComponent<Outline>(); // se marca en Refresh (al mostrarse el panel)
        }

        void AddSwatch(PigmentDefinition pigment)
        {
            var swatch = Instantiate(swatchTemplate, swatchContainer);
            swatch.name = $"Swatch_{pigment.Id}";
            swatch.gameObject.SetActive(true);
            swatch.image.color = pigment.Color;
            swatch.onClick.AddListener(() => brush.SelectPigment(pigment));
            swatchHighlights[pigment] = swatch.GetComponent<Outline>();
            swatchAmounts[pigment] = swatch.transform.Find("Amount").GetComponent<Text>();
            RefreshAmounts();
        }

        void RefreshAmounts()
        {
            foreach (var pair in swatchAmounts)
                pair.Value.text = stock.Get(pair.Key).ToString();
        }

        void Update()
        {
            undoButton.interactable = brush.CanUndo;
            redoButton.interactable = brush.CanRedo;
        }

        void OnEnable()
        {
            brush.ToolsChanged += Refresh;
            Refresh();
        }

        void OnDisable() => brush.ToolsChanged -= Refresh;

        void Refresh()
        {
            foreach (var pair in swatchHighlights)
                pair.Value.enabled = !brush.EraserActive && pair.Key == brush.SelectedPigment;
            foreach (var pair in brushHighlights)
                pair.Value.enabled = pair.Key == brush.SelectedBrush;
            eraserHighlight.enabled = brush.EraserActive;
            guideHighlight.enabled = brush.ShowGuide;
            hintsHighlight.enabled = brush.ShowColorHints;
            sizeSlider.maxValue = brush.MaxBrushRadius; // depende de la resolución del lienzo activo
            sizeSlider.SetValueWithoutNotify(brush.BrushRadius);
        }
    }
}
