using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Ui
{
    /// <summary>Crea los componentes base de la interfaz con el UITheme actual (runtime y editor).</summary>
    public static class UIFactory
    {
        public static RectTransform Rect(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            return (RectTransform)go.transform;
        }

        public static void Stretch(RectTransform r)
        {
            r.anchorMin = Vector2.zero; r.anchorMax = Vector2.one;
            r.offsetMin = Vector2.zero; r.offsetMax = Vector2.zero;
        }

        public static void Place(RectTransform r, Vector2 anchor, Vector2 pivot, Vector2 pos, Vector2 size)
        {
            r.anchorMin = r.anchorMax = anchor; r.pivot = pivot;
            r.anchoredPosition = pos; r.sizeDelta = size;
        }

        public static Canvas Canvas(string name, int sortingOrder = 0)
        {
            var go = new GameObject(name, typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            var c = go.GetComponent<Canvas>();
            c.renderMode = RenderMode.ScreenSpaceOverlay;
            c.sortingOrder = sortingOrder;
            var s = go.GetComponent<CanvasScaler>();
            s.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            s.referenceResolution = new Vector2(1920, 1080);
            s.matchWidthOrHeight = 0.5f;
            go.AddComponent<Core.UiScaleApplier>();
            return c;
        }

        static Sprite dot;

        /// <summary>Círculo blanco suave (placeholder de la mira hasta tener sprite pintado).</summary>
        public static Sprite DotSprite()
        {
            if (dot != null) return dot;
            const int n = 32;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp };
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float d = Vector2.Distance(new Vector2(x + .5f, y + .5f), new Vector2(n / 2f, n / 2f));
                    tex.SetPixel(x, y, new Color(1, 1, 1, Mathf.Clamp01(n / 2f - d)));
                }
            tex.Apply();
            dot = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(.5f, .5f), 100f);
            return dot;
        }

        static Sprite glow;

        /// <summary>Resplandor radial suave (alfa decrece del centro al borde); se tiñe con Image.color.</summary>
        public static Sprite GlowSprite()
        {
            if (glow != null) return glow;
            const int n = 64;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp };
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float d = Vector2.Distance(new Vector2(x + .5f, y + .5f), new Vector2(n / 2f, n / 2f)) / (n / 2f);
                    float a = Mathf.Clamp01(1f - d);
                    tex.SetPixel(x, y, new Color(1, 1, 1, a * a));
                }
            tex.Apply();
            glow = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(.5f, .5f), 100f);
            return glow;
        }

        public static Image Panel(string name, Transform parent, Vector2 size)
        {
            var t = UITheme.Current;
            var r = Rect(name, parent);
            r.sizeDelta = size;
            var img = r.gameObject.AddComponent<Image>();
            img.sprite = t.panel;
            img.type = t.panel != null ? Image.Type.Sliced : Image.Type.Simple;
            img.color = t.panel != null ? Color.white : t.PanelTint;
            return img;
        }

        public enum TextStyle { Title, Heading, Body, Small }

        public static TextMeshProUGUI Label(string name, Transform parent, string text, TextStyle style = TextStyle.Body,
            TextAlignmentOptions align = TextAlignmentOptions.Center)
        {
            var t = UITheme.Current;
            var r = Rect(name, parent);
            var tmp = r.gameObject.AddComponent<TextMeshProUGUI>();
            tmp.text = text;
            tmp.alignment = align;
            tmp.color = t.cream;
            tmp.raycastTarget = false;
            tmp.textWrappingMode = TextWrappingModes.Normal;
            switch (style)
            {
                case TextStyle.Title: tmp.font = t.Title ?? tmp.font; tmp.fontSize = t.titleSize; break;
                case TextStyle.Heading: tmp.font = t.Title ?? tmp.font; tmp.fontSize = t.headingSize; break;
                case TextStyle.Small: if (t.bodyFont != null) tmp.font = t.bodyFont; tmp.fontSize = t.smallSize; break;
                default: if (t.bodyFont != null) tmp.font = t.bodyFont; tmp.fontSize = t.bodySize; break;
            }
            return tmp;
        }

        /// <summary>
        /// Contraste para texto sobre una textura pintada (siempre hace falta): contorno de tinta oscura para texto claro,
        /// o crema para texto oscuro, más una sombra suave. Regla de la UI: ningún texto va sobre pintura sin esto.
        /// </summary>
        public static void ContrastOnPaint(TextMeshProUGUI tmp, float outline = 0.22f)
        {
            var t = UITheme.Current;
            bool lightText = tmp.color.grayscale > 0.5f;
            tmp.outlineWidth = outline;
            tmp.outlineColor = lightText ? (Color32)new Color(t.ink.r * .6f, t.ink.g * .6f, t.ink.b * .6f) : (Color32)new Color(.97f, .93f, .8f);
            if (tmp.GetComponent<Shadow>() == null)
                tmp.gameObject.AddComponent<Shadow>().effectColor = new Color(0, 0, 0, .6f);
        }

        public static Button Button(string name, Transform parent, string label, Vector2 size)
        {
            var t = UITheme.Current;
            var r = Rect(name, parent);
            r.sizeDelta = size;
            var img = r.gameObject.AddComponent<Image>();
            img.sprite = t.buttonNormal;
            img.type = t.buttonNormal != null ? Image.Type.Sliced : Image.Type.Simple;
            img.color = t.buttonNormal != null ? Color.white : t.cerulean;
            var b = r.gameObject.AddComponent<Button>();
            b.targetGraphic = img;
            if (t.buttonNormal != null)
            {
                b.transition = Selectable.Transition.SpriteSwap;
                b.spriteState = new SpriteState
                {
                    highlightedSprite = t.buttonHover, selectedSprite = t.buttonHover,
                    pressedSprite = t.buttonPressed, disabledSprite = t.buttonDisabled
                };
            }
            else
            {
                b.transition = Selectable.Transition.ColorTint;
                b.colors = new ColorBlock
                {
                    normalColor = Color.white, highlightedColor = Color.Lerp(Color.white, t.warmYellow, 0.55f),
                    selectedColor = Color.Lerp(Color.white, t.warmYellow, 0.55f), pressedColor = new Color(.7f, .7f, .7f),
                    disabledColor = new Color(1, 1, 1, .4f), colorMultiplier = 1f, fadeDuration = t.buttonFade
                };
            }
            var l = Label("Label", r, label, TextStyle.Body);
            Stretch(l.rectTransform);
            return b;
        }

        public static Slider Slider(string name, Transform parent, Vector2 size, float min, float max, float value)
        {
            var t = UITheme.Current;
            var r = Rect(name, parent);
            r.sizeDelta = size;
            var back = Rect("Background", r);
            Stretch(back);
            var bi = back.gameObject.AddComponent<Image>();
            bi.sprite = t.barBack; bi.type = t.barBack != null ? Image.Type.Sliced : Image.Type.Simple;
            bi.color = t.barBack != null ? Color.white : new Color(t.ink.r, t.ink.g, t.ink.b, .7f);
            var area = Rect("Fill Area", r);
            Stretch(area);
            var fill = Rect("Fill", area);
            fill.sizeDelta = Vector2.zero;
            var fi = fill.gameObject.AddComponent<Image>();
            fi.sprite = t.barFill; fi.type = t.barFill != null ? Image.Type.Sliced : Image.Type.Simple;
            fi.color = t.barFill != null ? Color.white : t.warmYellow;
            var handleArea = Rect("Handle Slide Area", r);
            Stretch(handleArea);
            var handle = Rect("Handle", handleArea);
            handle.sizeDelta = new Vector2(size.y * 1.4f, size.y * 1.4f);
            var hi = handle.gameObject.AddComponent<Image>();
            hi.color = t.cream;
            var s = r.gameObject.AddComponent<Slider>();
            s.fillRect = fill; s.handleRect = handle; s.targetGraphic = hi;
            s.minValue = min; s.maxValue = max; s.value = value;
            return s;
        }

        public static Toggle Toggle(string name, Transform parent, string label, bool value)
        {
            var t = UITheme.Current;
            var r = Rect(name, parent);
            r.sizeDelta = new Vector2(420, 48);
            var box = Rect("Box", r);
            Place(box, new Vector2(0, .5f), new Vector2(0, .5f), Vector2.zero, new Vector2(40, 40));
            var bg = box.gameObject.AddComponent<Image>();
            bg.color = new Color(t.ink.r, t.ink.g, t.ink.b, .9f);
            var frame = box.gameObject.AddComponent<Outline>();
            frame.effectColor = t.cream;
            frame.effectDistance = new Vector2(3, 3);
            var check = Rect("Check", box);
            Stretch(check);
            check.offsetMin = new Vector2(6, 6); check.offsetMax = new Vector2(-6, -6);
            var ci = check.gameObject.AddComponent<Image>();
            ci.color = t.warmYellow;
            var l = Label("Label", r, label, TextStyle.Body, TextAlignmentOptions.Left);
            Stretch(l.rectTransform);
            l.rectTransform.offsetMin = new Vector2(56, 0);
            var tg = r.gameObject.AddComponent<Toggle>();
            tg.targetGraphic = bg; tg.graphic = ci; tg.isOn = value;
            return tg;
        }
    }
}
