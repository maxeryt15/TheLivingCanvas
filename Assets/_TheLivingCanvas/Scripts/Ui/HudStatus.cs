using System.Collections.Generic;
using TheLivingCanvas.Core;
using TheLivingCanvas.Economy;
using TheLivingCanvas.Painting;
using TheLivingCanvas.Progression;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// Estado discreto abajo a la izquierda: monedas (con "+30" al cambiar), nivel con barra pintada y los pigmentos que
    /// tienes como manchas con su cantidad. Sustituye a CoinCounterUI / LevelCounterUI del Studio. Se atenúa tras unos
    /// segundos sin cambios y vuelve a verse al cambiar algo. Busca Wallet / ArtistLevel / PigmentStock al arrancar;
    /// la fila que no encuentra no se muestra.
    /// </summary>
    public class HudStatus : MonoBehaviour
    {
        const float Width = 400f, Margin = 48f, IdleAlpha = .55f, IdleAfter = 5f, FadeSpeed = 4f;
        const int MaxPigments = 8;

        Wallet wallet;
        ArtistLevel level;
        PigmentStock pigments;

        CanvasGroup group;
        RectTransform card, swatchRow;
        TextMeshProUGUI coinText, deltaText, levelText;
        Image xpFill;
        RectTransform xpRect;
        float lastChange, deltaUntil, shownXp, punchStart = float.NegativeInfinity;
        readonly List<GameObject> swatches = new List<GameObject>();

        void Awake()
        {
            wallet = FindAnyObjectByType<Wallet>();
            level = FindAnyObjectByType<ArtistLevel>();
            pigments = FindAnyObjectByType<PigmentStock>();
            Build();
        }

        void OnEnable()
        {
            if (wallet != null) wallet.Changed += OnCoins;
            if (level != null) level.Changed += OnLevel;
            if (pigments != null) pigments.Changed += RebuildPigments;
            RefreshAll();
        }

        void OnDisable()
        {
            if (wallet != null) wallet.Changed -= OnCoins;
            if (level != null) level.Changed -= OnLevel;
            if (pigments != null) pigments.Changed -= RebuildPigments;
        }

        void Build()
        {
            var t = UITheme.Current;
            var canvas = UIFactory.Canvas("HudStatusCanvas", 200);
            canvas.transform.SetParent(transform, false);

            card = UIFactory.Rect("Card", canvas.transform);
            UIFactory.Place(card, Vector2.zero, Vector2.zero, new Vector2(Margin, Margin), new Vector2(Width, 150f));
            group = card.gameObject.AddComponent<CanvasGroup>();
            group.blocksRaycasts = false; group.interactable = false;

            var bg = card.gameObject.AddComponent<Image>();
            bg.sprite = t.tooltip; bg.type = t.tooltip != null ? Image.Type.Sliced : Image.Type.Simple;
            bg.color = t.tooltip != null ? new Color(1, 1, 1, .9f) : t.Shade(.8f);
            bg.raycastTarget = false;

            // Monedas
            var dot = UIFactory.Rect("CoinDot", card);
            UIFactory.Place(dot, new Vector2(0, 1), new Vector2(.5f, .5f), new Vector2(34, -32), new Vector2(26, 26));
            var di = dot.gameObject.AddComponent<Image>();
            di.sprite = BrushStrokes.Blot(3); di.color = t.Reward; di.raycastTarget = false;
            coinText = UIFactory.Label("Coins", card, "0", UIFactory.TextStyle.Body, TextAlignmentOptions.Left);
            UIFactory.Place(coinText.rectTransform, new Vector2(0, 1), new Vector2(0, .5f), new Vector2(56, -32), new Vector2(190, 40));
            UIFactory.ContrastOnPaint(coinText, .2f);
            deltaText = UIFactory.Label("Delta", card, "", UIFactory.TextStyle.Small, TextAlignmentOptions.Right);
            UIFactory.Place(deltaText.rectTransform, new Vector2(1, 1), new Vector2(1, .5f), new Vector2(-22, -32), new Vector2(120, 32));
            UIFactory.ContrastOnPaint(deltaText, .2f);

            // Nivel + barra pintada
            levelText = UIFactory.Label("Level", card, "Lv 1", UIFactory.TextStyle.Small, TextAlignmentOptions.Left);
            UIFactory.Place(levelText.rectTransform, new Vector2(0, 1), new Vector2(0, .5f), new Vector2(24, -72), new Vector2(120, 28));
            UIFactory.ContrastOnPaint(levelText, .2f);
            var groove = UIFactory.Rect("XpGroove", card);
            UIFactory.Place(groove, new Vector2(0, 1), new Vector2(0, .5f), new Vector2(110, -72), new Vector2(Width - 140f, 18));
            var gi = groove.gameObject.AddComponent<Image>();
            gi.sprite = t.barBack; gi.type = t.barBack != null ? Image.Type.Sliced : Image.Type.Simple;
            gi.color = t.barBack != null ? Color.white : UITheme.A(t.ink, .7f); gi.raycastTarget = false;
            var fillArea = UIFactory.Rect("Fill", groove);
            UIFactory.Stretch(fillArea);
            fillArea.offsetMin = new Vector2(1, 0); fillArea.offsetMax = new Vector2(-1, 0);
            fillArea.gameObject.AddComponent<RectMask2D>();
            xpRect = UIFactory.Rect("Paint", fillArea);
            xpRect.anchorMin = Vector2.zero; xpRect.anchorMax = new Vector2(0f, 1f);
            xpRect.offsetMin = xpRect.offsetMax = Vector2.zero;
            xpFill = xpRect.gameObject.AddComponent<Image>();
            xpFill.sprite = t.barFill; xpFill.type = t.barFill != null ? Image.Type.Sliced : Image.Type.Simple;
            xpFill.color = Color.Lerp(t.Positive, Color.white, .25f); xpFill.raycastTarget = false;

            // Pigmentos
            swatchRow = UIFactory.Rect("Pigments", card);
            UIFactory.Place(swatchRow, new Vector2(0, 0), new Vector2(0, 0), new Vector2(22, 14), new Vector2(Width - 44f, 54));
            var layout = swatchRow.gameObject.AddComponent<HorizontalLayoutGroup>();
            layout.spacing = 8f; layout.childAlignment = TextAnchor.MiddleLeft;
            layout.childControlWidth = layout.childControlHeight = false;
            layout.childForceExpandWidth = layout.childForceExpandHeight = false;

            if (wallet == null) { coinText.gameObject.SetActive(false); dot.gameObject.SetActive(false); }
            if (level == null) { levelText.gameObject.SetActive(false); groove.gameObject.SetActive(false); }
            lastChange = Time.unscaledTime;
        }

        void RefreshAll()
        {
            if (card == null) return;
            if (wallet != null) coinText.text = wallet.Coins + " coins";
            if (level != null) { OnLevel(); shownXp = level.Progress; SetXp(shownXp); }
            RebuildPigments();
        }

        void OnCoins(int total, int delta)
        {
            coinText.text = total + " coins";
            if (delta == 0) return; // carga de partida: sin "+0"
            deltaText.text = delta > 0 ? "+" + delta : delta.ToString();
            deltaText.color = delta > 0 ? UITheme.Current.Reward : UITheme.Current.Warn;
            deltaUntil = Time.unscaledTime + 2f;
            if (delta > 0) punchStart = Time.unscaledTime;
            Touch();
        }

        void OnLevel()
        {
            if (level == null) return;
            levelText.text = level.IsMaxLevel ? "Lv " + level.Level + " (max)" : "Lv " + level.Level;
            Touch();
        }

        void RebuildPigments()
        {
            if (card == null) return;
            foreach (var s in swatches) if (s != null) Destroy(s);
            swatches.Clear();
            int shown = 0;
            if (pigments != null)
            {
                foreach (var pair in pigments.All)
                {
                    if (pair.Value <= 0 || pair.Key == null) continue;
                    if (shown++ >= MaxPigments) break;
                    swatches.Add(MakeSwatch(pair.Key.Color, pair.Value));
                }
            }
            swatchRow.gameObject.SetActive(shown > 0);
            var rt = card.sizeDelta;
            card.sizeDelta = new Vector2(rt.x, shown > 0 ? 150f : 96f);
            Touch();
        }

        GameObject MakeSwatch(Color col, int amount)
        {
            var t = UITheme.Current;
            var r = UIFactory.Rect("Swatch", swatchRow);
            r.sizeDelta = new Vector2(38, 50);
            var le = r.gameObject.AddComponent<LayoutElement>();
            le.minWidth = le.preferredWidth = 38; le.minHeight = le.preferredHeight = 50;
            var blot = UIFactory.Rect("Blot", r);
            UIFactory.Place(blot, new Vector2(.5f, 1), new Vector2(.5f, 1), new Vector2(0, 0), new Vector2(34, 34));
            var bi = blot.gameObject.AddComponent<Image>();
            bi.sprite = BrushStrokes.Blot(Mathf.Abs(col.GetHashCode()) % 7 + 1); bi.color = col; bi.raycastTarget = false;
            var n = UIFactory.Label("N", r, amount.ToString(), UIFactory.TextStyle.Small, TextAlignmentOptions.Center);
            n.fontSize = 17;
            UIFactory.Place(n.rectTransform, new Vector2(.5f, 0), new Vector2(.5f, 0), Vector2.zero, new Vector2(46, 20));
            UIFactory.ContrastOnPaint(n, .2f);
            return r.gameObject;
        }

        void SetXp(float v) { xpRect.anchorMax = new Vector2(Mathf.Clamp01(v), 1f); }

        void Touch() { lastChange = Time.unscaledTime; }

        void Update()
        {
            if (group == null) return;
            float now = Time.unscaledTime;
            bool reduced = GameSettings.ReducedMotion;

            float target = now - lastChange < IdleAfter ? 1f : IdleAlpha;
            group.alpha = reduced ? target : Mathf.MoveTowards(group.alpha, target, FadeSpeed * Time.unscaledDeltaTime);

            if (deltaText.text.Length > 0 && now >= deltaUntil) deltaText.text = "";

            if (level != null)
            {
                float want = level.Progress;
                shownXp = reduced ? want : Mathf.Lerp(shownXp, want, 1f - Mathf.Exp(-6f * Time.unscaledDeltaTime));
                SetXp(shownXp);
            }

            float punch = (now - punchStart) / .25f;
            coinText.rectTransform.localScale = Vector3.one * (!reduced && punch < 1f ? Mathf.Lerp(1f, 1.18f, 1f - Mathf.Abs(2f * punch - 1f)) : 1f);
        }
    }
}
