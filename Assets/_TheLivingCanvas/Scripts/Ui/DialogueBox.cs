using System;
using TheLivingCanvas.Core;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// Diálogo en primera persona: una caja pintada abajo con el nombre y una línea cada vez, escrita poco a poco.
    /// No libera el cursor ni para al jugador: se sigue mirando al personaje. E / Espacio / clic / A completan la línea y
    /// avanzan; Esc / B cierran. También muestra subtítulos sueltos (<see cref="ShowSubtitle"/>) si el ajuste está activo.
    /// Se construye por código al arrancar.
    /// </summary>
    public class DialogueBox : MonoBehaviour
    {
        const float CharsPerSecond = 55f, FadeSeconds = 0.18f, SubtitleMin = 2.5f, SubtitlePerChar = 0.055f;
        static readonly Vector2 BoxSize = new Vector2(1240, 250);

        public static DialogueBox Instance { get; private set; }
        /// <summary>Fotograma en que se cerró por última vez: la pausa no debe usar el mismo Esc.</summary>
        public static int ClosedFrame { get; private set; } = -1;

        CanvasGroup boxGroup, subtitleGroup;
        RectTransform subtitleRect;
        TextMeshProUGUI speakerLabel, lineLabel, hintLabel, subtitleLabel;
        string[] lines;
        int index, openedFrame = -1;
        float shown;
        Action onClosed;
        float boxAlpha, subtitleAlpha, subtitleUntil;

        public bool IsOpen { get; private set; }

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

        public void Open(string speaker, string[] dialogueLines, Action closed = null)
        {
            if (IsOpen || dialogueLines == null || dialogueLines.Length == 0) return;
            IsOpen = true;
            openedFrame = Time.frameCount;
            lines = dialogueLines;
            onClosed = closed;
            index = 0;
            speakerLabel.text = speaker;
            ShowLine();
            UIEvents.Play(UISound.OpenMenu);
        }

        public void Close()
        {
            if (!IsOpen) return;
            IsOpen = false;
            ClosedFrame = Time.frameCount;
            UIEvents.Play(UISound.CloseMenu);
            var callback = onClosed;
            onClosed = null;
            callback?.Invoke();
        }

        /// <summary>Línea suelta (sin pulsar nada) que desaparece sola. No hace nada si los subtítulos están apagados.</summary>
        public void ShowSubtitle(string speaker, string text, float seconds = 0f)
        {
            if (!GameSettings.Subtitles || string.IsNullOrEmpty(text)) return;
            subtitleLabel.text = string.IsNullOrEmpty(speaker) ? text : $"<color=#E8C25A>{speaker}:</color> {text}";
            subtitleUntil = Time.unscaledTime + (seconds > 0f ? seconds : Mathf.Max(SubtitleMin, text.Length * SubtitlePerChar));
        }

        // ---------- Bucle ----------

        void Update()
        {
            float dt = Time.unscaledDeltaTime;
            float fade = GameSettings.ReducedMotion ? 1f : dt / FadeSeconds;
            boxAlpha = Mathf.MoveTowards(boxAlpha, IsOpen ? 1f : 0f, fade);
            subtitleAlpha = Mathf.MoveTowards(subtitleAlpha, Time.unscaledTime < subtitleUntil ? 1f : 0f, fade);
            subtitleRect.anchoredPosition = new Vector2(0, IsOpen ? BoxSize.y + 90f : 50f); // sobre la caja si hay diálogo
            boxGroup.alpha = boxAlpha;
            subtitleGroup.alpha = subtitleAlpha;
            boxGroup.gameObject.SetActive(boxAlpha > 0f);
            subtitleGroup.gameObject.SetActive(subtitleAlpha > 0f);
            if (!IsOpen) return;

            int total = lineLabel.textInfo.characterCount;
            shown = GameSettings.ReducedMotion ? total : Mathf.Min(total, shown + CharsPerSecond * dt);
            lineLabel.maxVisibleCharacters = Mathf.FloorToInt(shown);
            bool done = shown >= total;
            hintLabel.gameObject.SetActive(done);
            if (done && !GameSettings.ReducedMotion)
                hintLabel.alpha = 0.65f + 0.35f * Mathf.Sin(Time.unscaledTime * 3f);

            if (Time.frameCount == openedFrame) return; // la pulsación de E que abre no avanza
            if (ClosePressed()) { Close(); return; }
            if (AdvancePressed())
            {
                if (!done) shown = total; // primero se completa la línea
                else Advance();
            }
        }

        static bool AdvancePressed() =>
            (Keyboard.current != null && (Keyboard.current.eKey.wasPressedThisFrame || Keyboard.current.spaceKey.wasPressedThisFrame
                                          || Keyboard.current.enterKey.wasPressedThisFrame))
            || (Mouse.current != null && Mouse.current.leftButton.wasPressedThisFrame)
            || (Gamepad.current != null && Gamepad.current.buttonSouth.wasPressedThisFrame);

        static bool ClosePressed() =>
            (Keyboard.current != null && Keyboard.current.escapeKey.wasPressedThisFrame)
            || (Gamepad.current != null && Gamepad.current.buttonEast.wasPressedThisFrame);

        void Advance()
        {
            if (index >= lines.Length - 1) { Close(); return; }
            index++;
            ShowLine();
            UIEvents.Play(UISound.PageTurn);
        }

        void ShowLine()
        {
            lineLabel.text = lines[index];
            lineLabel.ForceMeshUpdate();
            lineLabel.maxVisibleCharacters = 0;
            shown = 0f;
            hintLabel.text = index >= lines.Length - 1 ? "E   Close" : "E   Next";
        }

        // ---------- Construcción ----------

        void Build()
        {
            var t = UITheme.Current;
            var canvas = UIFactory.Canvas("DialogueCanvas", 300);
            canvas.transform.SetParent(transform, false);

            // Caja del diálogo
            var panel = UIFactory.Panel("Box", canvas.transform, BoxSize);
            UIFactory.Place(panel.rectTransform, new Vector2(.5f, 0), new Vector2(.5f, 0), new Vector2(0, 70), BoxSize);
            panel.raycastTarget = false;
            boxGroup = panel.gameObject.AddComponent<CanvasGroup>();
            boxGroup.interactable = false;
            boxGroup.blocksRaycasts = false;

            // Velo oscuro interior para que el texto se lea sobre el mundo (el marco pintado queda alrededor)
            var shade = UIFactory.Rect("Shade", panel.transform);
            UIFactory.Stretch(shade);
            shade.offsetMin = new Vector2(46, 46); shade.offsetMax = new Vector2(-46, -46);
            var shadeImg = shade.gameObject.AddComponent<Image>();
            shadeImg.color = new Color(t.ink.r * .5f, t.ink.g * .5f, t.ink.b * .6f, .6f);
            shadeImg.raycastTarget = false;

            speakerLabel = UIFactory.Label("Speaker", panel.transform, "", UIFactory.TextStyle.Heading, TextAlignmentOptions.Left);
            speakerLabel.color = t.warmYellow;
            UIFactory.ContrastOnPaint(speakerLabel, 0.3f);
            UIFactory.Place(speakerLabel.rectTransform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(70, -24), new Vector2(700, 64));

            lineLabel = UIFactory.Label("Line", panel.transform, "", UIFactory.TextStyle.Body, TextAlignmentOptions.TopLeft);
            lineLabel.fontSize = t.bodySize * 1.15f;
            UIFactory.ContrastOnPaint(lineLabel, 0.2f);
            UIFactory.Place(lineLabel.rectTransform, new Vector2(.5f, 1), new Vector2(.5f, 1), new Vector2(0, -92), new Vector2(BoxSize.x - 200, BoxSize.y - 150));

            hintLabel = UIFactory.Label("Hint", panel.transform, "E   Next", UIFactory.TextStyle.Small, TextAlignmentOptions.Right);
            UIFactory.ContrastOnPaint(hintLabel, 0.3f);
            UIFactory.Place(hintLabel.rectTransform, new Vector2(1, 0), new Vector2(1, 0), new Vector2(-96, 48), new Vector2(300, 40));

            // Subtítulos sueltos (más abajo y sin caja: texto con contorno sobre el mundo)
            var sub = UIFactory.Rect("Subtitles", canvas.transform);
            UIFactory.Place(sub, new Vector2(.5f, 0), new Vector2(.5f, 0), new Vector2(0, 40), new Vector2(1400, 90));
            subtitleRect = sub;
            subtitleGroup = sub.gameObject.AddComponent<CanvasGroup>();
            subtitleGroup.blocksRaycasts = false;
            subtitleLabel = UIFactory.Label("Text", sub, "", UIFactory.TextStyle.Body);
            UIFactory.Stretch(subtitleLabel.rectTransform);
            UIFactory.ContrastOnPaint(subtitleLabel, 0.35f);

            boxGroup.alpha = 0f;
            subtitleGroup.alpha = 0f;
            boxGroup.gameObject.SetActive(false);
            subtitleGroup.gameObject.SetActive(false);
        }
    }
}
