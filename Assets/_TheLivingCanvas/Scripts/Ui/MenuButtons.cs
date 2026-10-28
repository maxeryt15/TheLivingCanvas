using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// Botón de menú sin caja (menú principal y pausa): solo texto; al pasar el ratón o seleccionarlo, un trazo pintado
    /// se desvanece detrás. Comparte el aspecto entre pantallas.
    /// </summary>
    public static class MenuButtons
    {
        public static Button Create(string label, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, TextAlignmentOptions align, UnityEngine.Events.UnityAction onClick)
        {
            var t = UITheme.Current;
            var r = UIFactory.Rect(label + "Button", parent);
            UIFactory.Place(r, anchor, anchor, pos, size);
            var stroke = r.gameObject.AddComponent<Image>();
            stroke.sprite = t.promptStroke;
            stroke.type = Image.Type.Simple;
            stroke.color = t.promptStroke != null ? Color.white : t.cerulean;
            var b = r.gameObject.AddComponent<Button>();
            b.targetGraphic = stroke;
            b.transition = Selectable.Transition.ColorTint;
            b.colors = new ColorBlock
            {
                normalColor = new Color(1, 1, 1, 0), highlightedColor = new Color(1, 1, 1, .9f), selectedColor = new Color(1, 1, 1, .9f),
                pressedColor = new Color(.8f, .8f, .8f, 1f), disabledColor = new Color(1, 1, 1, 0), colorMultiplier = 1f, fadeDuration = .18f
            };
            var l = UIFactory.Label("Label", r, label, UIFactory.TextStyle.Heading, align);
            UIFactory.ContrastOnPaint(l, 0.4f);
            l.outlineColor = t.OutlineDark;
            UIFactory.Stretch(l.rectTransform);
            if (align == TextAlignmentOptions.Left) l.rectTransform.offsetMin = new Vector2(44, 0);
            r.gameObject.AddComponent<UIButtonSound>();
            b.onClick.AddListener(onClick);
            return b;
        }
    }
}
