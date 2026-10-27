using System.Collections.Generic;
using TheLivingCanvas.Core;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// Avisos breves arriba a la derecha: tarjetas pintadas que entran deslizándose, esperan y se desvanecen.
    /// API estática (<see cref="Show"/>): no hace nada si la escena no tiene Notifications. Repetir el mismo texto
    /// mientras sigue en pantalla solo renueva su tiempo. Con Reduced Motion no se deslizan.
    /// </summary>
    public class Notifications : MonoBehaviour
    {
        public enum Kind { Info, Reward, Place, Saved }

        const int MaxVisible = 4;
        const float Width = 560f, Height = 78f, Gap = 12f, SlideSeconds = 0.35f, FadeSeconds = 0.5f, SlideDistance = 90f;
        const float TopMargin = 70f, RightMargin = 60f, DefaultSeconds = 4.5f;

        public static Notifications Instance { get; private set; }

        class Toast
        {
            public RectTransform Rect;
            public CanvasGroup Group;
            public TextMeshProUGUI Label;
            public string Text;
            public float Born, Life;
            public float Y;
            public bool Leaving;
        }

        readonly List<Toast> toasts = new List<Toast>();
        Transform root;

        void Awake()
        {
            Instance = this;
            var canvas = UIFactory.Canvas("NotificationCanvas", 250);
            canvas.transform.SetParent(transform, false);
            root = canvas.transform;
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        /// <summary>Muestra un aviso. <paramref name="seconds"/> &lt;= 0 usa el tiempo por defecto.</summary>
        public static void Show(string text, Kind kind = Kind.Info, float seconds = 0f)
        {
            if (Instance != null) Instance.Add(text, kind, seconds > 0f ? seconds : (kind == Kind.Saved ? 2.2f : DefaultSeconds));
        }

        void Add(string text, Kind kind, float life)
        {
            foreach (var existing in toasts)
                if (!existing.Leaving && existing.Text == text) { existing.Born = Time.unscaledTime; existing.Life = life; return; }

            var t = UITheme.Current;
            bool quiet = kind == Kind.Saved;
            var panel = UIFactory.Panel("Toast", root, new Vector2(quiet ? 300f : Width, quiet ? 56f : Height));
            panel.raycastTarget = false;
            var rect = panel.rectTransform;
            UIFactory.Place(rect, new Vector2(1, 1), new Vector2(1, 1), new Vector2(-RightMargin, -TopMargin), rect.sizeDelta);

            // Nota de papel: tarjeta crema con texto de tinta; el tipo se marca con una pincelada distinta.
            if (t.card != null) { panel.sprite = t.card; panel.type = Image.Type.Sliced; panel.color = Color.white; }
            else panel.color = t.Paper;

            var mark = UIFactory.Rect("Mark", rect);
            UIFactory.Place(mark, new Vector2(0, .5f), new Vector2(.5f, .5f), new Vector2(quiet ? 34 : 42, 0), new Vector2(quiet ? 22 : 34, quiet ? 22 : 34));
            var markImg = mark.gameObject.AddComponent<Image>();
            markImg.sprite = KindSprite(kind);
            markImg.color = KindColor(kind);
            markImg.raycastTarget = false;
            mark.localRotation = Quaternion.Euler(0, 0, kind == Kind.Place ? -12f : 8f);

            var label = UIFactory.Label("Text", rect, text, quiet ? UIFactory.TextStyle.Small : UIFactory.TextStyle.Body, TextAlignmentOptions.Left);
            label.color = t.TextOnPaper;
            UIFactory.ContrastOnPaint(label, 0.1f);
            UIFactory.Stretch(label.rectTransform);
            label.rectTransform.offsetMin = new Vector2(quiet ? 58 : 76, 4);
            label.rectTransform.offsetMax = new Vector2(-28, -4);
            label.enableAutoSizing = true;
            label.fontSizeMax = label.fontSize; label.fontSizeMin = label.fontSize * .7f;

            var group = rect.gameObject.AddComponent<CanvasGroup>();
            group.alpha = 0f;
            toasts.Add(new Toast { Rect = rect, Group = group, Label = label, Text = text, Born = Time.unscaledTime, Life = life });
            while (CountActive() > MaxVisible) ExpireOldest();
        }

        static Sprite KindSprite(Kind kind)
        {
            switch (kind)
            {
                case Kind.Reward: return BrushStrokes.Blot(3);
                case Kind.Place: return BrushStrokes.Dab(2, 160, 112);
                case Kind.Saved: return BrushStrokes.Blot(5);
                default: return BrushStrokes.Ring(2);
            }
        }

        static Color KindColor(Kind kind)
        {
            var t = UITheme.Current;
            switch (kind)
            {
                case Kind.Reward: return t.warmYellow;
                case Kind.Place: return t.olive;
                case Kind.Saved: return UITheme.A(t.greyBlue, .8f);
                default: return t.Info;
            }
        }

        int CountActive()
        {
            int n = 0;
            foreach (var x in toasts) if (!x.Leaving) n++;
            return n;
        }

        void ExpireOldest()
        {
            foreach (var x in toasts)
                if (!x.Leaving) { x.Leaving = true; x.Born = Time.unscaledTime; return; }
        }

        void Update()
        {
            float now = Time.unscaledTime;
            bool reduced = GameSettings.ReducedMotion;
            float y = 0f;
            for (int i = 0; i < toasts.Count; i++)
            {
                var x = toasts[i];
                float age = now - x.Born;
                if (!x.Leaving && age >= x.Life) { x.Leaving = true; x.Born = now; age = 0f; }

                float alpha, slide;
                if (x.Leaving)
                {
                    alpha = 1f - Mathf.Clamp01(age / FadeSeconds);
                    slide = 1f;
                    if (alpha <= 0f) { Destroy(x.Rect.gameObject); toasts.RemoveAt(i--); continue; }
                }
                else
                {
                    float enter = Mathf.Clamp01(age / SlideSeconds);
                    alpha = enter;
                    slide = 1f - (1f - enter) * (1f - enter) * (reduced ? 0f : 1f);
                }

                x.Group.alpha = alpha;
                // Se apilan hacia abajo; el hueco se cierra suavemente cuando uno se va.
                x.Y = Mathf.Lerp(x.Y, y, reduced ? 1f : 1f - Mathf.Exp(-12f * Time.unscaledDeltaTime));
                float offset = reduced ? 0f : (1f - slide) * SlideDistance;
                x.Rect.anchoredPosition = new Vector2(-RightMargin + offset, -TopMargin - x.Y);
                y += x.Rect.sizeDelta.y + Gap;
            }
        }
    }
}
