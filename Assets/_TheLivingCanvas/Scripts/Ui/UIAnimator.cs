using System.Collections;
using System.Collections.Generic;
using TheLivingCanvas.Core;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// Anima la aparición/desaparición de un elemento de UI con un preset (fade, escala suave, deslizamiento,
    /// pincelada, tinta, página, disolución). Un solo componente por elemento: si se llama a Show/Hide mientras
    /// otra animación corre, la sustituye sin acumular. Con "Reduced motion" todo se reduce a un fundido corto.
    /// Los presets de pincelada/tinta/disolución afectan a las Image hijas; el texto (TMP) solo se desvanece.
    /// </summary>
    [DisallowMultipleComponent]
    [RequireComponent(typeof(RectTransform))]
    public class UIAnimator : MonoBehaviour
    {
        [SerializeField] UIAnimKind showPreset = UIAnimKind.FadeIn;
        [SerializeField] UIAnimKind hidePreset = UIAnimKind.FadeOut;
        [SerializeField] bool playOnEnable;
        [Tooltip("Desactiva el GameObject al terminar de ocultarse.")]
        [SerializeField] bool deactivateOnHide = true;
        [Tooltip("Semilla del ruido de los revelados (cada elemento se pinta distinto).")]
        [SerializeField] float seed;
        [Tooltip("Retardo extra al mostrarse, sumado al del preset (para escalonar elementos: trazo, luego texto).")]
        [SerializeField] float showDelay;

        RectTransform rect;
        CanvasGroup group;
        Coroutine run;
        Vector3 baseScale = Vector3.one;
        Vector2 basePos;
        bool baseCaptured;
        Image[] images;
        Material[] originals;
        Material revealMat;
        bool wasHidden = true;

        static readonly int RevealId = Shader.PropertyToID("_Reveal");
        static readonly int SoftId = Shader.PropertyToID("_Soft");
        static readonly int SeedId = Shader.PropertyToID("_Seed");

        public bool IsShown { get; private set; }

        void Awake() => Capture();

        void OnEnable()
        {
            if (playOnEnable && wasHidden) Show();
        }

        void OnDisable()
        {
            // Un GameObject desactivado no corre corrutinas: deja el estado final coherente.
            run = null;
            RestoreMaterials();
        }

        void OnDestroy()
        {
            if (revealMat != null) Destroy(revealMat);
        }

        void Capture()
        {
            if (baseCaptured) return;
            rect = (RectTransform)transform;
            group = GetComponent<CanvasGroup>();
            if (group == null) group = gameObject.AddComponent<CanvasGroup>();
            baseScale = rect.localScale;
            basePos = rect.anchoredPosition;
            baseCaptured = true;
        }

        /// <summary>Configuración desde código (elementos creados en runtime).</summary>
        public UIAnimator Configure(UIAnimKind show, UIAnimKind hide, float noiseSeed = 0f, float extraDelay = 0f, bool deactivate = false)
        {
            showPreset = show; hidePreset = hide; seed = noiseSeed; showDelay = extraDelay; deactivateOnHide = deactivate;
            return this;
        }

        public void Show() => Play(showPreset, true);
        public void Hide() => Play(hidePreset, false);
        public void Show(UIAnimKind preset) => Play(preset, true);
        public void Hide(UIAnimKind preset) => Play(preset, false);

        /// <summary>Muestra o esconde sin animar (estado inicial).</summary>
        public void Set(bool shown)
        {
            Capture();
            Stop();
            gameObject.SetActive(shown || !deactivateOnHide);
            Apply(UIAnimPresets.Default(UIAnimKind.FadeIn), shown ? 1f : 0f, false);
            IsShown = shown;
            wasHidden = !shown;
        }

        void Play(UIAnimKind kind, bool show)
        {
            Capture();
            Stop();
            if (show) gameObject.SetActive(true);
            if (!gameObject.activeInHierarchy) { IsShown = show; return; }
            run = StartCoroutine(Run(UIAnimPresets.Get(kind), show));
        }

        void Stop()
        {
            if (run != null) { StopCoroutine(run); run = null; }
        }

        IEnumerator Run(UIAnimPreset p, bool show)
        {
            bool reduced = GameSettings.ReducedMotion;
            bool shaderKind = p.kind == UIAnimKind.BrushReveal || p.kind == UIAnimKind.InkReveal || p.kind == UIAnimKind.Dissolve;
            bool useShader = shaderKind && !reduced && PrepareReveal(p);
            float duration = reduced ? Mathf.Min(p.duration, 0.2f) : p.duration;
            float delay = reduced ? 0f : p.delay + (show ? showDelay : 0f);

            IsShown = show;
            wasHidden = false;
            float from = show ? 0f : 1f, to = show ? 1f : 0f;
            Apply(p, from, useShader);
            if (delay > 0f) yield return new WaitForSecondsRealtime(delay);

            for (float t = 0f; t < duration; t += Time.unscaledDeltaTime)
            {
                Apply(p, Mathf.LerpUnclamped(from, to, p.curve.Evaluate(t / duration)), useShader);
                yield return null;
            }
            Apply(p, to, useShader);

            RestoreMaterials();
            run = null;
            if (!show)
            {
                wasHidden = true;
                if (deactivateOnHide) gameObject.SetActive(false);
            }
        }

        /// <summary>Aplica la animación con progreso v (0 = oculto, 1 = visible).</summary>
        void Apply(UIAnimPreset p, float v, bool useShader)
        {
            bool reduced = GameSettings.ReducedMotion;
            group.alpha = useShader ? (v > 0f ? 1f : 0f) : Mathf.Clamp01(v);
            group.blocksRaycasts = v > 0.5f;
            if (useShader && revealMat != null) revealMat.SetFloat(RevealId, v);

            // Solo se tocan escala/posición cuando el preset las usa: así un LayoutGroup puede colocar al elemento.
            switch (p.kind)
            {
                case UIAnimKind.SoftScale:
                    rect.localScale = reduced ? baseScale : baseScale * Mathf.Lerp(p.fromScale, 1f, v); break;
                case UIAnimKind.SoftSlide:
                    rect.anchoredPosition = reduced ? basePos : basePos + p.slide * (1f - v); break;
                case UIAnimKind.PageTurn:
                    rect.localScale = reduced ? baseScale : new Vector3(baseScale.x * Mathf.Lerp(p.fromScale, 1f, v), baseScale.y, baseScale.z); break;
            }
        }

        // ---------- Revelado por shader ----------

        bool PrepareReveal(UIAnimPreset p)
        {
            var shader = UIAnimPresets.RevealShader;
            if (shader == null) return false;
            if (images == null) images = GetComponentsInChildren<Image>(true);
            if (images.Length == 0) return false;
            if (revealMat == null) revealMat = new Material(shader) { hideFlags = HideFlags.DontSave };

            string mode = p.kind == UIAnimKind.BrushReveal ? "_MODE_BRUSH" : p.kind == UIAnimKind.InkReveal ? "_MODE_INK" : "_MODE_DISSOLVE";
            foreach (var k in new[] { "_MODE_BRUSH", "_MODE_INK", "_MODE_DISSOLVE" }) revealMat.DisableKeyword(k);
            revealMat.EnableKeyword(mode);
            revealMat.SetFloat(SoftId, p.edgeSoftness);
            revealMat.SetFloat(SeedId, seed);

            if (originals == null) originals = new Material[images.Length];
            for (int i = 0; i < images.Length; i++)
            {
                if (images[i] == null) continue;
                originals[i] = images[i].material == images[i].defaultMaterial ? null : images[i].material;
                images[i].material = revealMat;
            }
            return true;
        }

        void RestoreMaterials()
        {
            if (images == null || originals == null) return;
            for (int i = 0; i < images.Length; i++)
                if (images[i] != null && images[i].material == revealMat) images[i].material = originals[i];
        }
    }
}
