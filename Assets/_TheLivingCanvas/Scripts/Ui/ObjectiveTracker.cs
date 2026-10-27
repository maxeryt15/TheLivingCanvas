using System.Collections.Generic;
using TheLivingCanvas.Core;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// Objetivos activos en una esquina (arriba a la izquierda): un encabezado discreto y hasta tres líneas.
    /// Al cumplir uno se marca con un tilde un momento, avisa y desaparece. Sin objetivos no se ve nada.
    /// API estática: <see cref="Set"/> añade o cambia el texto, <see cref="Complete"/> lo cumple, <see cref="Remove"/> lo quita.
    /// Es solo el mostrador: qué objetivos hay y cuándo se cumplen lo decide la historia (aún no definida).
    /// </summary>
    public class ObjectiveTracker : MonoBehaviour
    {
        const int MaxShown = 3;
        const float CompleteHold = 2.2f, FadeSeconds = 0.4f, Left = 60f, Top = 70f, LineHeight = 48f, Width = 640f;

        public static ObjectiveTracker Instance { get; private set; }

        class Entry
        {
            public string Id, Text;
            public bool Done;
            public float DoneAt;
            public TextMeshProUGUI Label;
            public float Alpha;
        }

        readonly List<Entry> entries = new List<Entry>();
        CanvasGroup group;
        TextMeshProUGUI header;
        RectTransform listRoot;

        void Awake()
        {
            Instance = this;
            Build();
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        // ---------- API ----------

        public static void Set(string id, string text) => Instance?.SetEntry(id, text);
        public static void Complete(string id) => Instance?.CompleteEntry(id);
        public static void Remove(string id) => Instance?.RemoveEntry(id);

        void SetEntry(string id, string text)
        {
            var e = Find(id);
            if (e == null)
            {
                e = new Entry { Id = id };
                var l = UIFactory.Label("Objective_" + id, listRoot, "", UIFactory.TextStyle.Body, TextAlignmentOptions.Left);
                UIFactory.ContrastOnPaint(l, 0.45f);
                l.outlineColor = UITheme.Current.OutlineDark;
                UIFactory.Place(l.rectTransform, new Vector2(0, 1), new Vector2(0, 1), Vector2.zero, new Vector2(Width, LineHeight));
                e.Label = l;
                entries.Add(e);
                Notifications.Show("New objective: " + text, Notifications.Kind.Info);
            }
            e.Text = text;
            e.Done = false;
        }

        void CompleteEntry(string id)
        {
            var e = Find(id);
            if (e == null || e.Done) return;
            e.Done = true;
            e.DoneAt = Time.unscaledTime;
            Notifications.Show("Objective complete: " + e.Text, Notifications.Kind.Reward);
        }

        void RemoveEntry(string id)
        {
            var e = Find(id);
            if (e == null) return;
            Destroy(e.Label.gameObject);
            entries.Remove(e);
        }

        Entry Find(string id) => entries.Find(x => x.Id == id);

        // ---------- Bucle ----------

        void Update()
        {
            float dt = Time.unscaledDeltaTime;
            for (int i = entries.Count - 1; i >= 0; i--)
                if (entries[i].Done && Time.unscaledTime - entries[i].DoneAt > CompleteHold + FadeSeconds) RemoveEntry(entries[i].Id);

            // Se oculta al abrir la pausa o mientras habla un personaje, para no competir con la caja.
            bool hide = entries.Count == 0 || (DialogueBox.Instance != null && DialogueBox.Instance.IsOpen);
            group.alpha = Mathf.MoveTowards(group.alpha, hide ? 0f : 1f, dt / 0.25f);

            float y = 0f;
            int shown = 0;
            var t = UITheme.Current;
            foreach (var e in entries)
            {
                bool visible = shown < MaxShown;
                if (visible) shown++;
                float fade = e.Done ? 1f - Mathf.Clamp01((Time.unscaledTime - e.DoneAt - CompleteHold) / FadeSeconds) : 1f;
                e.Alpha = Mathf.MoveTowards(e.Alpha, visible ? fade : 0f, dt / 0.25f);
                e.Label.alpha = e.Alpha;
                e.Label.text = e.Done ? "<s>" + e.Text + "</s>" : e.Text;
                e.Label.color = e.Done ? new Color(t.olive.r * 1.4f, t.olive.g * 1.5f, t.olive.b * 1.3f, e.Alpha) : UITheme.A(t.cream, e.Alpha);
                e.Label.rectTransform.anchoredPosition = new Vector2(0, -y);
                if (visible) y += LineHeight;
            }
            header.gameObject.SetActive(entries.Count > 0);
        }

        // ---------- Construcción ----------

        void Build()
        {
            var t = UITheme.Current;
            var canvas = UIFactory.Canvas("ObjectiveCanvas", 240);
            canvas.transform.SetParent(transform, false);
            var area = UIFactory.Rect("Area", canvas.transform);
            UIFactory.Place(area, new Vector2(0, 1), new Vector2(0, 1), new Vector2(Left, -Top), new Vector2(Width, 220));
            group = area.gameObject.AddComponent<CanvasGroup>();
            group.alpha = 0f;
            group.blocksRaycasts = false;

            // Velo de tinta tras la lista: se lee sobre muros claros
            var back = UIFactory.Rect("Backing", area);
            UIFactory.Place(back, new Vector2(0, 1), new Vector2(0, 1), new Vector2(-24, 18), new Vector2(Width + 60, 170));
            var backImg = back.gameObject.AddComponent<Image>();
            backImg.sprite = t.tooltip; backImg.type = t.tooltip != null ? Image.Type.Sliced : Image.Type.Simple; backImg.color = t.tooltip != null ? new Color(1, 1, 1, .62f) : t.Shade(.6f); backImg.raycastTarget = false;

            header = UIFactory.Label("Header", area, "OBJECTIVES", UIFactory.TextStyle.Small, TextAlignmentOptions.Left);
            header.characterSpacing = 8f;
            header.color = UITheme.A(t.warmYellow, .9f);
            UIFactory.ContrastOnPaint(header, 0.45f);
            header.outlineColor = UITheme.Current.OutlineDark;
            UIFactory.Place(header.rectTransform, new Vector2(0, 1), new Vector2(0, 1), Vector2.zero, new Vector2(Width, 30));

            // Subrayado de pincel bajo el encabezado
            var ul = UIFactory.Rect("HeaderStroke", area);
            UIFactory.Place(ul, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, -30), new Vector2(Width * .8f, 16));
            var ui = ul.gameObject.AddComponent<Image>();
            ui.sprite = BrushStrokes.Stroke(9, 512, 48); ui.color = UITheme.A(t.warmYellow, .7f); ui.raycastTarget = false;

            listRoot = UIFactory.Rect("List", area);
            UIFactory.Place(listRoot, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, -38), new Vector2(Width, 180));
        }
    }
}
