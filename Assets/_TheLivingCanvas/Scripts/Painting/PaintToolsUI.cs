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
        [SerializeField] PaintModeController paintMode;
        [SerializeField] RectTransform swatchContainer;
        [Tooltip("Botón de muestra desactivado que se clona por cada pigmento (con un Text 'Amount').")]
        [SerializeField] Button swatchTemplate;
        [SerializeField] Slider sizeSlider;
        [Tooltip("Botón de pincel desactivado, en la fila del borrador: se clona por cada pincel delante del borrador.")]
        [SerializeField] Button brushTemplate;
        [SerializeField] Button eraserButton;
        [Tooltip("Botones de herramientas compradas, desactivados hasta tenerlas (segunda fila).")]
        [SerializeField] Button eyedropperButton;
        [SerializeField] Button symmetryButton;
        [Tooltip("Muestra del color copiado con el cuentagotas; oculta hasta copiar uno.")]
        [SerializeField] Button pickedButton;
        [SerializeField] Button undoButton;
        [SerializeField] Button redoButton;
        [SerializeField] Button clearButton;
        [SerializeField] Button guideButton;
        [SerializeField] Button hintsButton;
        [Tooltip("Nombre del color en uso (ayuda para daltonismo).")]
        [SerializeField] Text currentColorLabel;
        [Tooltip("Leyenda zona — color sugerido de la plantilla; se oculta si no hay ninguna.")]
        [SerializeField] GameObject zoneLegendRoot;
        [SerializeField] Text zoneLegendLabel;

        readonly Dictionary<PigmentDefinition, Outline> swatchHighlights = new();
        readonly Dictionary<PigmentDefinition, Text> swatchAmounts = new();
        readonly Dictionary<BrushDefinition, Outline> brushHighlights = new();
        Outline eraserHighlight;
        Outline eyedropperHighlight;
        Outline symmetryHighlight;
        Outline pickedHighlight;
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

            eyedropperHighlight = eyedropperButton.GetComponent<Outline>();
            symmetryHighlight = symmetryButton.GetComponent<Outline>();
            pickedHighlight = pickedButton.GetComponent<Outline>();
            eyedropperButton.onClick.AddListener(() => brush.SetEyedropper(!brush.EyedropperActive));
            symmetryButton.onClick.AddListener(() => brush.SetSymmetry(!brush.SymmetryActive));
            pickedButton.onClick.AddListener(brush.SelectPickedColor);
            ShowOwnedTools();
            brush.ToolAdded += OnToolAdded;

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
            brush.ToolAdded -= OnToolAdded;
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

        void ShowOwnedTools()
        {
            eyedropperButton.gameObject.SetActive(brush.HasTool(PaintTool.Eyedropper));
            symmetryButton.gameObject.SetActive(brush.HasTool(PaintTool.Symmetry));
        }

        void OnToolAdded(PaintTool _) => ShowOwnedTools();

        void AddSwatch(PigmentDefinition pigment)
        {
            var swatch = Instantiate(swatchTemplate, swatchContainer);
            swatch.name = $"Swatch_{pigment.Id}";
            swatch.gameObject.SetActive(true);
            swatch.image.color = pigment.Color;
            swatch.onClick.AddListener(() => brush.SelectPigment(pigment));
            swatchHighlights[pigment] = swatch.GetComponent<Outline>();
            swatchAmounts[pigment] = swatch.transform.Find("Amount").GetComponent<Text>();
            swatch.transform.Find("NameStrip/Name").GetComponent<Text>().text = pigment.DisplayName;
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
            RefreshZoneLegend();
        }

        void OnDisable() => brush.ToolsChanged -= Refresh;

        void Refresh()
        {
            bool picked = brush.PickedColor.HasValue;
            foreach (var pair in swatchHighlights)
                pair.Value.enabled = !brush.EraserActive && !picked && pair.Key == brush.SelectedPigment;
            foreach (var pair in brushHighlights)
                pair.Value.enabled = pair.Key == brush.SelectedBrush;
            eraserHighlight.enabled = brush.EraserActive;
            eyedropperHighlight.enabled = brush.EyedropperActive;
            symmetryHighlight.enabled = brush.SymmetryActive;
            pickedButton.gameObject.SetActive(picked);
            if (picked)
                pickedButton.image.color = brush.PickedColor.Value;
            pickedHighlight.enabled = picked && !brush.EraserActive;
            guideHighlight.enabled = brush.ShowGuide;
            hintsHighlight.enabled = brush.ShowColorHints;
            currentColorLabel.text = CurrentColorText(picked);
            sizeSlider.maxValue = brush.MaxBrushRadius; // depende de la resolución del lienzo activo
            sizeSlider.SetValueWithoutNotify(brush.BrushRadius);
        }

        string CurrentColorText(bool picked)
        {
            if (brush.EraserActive) return "Eraser";
            if (brush.EyedropperActive) return "Eyedropper: click on paint";
            if (picked) return "Color: Picked";
            return brush.SelectedPigment != null ? $"Color: {brush.SelectedPigment.DisplayName}" : "Color: None";
        }

        /// <summary>La plantilla solo cambia entre sesiones de pintura, así que basta actualizarla al mostrarse el panel.</summary>
        void RefreshZoneLegend()
        {
            var parts = new List<string>();
            var canvas = paintMode.ActiveCanvas;
            if (canvas != null && canvas.Crop != null)
            {
                foreach (var zone in canvas.Crop.Template.Zones)
                {
                    if (zone.suggestedPigment != null)
                        parts.Add($"{zone.zoneName} — {zone.suggestedPigment.DisplayName}");
                }
            }
            zoneLegendLabel.text = string.Join("  ·  ", parts);
            zoneLegendRoot.SetActive(parts.Count > 0);
        }
    }
}
