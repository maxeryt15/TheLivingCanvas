using System;
using System.Collections;
using TheLivingCanvas.Core;
using TheLivingCanvas.Interaction;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.Utilities;
using UnityEngine.UI;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// HUD de juego casi invisible: una mancha de pintura como mira y, al apuntar a algo interactuable,
    /// un prompt pintado (trazo de tinta, marca con la tecla y la acción). Sin rectángulos, sin estadísticas.
    /// Se construye por código al arrancar. La prioridad entre varios interactuables la decide PlayerInteractor.
    /// </summary>
    public class Hud : MonoBehaviour
    {
        PlayerInteractor interactor;

        // Mira
        Image reticle, reticleHalo;
        RectTransform reticleRect;
        UIAnimator ringAnim;
        float reticleK;

        // Prompt
        RectTransform promptRoot;
        UIAnimator strokeAnim, keyAnim, blotAnim, labelAnim;
        TextMeshProUGUI keyText, promptLabel;
        bool promptShown;
        string shownKey, shownPrompt;
        Coroutine press;

        // Pinceladas con vida: cada una deriva despacio (rotación y escala) con su propio ritmo. Valores en grados / fracción.
        RectTransform wStroke, wBlot, wBand;
        const float StrokeRot = -1.2f, BlotRot = 7f, BandRot = 1.6f;
        const float WobbleDeg = 1.2f, WobbleScale = 0.0175f, WobbleSpeed = 0.65f, WobbleMove = 2f; // WobbleMove en px del canvas
        bool usingGamepad;
        IDisposable anyButton;
        InputAction boundAction;

        static Color ReticleIdle => UITheme.Current.ReticleIdle;
        static Color ReticleActive => UITheme.Current.ReticleActive;

        void Awake()
        {
            // Un HUD se construye siempre desde cero: si la escena trae un canvas sobrante, se descarta (evita prompts duplicados).
            for (int i = transform.childCount - 1; i >= 0; i--) Destroy(transform.GetChild(i).gameObject);
            Build();
        }

        void Start()
        {
            interactor = FindAnyObjectByType<PlayerInteractor>();
            if (interactor != null)
            {
                boundAction = interactor.InteractAction.action;
                boundAction.performed += OnInteractPressed;
            }
            // El prompt muestra la tecla del último dispositivo usado (teclado/ratón o mando).
            anyButton = InputSystem.onAnyButtonPress.Call(c => usingGamepad = c.device is Gamepad);
        }

        void OnDestroy()
        {
            if (boundAction != null) boundAction.performed -= OnInteractPressed;
            anyButton?.Dispose();
        }

        void Update()
        {
            bool aiming = interactor != null && interactor.isActiveAndEnabled;
            // Con el cursor libre (panel abierto, pausa) no hay mira ni prompt.
            bool locked = Cursor.lockState == CursorLockMode.Locked;
            var current = aiming && locked ? interactor.Current : null;

            reticle.enabled = reticleHalo.enabled = aiming && locked;
            reticleK = Mathf.MoveTowards(reticleK, current != null ? 1f : 0f, Time.unscaledDeltaTime / 0.25f);
            float k = Mathf.SmoothStep(0f, 1f, reticleK);
            reticle.color = Color.Lerp(ReticleIdle, ReticleActive, k);
            reticleHalo.color = UITheme.A(UITheme.Current.OutlineDark, Mathf.Lerp(.5f, .7f, k));
            reticleRect.localScale = Vector3.one * Mathf.Lerp(1f, 1.5f, k);

            bool show = current != null;
            if (show != promptShown)
            {
                promptShown = show;
                // Prompt nuevo (estaba oculto): avanza a la siguiente variante sin que se vea el cambio.
                if (show && skinFade == null && UITheme.Current.CycleSkins && Time.unscaledTime - lastSkinChange > SkinMinOnAppear) ApplySkin(NextSkin());
                if (show) { strokeAnim.Show(); blotAnim.Show(); keyAnim.Show(); labelAnim.Show(); ringAnim.Show(); }
                else { strokeAnim.Hide(); blotAnim.Hide(); keyAnim.Hide(); labelAnim.Hide(); ringAnim.Hide(); shownPrompt = null; }
            }
            if (!show) return;
            Wobble();
            CycleTick();

            string key = interactor.InteractAction.action.GetBindingDisplayString(group: usingGamepad ? "Gamepad" : "Keyboard&Mouse");
            if (key != shownKey) { shownKey = key; keyText.text = key; }
            if (current.Prompt != shownPrompt) { shownPrompt = current.Prompt; promptLabel.text = shownPrompt; }
        }

        /// <summary>Balanceo sutil de las pinceladas del prompt (ruido suave, sin bucles evidentes). Quieto con Reduced motion.</summary>
        void Wobble()
        {
            if (GameSettings.ReducedMotion) return;
            float t = Time.unscaledTime * WobbleSpeed;
            Sway(wStroke, StrokeRot, t, 0f);
            Sway(wBlot, BlotRot, t, 11.3f);
            Sway(wBand, BandRot, t, 23.7f);
        }

        static void Sway(RectTransform r, float baseDeg, float t, float phase)
        {
            float a = Mathf.PerlinNoise(t + phase, 0.3f) * 2f - 1f;
            float b = Mathf.PerlinNoise(t * 0.8f + phase, 5.1f) * 2f - 1f;
            float cx = Mathf.PerlinNoise(t * 1.1f + phase, 9.7f) * 2f - 1f;
            float cy = Mathf.PerlinNoise(t * 0.9f + phase, 14.2f) * 2f - 1f;
            r.localRotation = Quaternion.Euler(0, 0, baseDeg + a * WobbleDeg);
            r.localScale = new Vector3(1f + b * WobbleScale, 1f - b * WobbleScale * 0.6f, 1f);
            r.anchoredPosition = new Vector2(cx, cy) * WobbleMove; // deriva leve; los rects están estirados, así que se desplazan enteros
        }

        // ---------- Respuesta al pulsar ----------

        void OnInteractPressed(InputAction.CallbackContext _)
        {
            if (!promptShown) return;
            UIEvents.Play(UISound.Interaction);
            if (GameSettings.ReducedMotion) return;
            if (press != null) StopCoroutine(press);
            press = StartCoroutine(PressRoutine());
        }

        IEnumerator PressRoutine()
        {
            // Se encoge un poco y vuelve: sutil, sin rebote.
            const float down = 0.09f, up = 0.2f;
            for (float t = 0; t < down; t += Time.unscaledDeltaTime)
            {
                promptRoot.localScale = Vector3.one * Mathf.Lerp(1f, .93f, Mathf.SmoothStep(0, 1, t / down));
                yield return null;
            }
            for (float t = 0; t < up; t += Time.unscaledDeltaTime)
            {
                promptRoot.localScale = Vector3.one * Mathf.Lerp(.93f, 1f, Mathf.SmoothStep(0, 1, t / up));
                yield return null;
            }
            promptRoot.localScale = Vector3.one;
            press = null;
        }

        // ---------- Variantes del prompt (ciclo con crossfade lento) ----------

        const float SkinEvery = 5f, SkinFade = 4f, SkinMinOnAppear = 8f; // segundos
        Image strokeImg, strokeOver, blotImg, blotOver;
        int skin;
        static int lastSkin = -1; // sobrevive a recargas de escena: el ciclo continúa donde iba
        float lastSkinChange;
        Coroutine skinFade;

        /// <summary>Copia hija de la imagen, transparente: sirve para fundir hacia la siguiente variante. Hereda alfa, balanceo y reveal del padre.</summary>
        static Image MakeOverlay(RectTransform parent, Image baseImg)
        {
            var r = UIFactory.Rect("SkinFade", parent);
            UIFactory.Stretch(r);
            var img = r.gameObject.AddComponent<Image>();
            img.sprite = baseImg.sprite;
            img.color = new Color(baseImg.color.r, baseImg.color.g, baseImg.color.b, 0f);
            img.raycastTarget = false;
            return img;
        }

        int NextSkin() => (skin + 1) % UITheme.Current.SkinCount;

        void ApplySkin(int i)
        {
            skin = lastSkin = i;
            lastSkinChange = Time.unscaledTime;
            UITheme.Current.SkinSprites(i, out var b, out var s);
            if (b != null) blotImg.sprite = b;
            if (s != null) strokeImg.sprite = s;
            SetOverlayAlpha(0f);
        }

        void SetOverlayAlpha(float k)
        {
            var c = blotOver.color; c.a = k * blotImg.color.a; blotOver.color = c;
            c = strokeOver.color; c.a = k * strokeImg.color.a; strokeOver.color = c;
        }

        /// <summary>Cada cierto tiempo, con el prompt a la vista, la pintura se funde despacio hacia la siguiente variante.</summary>
        void CycleTick()
        {
            var t = UITheme.Current;
            if (!t.CycleSkins || skinFade != null || GameSettings.ReducedMotion) return;
            if (Time.unscaledTime - lastSkinChange > SkinEvery) skinFade = StartCoroutine(FadeToSkin(NextSkin()));
        }

        IEnumerator FadeToSkin(int to)
        {
            UITheme.Current.SkinSprites(to, out var b, out var s);
            if (b == null || s == null) { skinFade = null; yield break; }
            blotOver.sprite = b; strokeOver.sprite = s;
            for (float e = 0; e < SkinFade; e += Time.unscaledDeltaTime)
            {
                SetOverlayAlpha(Mathf.SmoothStep(0f, 1f, e / SkinFade));
                yield return null;
            }
            ApplySkin(to);
            skinFade = null;
        }

        // ---------- Construcción ----------

        void Build()
        {
            var t = UITheme.Current;
            var canvas = UIFactory.Canvas("HudCanvas", 10);
            canvas.transform.SetParent(transform, false);
            canvas.GetComponent<GraphicRaycaster>().enabled = false; // el HUD no recibe clics

            BuildReticle(canvas.transform, t);
            BuildPrompt(canvas.transform, t);
        }

        void BuildReticle(Transform parent, UITheme t)
        {
            // Anillo de tinta que aparece alrededor al poder interactuar
            var ringRect = UIFactory.Rect("Ring", parent);
            UIFactory.Place(ringRect, new Vector2(.5f, .5f), new Vector2(.5f, .5f), Vector2.zero, new Vector2(46, 46));
            var ring = ringRect.gameObject.AddComponent<Image>();
            ring.sprite = BrushStrokes.Ring(3);
            ring.color = UITheme.A(t.cream, .75f);
            ring.raycastTarget = false;
            ringAnim = ringRect.gameObject.AddComponent<UIAnimator>().Configure(UIAnimKind.InkReveal, UIAnimKind.FadeOut, 1.3f);
            ringAnim.Set(false);

            // Mancha de pintura pequeña como mira, con un halo de tinta detrás para leerse sobre cualquier fondo
            reticleRect = UIFactory.Rect("Reticle", parent);
            UIFactory.Place(reticleRect, new Vector2(.5f, .5f), new Vector2(.5f, .5f), Vector2.zero, new Vector2(12, 12));
            var haloRect = UIFactory.Rect("Halo", reticleRect);
            UIFactory.Place(haloRect, new Vector2(.5f, .5f), new Vector2(.5f, .5f), Vector2.zero, new Vector2(21, 21));
            reticleHalo = haloRect.gameObject.AddComponent<Image>();
            reticleHalo.sprite = BrushStrokes.Blot(6);
            reticleHalo.color = UITheme.A(t.OutlineDark, .55f);
            reticleHalo.raycastTarget = false;
            var dotRect = UIFactory.Rect("Dot", reticleRect);
            UIFactory.Stretch(dotRect);
            reticle = dotRect.gameObject.AddComponent<Image>();
            reticle.sprite = t.reticle != null ? t.reticle : BrushStrokes.Blot(2);
            reticle.color = ReticleIdle;
            reticle.raycastTarget = false;
        }

        void BuildPrompt(Transform parent, UITheme t)
        {
            promptRoot = UIFactory.Rect("InteractionPrompt", parent);
            UIFactory.Place(promptRoot, new Vector2(.5f, 0), new Vector2(.5f, .5f), new Vector2(0, 150), new Vector2(300, 84));
            var row = promptRoot.gameObject.AddComponent<HorizontalLayoutGroup>();
            row.padding = new RectOffset(48, 56, 10, 10);
            row.spacing = 14;
            row.childAlignment = TextAnchor.MiddleCenter;
            row.childControlWidth = row.childControlHeight = true;
            row.childForceExpandWidth = row.childForceExpandHeight = false;
            var fit = promptRoot.gameObject.AddComponent<ContentSizeFitter>();
            fit.horizontalFit = fit.verticalFit = ContentSizeFitter.FitMode.PreferredSize;

            // Trazo de tinta detrás (sin bordes rectos): da contraste sin ser una caja
            var strokeRect = UIFactory.Rect("Stroke", promptRoot);
            strokeRect.gameObject.AddComponent<LayoutElement>().ignoreLayout = true;
            UIFactory.Stretch(strokeRect);
            strokeRect.offsetMin = new Vector2(-26, -8);
            strokeRect.offsetMax = new Vector2(26, 8);
            var stroke = strokeRect.gameObject.AddComponent<Image>();
            skin = lastSkin >= 0 && lastSkin < t.SkinCount ? lastSkin : (t.CycleSkins ? 0 : Mathf.Max(0, t.SavedSkin + 1));
            t.SkinSprites(skin, out var skinBlot, out var skinStroke);
            bool paintedStroke = skinStroke != null;
            stroke.sprite = paintedStroke ? skinStroke : BrushStrokes.Stroke(7, 512, 96);
            strokeImg = stroke;
            // Se multiplica por un tono oscuro para atenuar el trazo: el texto crema destaca sobre él.
            stroke.color = paintedStroke ? t.PromptStrokeTint : UITheme.A(t.ink, .75f);
            stroke.raycastTarget = false;
            strokeOver = MakeOverlay(strokeRect, stroke);
            strokeRect.localRotation = Quaternion.Euler(0, 0, StrokeRot);
            wStroke = strokeRect;
            strokeAnim = strokeRect.gameObject.AddComponent<UIAnimator>().Configure(UIAnimKind.BrushReveal, UIAnimKind.FadeOut, 4.1f);

            // Marca con la tecla: mancha crema con la letra en tinta
            var keyRect = UIFactory.Rect("Key", promptRoot);
            var le = keyRect.gameObject.AddComponent<LayoutElement>();
            le.minWidth = le.preferredWidth = 88; le.minHeight = le.preferredHeight = 64;
            var blotRect = UIFactory.Rect("Blot", keyRect);
            UIFactory.Stretch(blotRect);
            var blot = blotRect.gameObject.AddComponent<Image>();
            bool paintedBlot = skinBlot != null;
            blot.sprite = paintedBlot ? skinBlot : BrushStrokes.Dab(5, 160, 112);
            blot.color = paintedBlot ? Color.white : UITheme.A(t.cream, .95f);
            blotImg = blot;
            blot.raycastTarget = false;
            blotOver = MakeOverlay(blotRect, blot);
            blotRect.localRotation = Quaternion.Euler(0, 0, BlotRot);
            wBlot = blotRect;
            blotAnim = blotRect.gameObject.AddComponent<UIAnimator>().Configure(UIAnimKind.InkReveal, UIAnimKind.FadeOut, 2.3f, 0.12f);
            // Disco de tinta bajo la letra: se lee igual sobre cualquier variante pintada
            var discRect = UIFactory.Rect("Disc", keyRect);
            UIFactory.Stretch(discRect);
            discRect.offsetMin = new Vector2(16, 12); discRect.offsetMax = new Vector2(-16, -12);
            var disc = discRect.gameObject.AddComponent<Image>();
            disc.sprite = BrushStrokes.Blot(4); disc.color = UITheme.A(t.OutlineDark, .88f); disc.raycastTarget = false;
            keyText = UIFactory.Label("Letter", keyRect, "E", UIFactory.TextStyle.Body);
            UIFactory.Stretch(keyText.rectTransform);
            keyText.fontStyle = FontStyles.Bold;
            keyText.color = t.Paper;
            UIFactory.ContrastOnPaint(keyText, 0.4f);
            keyText.outlineColor = t.OutlineDark; // contorno negro: la letra blanca resalta sobre la marca
            keyText.textWrappingMode = TextWrappingModes.NoWrap;
            keyText.enableAutoSizing = true;
            keyText.fontSizeMin = 16; keyText.fontSizeMax = 36;
            keyAnim = keyRect.gameObject.AddComponent<UIAnimator>().Configure(UIAnimKind.FadeIn, UIAnimKind.FadeOut, 0f, 0.2f);

            // Acción
            // Acción: dentro de una caja de layout con una pincelada oscura detrás (resaltado de tinta) para leerse sobre la pintura
            var labelBox = UIFactory.Rect("LabelBox", promptRoot);
            var boxRow = labelBox.gameObject.AddComponent<HorizontalLayoutGroup>();
            boxRow.padding = new RectOffset(46, 46, 10, 10); // margen amplio: las puntas afiladas del barrido caen fuera del texto
            boxRow.childAlignment = TextAnchor.MiddleLeft;
            boxRow.childControlWidth = boxRow.childControlHeight = true;
            boxRow.childForceExpandWidth = boxRow.childForceExpandHeight = false;

            var bandRect = UIFactory.Rect("Highlight", labelBox);
            bandRect.gameObject.AddComponent<LayoutElement>().ignoreLayout = true;
            UIFactory.Stretch(bandRect);
            var band = bandRect.gameObject.AddComponent<Image>();
            band.sprite = BrushStrokes.Swipe(9);
            band.color = t.HudBand;
            band.raycastTarget = false;
            bandRect.localRotation = Quaternion.Euler(0, 0, BandRot); // ligeramente inclinado, como un trazo a mano
            wBand = bandRect;

            promptLabel = UIFactory.Label("Label", labelBox, "", UIFactory.TextStyle.Body, TextAlignmentOptions.Left);
            promptLabel.textWrappingMode = TextWrappingModes.NoWrap;
            promptLabel.fontSize = t.bodySize * 1.1f;
            promptLabel.fontStyle = FontStyles.Bold;
            promptLabel.color = t.Paper;
            UIFactory.ContrastOnPaint(promptLabel, 0.4f);
            promptLabel.outlineColor = t.OutlineDark; // contorno negro: legible sobre cualquier pincelada
            labelAnim = labelBox.gameObject.AddComponent<UIAnimator>().Configure(UIAnimKind.FadeIn, UIAnimKind.FadeOut, 0f, 0.3f);

            strokeAnim.Set(false); blotAnim.Set(false); keyAnim.Set(false); labelAnim.Set(false);
        }
    }
}
