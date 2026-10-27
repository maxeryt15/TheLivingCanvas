using System;
using System.Collections.Generic;
using System.Linq;
using TheLivingCanvas.Core;
using TMPro;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// Panel de ajustes compartido por el menú principal y la pausa, repartido en pestañas
    /// (Audio, Video, Gameplay, Accessibility). Guarda todo en GameSettings. Sin lógica de escena:
    /// quien lo abre decide qué hacer con la sensibilidad (la pausa la aplica a la cámara) y con "Back".
    /// </summary>
    public class SettingsPanel
    {
        const float RowStart = 196f, RowStep = 78f;

        public GameObject Root { get; private set; }
        /// <summary>Primer control seleccionable (para mando/teclado al abrir).</summary>
        public Selectable First { get; private set; }
        public Selectable Back { get; private set; }

        readonly List<GameObject> pages = new List<GameObject>();
        readonly List<Button> tabs = new List<Button>();

        public static SettingsPanel Create(Transform parent, UnityAction onBack, Action<float> onSensitivity = null)
        {
            var s = new SettingsPanel();
            s.Build(parent, onBack, onSensitivity);
            return s;
        }

        void Build(Transform parent, UnityAction onBack, Action<float> onSensitivity)
        {
            var size = new Vector2(1000, 780);
            var p = UIFactory.Panel("SettingsPanel", parent, size);
            UIFactory.Place(p.rectTransform, new Vector2(.5f, .5f), new Vector2(.5f, .5f), Vector2.zero, size);
            Root = p.gameObject;
            var title = UIFactory.Label("Title", p.transform, "Settings", UIFactory.TextStyle.Heading);
            UIFactory.Place(title.rectTransform, new Vector2(.5f, 1), new Vector2(.5f, 1), new Vector2(0, -36), new Vector2(700, 70));

            BuildAudio(Page(p.transform, "Audio"));
            BuildVideo(Page(p.transform, "Video"));
            BuildGameplay(Page(p.transform, "Gameplay"), onSensitivity);
            BuildAccessibility(Page(p.transform, "Accessibility"));
            for (int i = 0; i < pages.Count; i++)
            {
                int index = i;
                var tab = UIFactory.Button(pages[i].name + "Tab", p.transform, pages[i].name, new Vector2(210, 56));
                UIFactory.Place((RectTransform)tab.transform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(55 + i * 225, -102), new Vector2(210, 56));
                tab.onClick.AddListener(() => Show(index));
                tabs.Add(tab);
            }

            var back = UIFactory.Button("BackButton", p.transform, "Back", new Vector2(320, 68));
            UIFactory.Place((RectTransform)back.transform, new Vector2(.5f, 0), new Vector2(.5f, 0), new Vector2(0, 36), new Vector2(320, 68));
            back.onClick.AddListener(onBack);
            Back = back;
            Show(0);
            First = tabs[0];
            Root.SetActive(false);
        }

        // ---------- Pestañas ----------

        RectTransform Page(Transform parent, string name)
        {
            var r = UIFactory.Rect(name, parent);
            UIFactory.Stretch(r);
            pages.Add(r.gameObject);
            return r;
        }

        void Show(int index)
        {
            for (int i = 0; i < pages.Count; i++)
            {
                pages[i].SetActive(i == index);
                var img = tabs[i].targetGraphic as Graphic;
                if (img != null) img.canvasRenderer.SetAlpha(i == index ? 1f : 0.55f);
            }
        }

        static float Y(int row) => RowStart + row * RowStep;

        // ---------- Contenido ----------

        static void BuildAudio(Transform page)
        {
            PercentRow(page, "Master volume", GameSettings.Volume, v => GameSettings.Volume = v, Y(0));
            PercentRow(page, "Music", GameSettings.MusicVolume, v => GameSettings.MusicVolume = v, Y(1));
            PercentRow(page, "Sound effects", GameSettings.SfxVolume, v => GameSettings.SfxVolume = v, Y(2));
        }

        static void BuildVideo(Transform page)
        {
            var modes = Resolutions();
            var names = modes.Select(m => m.x + " x " + m.y).ToArray();
            var saved = GameSettings.ResolutionSaved;
            int current = Mathf.Max(0, modes.FindIndex(m => m == saved));
            if (!modes.Contains(saved)) current = Mathf.Max(0, modes.FindIndex(m => m.x == Screen.width && m.y == Screen.height));
            SelectorRow(page, "Resolution", names, current, i => GameSettings.SetResolution(modes[i].x, modes[i].y), Y(0));
            ToggleRow(page, "Fullscreen", GameSettings.Fullscreen, v => GameSettings.Fullscreen = v, Y(1));
            ToggleRow(page, "VSync", GameSettings.VSync, v => GameSettings.VSync = v, Y(2));
            SelectorRow(page, "Quality", QualitySettings.names, GameSettings.Quality, i => GameSettings.Quality = i, Y(3));
            var ui = SliderRow(page, "Interface size", GameSettings.UiScale, GameSettings.MinUiScale, GameSettings.MaxUiScale, null, Y(4));
            // El tamaño de la interfaz se aplica al soltar, no mientras se arrastra (redimensionaría el slider bajo el cursor).
            var trigger = ui.gameObject.AddComponent<EventTrigger>();
            foreach (var type in new[] { EventTriggerType.PointerUp, EventTriggerType.Submit })
            {
                var e = new EventTrigger.Entry { eventID = type };
                e.callback.AddListener(_ => GameSettings.UiScale = ui.value);
                trigger.triggers.Add(e);
            }
        }

        static void BuildGameplay(Transform page, Action<float> onSensitivity)
        {
            SliderRow(page, "Look sensitivity", GameSettings.Sensitivity, GameSettings.MinSensitivity, GameSettings.MaxSensitivity,
                v => { GameSettings.Sensitivity = v; onSensitivity?.Invoke(v); }, Y(0));
            ToggleRow(page, "Invert vertical look", GameSettings.InvertY, v => GameSettings.InvertY = v, Y(1));
        }

        static void BuildAccessibility(Transform page)
        {
            ToggleRow(page, "Subtitles", GameSettings.Subtitles, v => GameSettings.Subtitles = v, Y(0));
            ToggleRow(page, "Reduced motion", GameSettings.ReducedMotion, v => GameSettings.ReducedMotion = v, Y(1));
            ToggleRow(page, "High contrast text", GameSettings.HighContrastText, v => GameSettings.HighContrastText = v, Y(2));
        }

        /// <summary>Resoluciones distintas (sin repetir por tasa de refresco), de 1024x576 hacia arriba, ascendentes.</summary>
        static List<Vector2Int> Resolutions()
        {
            var list = Screen.resolutions.Select(r => new Vector2Int(r.width, r.height))
                .Where(r => r.x >= 1024 && r.y >= 576).Distinct().OrderBy(r => r.x).ThenBy(r => r.y).ToList();
            var now = new Vector2Int(Screen.width, Screen.height);
            if (list.Count == 0 || !list.Contains(now)) { list.Add(now); list = list.OrderBy(r => r.x).ThenBy(r => r.y).ToList(); }
            return list;
        }

        // ---------- Filas ----------

        static TextMeshProUGUI RowLabel(Transform parent, string label, float y)
        {
            var l = UIFactory.Label(label + "Label", parent, label, UIFactory.TextStyle.Body, TextAlignmentOptions.Left);
            UIFactory.Place(l.rectTransform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(70, -y), new Vector2(380, 48));
            return l;
        }

        static Slider SliderRow(Transform parent, string label, float value, float min, float max, UnityAction<float> onChange, float y, float width = 400)
        {
            RowLabel(parent, label, y);
            var s = UIFactory.Slider(label + "Slider", parent, new Vector2(width, 24), min, max, value);
            UIFactory.Place((RectTransform)s.transform, new Vector2(1, 1), new Vector2(1, 1), new Vector2(-70 - (400 - width), -y - 12), new Vector2(width, 24));
            if (onChange != null) s.onValueChanged.AddListener(onChange);
            return s;
        }

        /// <summary>Slider de 0 a 1 con el porcentaje escrito a la derecha.</summary>
        static void PercentRow(Transform parent, string label, float value, UnityAction<float> onChange, float y)
        {
            var s = SliderRow(parent, label, value, 0f, 1f, null, y, 310);
            var pct = UIFactory.Label(label + "Percent", parent, Mathf.RoundToInt(value * 100) + "%", UIFactory.TextStyle.Small, TextAlignmentOptions.Right);
            UIFactory.Place(pct.rectTransform, new Vector2(1, 1), new Vector2(1, 1), new Vector2(-70, -y), new Vector2(80, 48));
            s.onValueChanged.AddListener(v => { pct.text = Mathf.RoundToInt(v * 100) + "%"; onChange(v); });
        }

        static void ToggleRow(Transform parent, string label, bool value, UnityAction<bool> onChange, float y)
        {
            var tg = UIFactory.Toggle(label.Replace(" ", "") + "Toggle", parent, label, value);
            UIFactory.Place((RectTransform)tg.transform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(70, -y), new Vector2(520, 48));
            tg.onValueChanged.AddListener(onChange);
        }

        /// <summary>Selector con flechas: "&lt; valor &gt;". Da la vuelta al llegar al final.</summary>
        static void SelectorRow(Transform parent, string label, string[] options, int index, UnityAction<int> onChange, float y)
        {
            RowLabel(parent, label, y);
            int current = Mathf.Clamp(index, 0, options.Length - 1);
            var value = UIFactory.Label(label + "Value", parent, options[current], UIFactory.TextStyle.Body);
            UIFactory.Place(value.rectTransform, new Vector2(1, 1), new Vector2(1, 1), new Vector2(-136, -y), new Vector2(260, 48));
            void Step(int d)
            {
                current = (current + d + options.Length) % options.Length;
                value.text = options[current];
                onChange(current);
            }
            var left = UIFactory.Button(label + "Prev", parent, "<", new Vector2(56, 48));
            UIFactory.Place((RectTransform)left.transform, new Vector2(1, 1), new Vector2(1, 1), new Vector2(-406, -y), new Vector2(56, 48));
            left.onClick.AddListener(() => Step(-1));
            var right = UIFactory.Button(label + "Next", parent, ">", new Vector2(56, 48));
            UIFactory.Place((RectTransform)right.transform, new Vector2(1, 1), new Vector2(1, 1), new Vector2(-70, -y), new Vector2(56, 48));
            right.onClick.AddListener(() => Step(1));
        }
    }
}
