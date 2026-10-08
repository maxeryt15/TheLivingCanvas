using System.Collections.Generic;
using TheLivingCanvas.Data;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Paleta lateral del modo pintura: una muestra por pigmento (generadas desde la paleta del
    /// pincel), tamaño del pincel y borrador. Refleja el estado de PaintBrushController.
    /// </summary>
    public class PaintToolsUI : MonoBehaviour
    {
        [SerializeField] PaintBrushController brush;
        [SerializeField] RectTransform swatchContainer;
        [Tooltip("Botón de muestra desactivado que se clona por cada pigmento.")]
        [SerializeField] Button swatchTemplate;
        [SerializeField] Slider sizeSlider;
        [SerializeField] Button eraserButton;

        readonly Dictionary<PigmentDefinition, Outline> swatchHighlights = new();
        Outline eraserHighlight;

        void Awake()
        {
            swatchTemplate.gameObject.SetActive(false);
            foreach (var pigment in brush.Palette)
            {
                var swatch = Instantiate(swatchTemplate, swatchContainer);
                swatch.name = $"Swatch_{pigment.Id}";
                swatch.gameObject.SetActive(true);
                swatch.image.color = pigment.Color;
                swatch.onClick.AddListener(() => brush.SelectPigment(pigment));
                swatchHighlights[pigment] = swatch.GetComponent<Outline>();
            }

            eraserHighlight = eraserButton.GetComponent<Outline>();
            eraserButton.onClick.AddListener(() => brush.SetEraser(!brush.EraserActive));

            sizeSlider.minValue = brush.MinBrushRadius;
            sizeSlider.maxValue = brush.MaxBrushRadius;
            sizeSlider.onValueChanged.AddListener(brush.SetBrushRadius);
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
            eraserHighlight.enabled = brush.EraserActive;
            sizeSlider.SetValueWithoutNotify(brush.BrushRadius);
        }
    }
}
