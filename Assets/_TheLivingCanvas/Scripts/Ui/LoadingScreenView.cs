using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// Presentación de la pantalla de carga: un papel con un lienzo a medio pintar. El boceto a carbón está siempre; el paisaje
    /// pintado se descubre con una pincelada (shader PaintReveal) según el progreso real. Debajo, un trazo que se rellena y el
    /// mensaje. No decide nada de la carga: solo recibe progreso, estado y texto desde SceneLoader.
    /// </summary>
    public class LoadingScreenView : MonoBehaviour
    {
        const float MessageFade = 0.3f;

        CanvasGroup group;
        Image paper, shadow, sketch, painted, barBack, barFill;
        RectTransform canvasHolder, paperRect;
        TextMeshProUGUI titleText, messageText;
        Material revealMat;
        float messageAlpha = 1f, messageTimer;
        string pendingMessage;
        float progress;
        float seed;

        static readonly int RevealId = Shader.PropertyToID("_Reveal");

        public float Alpha { get => group.alpha; set => group.alpha = value; }
        public bool BlocksRaycasts { set => group.blocksRaycasts = value; }
        public Color PaperColor { get; private set; } = UITheme.Current.Paper;

        public static LoadingScreenView Create(Transform parent)
        {
            var canvas = UIFactory.Canvas("LoadingCanvas", 1000);
            canvas.transform.SetParent(parent, false);
            var view = canvas.gameObject.AddComponent<LoadingScreenView>();
            view.Build(canvas.transform);
            return view;
        }

        void Build(Transform root)
        {
            var t = UITheme.Current;
            group = gameObject.AddComponent<CanvasGroup>();
            group.alpha = 0f;
            group.blocksRaycasts = false;
            seed = Random.Range(0f, 100f);

            // Papel: llena toda la pantalla (se recorta en 16:10 y 21:9, nunca se deforma)
            paperRect = UIFactory.Rect("Paper", root);
            UIFactory.Stretch(paperRect);
            paperRect.localScale = Vector3.one * 1.04f; // margen para la deriva ambiente
            paper = paperRect.gameObject.AddComponent<Image>();
            paper.raycastTarget = false;
            paper.color = PaperColor;

            // Lienzo: centrado y algo alto, ligeramente torcido como pegado a mano
            // Zona del lienzo: proporcional a la pantalla; el ajustador de aspecto mantiene 16:9 sin deformar en 16:10, 21:9, etc.
            var area = UIFactory.Rect("CanvasArea", root);
            area.anchorMin = new Vector2(.06f, .19f); area.anchorMax = new Vector2(.94f, .905f);
            area.offsetMin = area.offsetMax = Vector2.zero;
            canvasHolder = UIFactory.Rect("Canvas", area); // recibe el giro y el movimiento ambiente
            UIFactory.Stretch(canvasHolder);
            canvasHolder.localRotation = Quaternion.Euler(0, 0, -0.7f);
            var fit = UIFactory.Rect("Fit", canvasHolder);
            UIFactory.Stretch(fit);
            var fitter = fit.gameObject.AddComponent<AspectRatioFitter>();
            fitter.aspectMode = AspectRatioFitter.AspectMode.FitInParent;
            fitter.aspectRatio = 16f / 9f;

            var shadowRect = UIFactory.Rect("Shadow", fit);
            UIFactory.Stretch(shadowRect);
            shadowRect.offsetMin = new Vector2(10, -18); shadowRect.offsetMax = new Vector2(10, -18);
            shadow = shadowRect.gameObject.AddComponent<Image>();
            shadow.raycastTarget = false;
            shadow.color = UITheme.A(t.ink, .18f);

            var sketchRect = UIFactory.Rect("Sketch", fit);
            UIFactory.Stretch(sketchRect);
            sketch = sketchRect.gameObject.AddComponent<Image>();
            sketch.raycastTarget = false;

            var paintedRect = UIFactory.Rect("Painted", fit);
            UIFactory.Stretch(paintedRect);
            painted = paintedRect.gameObject.AddComponent<Image>();
            painted.raycastTarget = false;
            var shader = UIAnimPresets.RevealShader;
            if (shader != null)
            {
                revealMat = new Material(shader) { hideFlags = HideFlags.DontSave };
                revealMat.DisableKeyword("_MODE_INK"); revealMat.DisableKeyword("_MODE_DISSOLVE");
                revealMat.EnableKeyword("_MODE_BRUSH");
                revealMat.SetFloat("_Soft", .2f);
                revealMat.SetFloat("_Seed", seed);
                revealMat.SetFloat(RevealId, 0f);
                painted.material = revealMat;
            }

            // Título discreto sobre el lienzo
            titleText = UIFactory.Label("Title", root, "The Living Canvas", UIFactory.TextStyle.Heading);
            UIFactory.Place(titleText.rectTransform, new Vector2(.5f, .985f), new Vector2(.5f, 1f), Vector2.zero, new Vector2(1000, 60));
            titleText.fontStyle = FontStyles.Bold;
            titleText.fontSize = 36;
            titleText.characterSpacing = 6f;
            titleText.color = UITheme.A(t.ink, .85f);

            // Progreso: pincelada que se rellena bajo el lienzo
            var back = UIFactory.Rect("BarBack", root);
            UIFactory.Place(back, new Vector2(.5f, .115f), new Vector2(.5f, .5f), Vector2.zero, new Vector2(760, 40));
            barBack = back.gameObject.AddComponent<Image>();
            barBack.raycastTarget = false;
            barBack.color = UITheme.A(t.ink, .16f);
            var fillRect = UIFactory.Rect("BarFill", back);
            UIFactory.Stretch(fillRect);
            barFill = fillRect.gameObject.AddComponent<Image>();
            barFill.type = Image.Type.Filled;
            barFill.fillMethod = Image.FillMethod.Horizontal;
            barFill.raycastTarget = false;

            messageText = UIFactory.Label("Message", root, "", UIFactory.TextStyle.Body);
            UIFactory.Place(messageText.rectTransform, new Vector2(.5f, .06f), new Vector2(.5f, .5f), Vector2.zero, new Vector2(1200, 56));
            messageText.fontStyle = FontStyles.Italic;
            messageText.color = t.ink;
            messageText.textWrappingMode = TextWrappingModes.NoWrap;
            ApplyContrast(false);
        }

        /// <summary>Elige la ilustración. Los sprites que falten se sustituyen por la cubierta pintada o por nada: nunca se rompe.</summary>
        public void SetVariant(LoadingScreenSettings.Variant v, bool faded, string title, bool showTitle)
        {
            var t = UITheme.Current;
            PaperColor = v != null ? v.paperTint : PaperColor;
            paper.sprite = v != null ? v.paper : null;
            paper.color = PaperColor;

            Sprite fallbackPaint = t.transitionCovers != null && t.transitionCovers.Length > 0 ? t.transitionCovers[0] : null;
            Sprite sk = v != null ? v.sketch : null;
            Sprite pt = v != null ? (faded && v.paintedFaded != null ? v.paintedFaded : v.painted) : null;
            sketch.sprite = sk; sketch.enabled = sk != null;
            painted.sprite = pt != null ? pt : fallbackPaint;
            painted.enabled = painted.sprite != null;
            // Sin arte configurado el lienzo sigue siendo una superficie (la cubierta), no un hueco
            shadow.sprite = sk != null ? sk : painted.sprite; // la sombra copia la silueta irregular del lienzo
            shadow.enabled = shadow.sprite != null;

            titleText.text = title;
            titleText.gameObject.SetActive(showTitle);
            // Pincelada azul clara (la variante "Almond" del prompt); si no existe, trazo procedural liso
            t.SkinSprites(t.SkinCount - 1, out _, out var barStroke);
            barBack.sprite = barFill.sprite = barStroke != null ? barStroke : BrushStrokes.Stroke(7, 512, 96);
            barFill.color = barStroke != null ? Color.white : t.cerulean;
            SetProgress(0f);
        }

        public void SetProgress(float p)
        {
            progress = Mathf.Clamp01(p);
            barFill.fillAmount = progress;
            if (revealMat != null) revealMat.SetFloat(RevealId, progress);
        }

        /// <summary>Cambia el mensaje con un fundido corto (no salta de golpe).</summary>
        public void SetMessage(string text, bool immediate = false)
        {
            if (text == pendingMessage || text == messageText.text && messageAlpha >= 1f) { pendingMessage = text; return; }
            pendingMessage = text;
            if (immediate) { messageText.text = text; messageAlpha = 1f; messageText.alpha = 1f; }
        }

        public void ApplyContrast(bool highContrast)
        {
            var t = UITheme.Current;
            messageText.outlineWidth = highContrast ? 0.35f : 0.12f;
            messageText.outlineColor = highContrast ? (Color32)Color.white : (Color32)PaperColor;
            messageText.color = highContrast ? Color.black : t.ink;
            messageText.fontSize = highContrast ? t.bodySize * 1.2f : t.bodySize;
            titleText.color = highContrast ? Color.black : UITheme.A(t.ink, .85f);
        }

        /// <summary>Movimiento ambiente casi imperceptible (el lienzo respira). 0 = quieto.</summary>
        public void Ambient(float intensity)
        {
            if (intensity <= 0f)
            {
                canvasHolder.localRotation = Quaternion.Euler(0, 0, -0.7f);
                canvasHolder.anchoredPosition = Vector2.zero;
                paperRect.localScale = Vector3.one * 1.04f;
                return;
            }
            float tm = Time.unscaledTime * .12f;
            float a = Mathf.PerlinNoise(tm + seed, .3f) * 2f - 1f;
            float b = Mathf.PerlinNoise(tm * .8f + seed, 4.1f) * 2f - 1f;
            float c = Mathf.PerlinNoise(tm * .9f + seed, 8.7f) * 2f - 1f;
            canvasHolder.localRotation = Quaternion.Euler(0, 0, -0.7f + a * .35f * intensity);
            canvasHolder.anchoredPosition = new Vector2(b, c) * 4f * intensity;
            paperRect.localScale = Vector3.one * (1.04f + a * .006f * intensity);
        }

        void Update()
        {
            // Mensaje: baja, cambia el texto y sube
            if (pendingMessage != null && pendingMessage != messageText.text)
            {
                messageAlpha = Mathf.MoveTowards(messageAlpha, 0f, Time.unscaledDeltaTime / MessageFade);
                if (messageAlpha <= 0f) messageText.text = pendingMessage;
            }
            else messageAlpha = Mathf.MoveTowards(messageAlpha, 1f, Time.unscaledDeltaTime / MessageFade);
            messageText.alpha = messageAlpha;
        }

        void OnDestroy()
        {
            if (revealMat != null) Destroy(revealMat);
        }
    }
}
