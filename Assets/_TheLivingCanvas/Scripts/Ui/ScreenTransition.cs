using System.Collections;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// Transiciones de pantalla completa: Cover cubre la vista, Uncover la descubre. Un único lienzo persistente
    /// (sobre el HUD, bajo la pantalla de carga). Los tipos pintados usan el shader TLC/UI/PaintReveal; con
    /// Reduced motion todo se convierte en un fundido corto. Uso: yield return ScreenTransition.Cover(Kind.Brush);
    /// </summary>
    public class ScreenTransition : MonoBehaviour
    {
        public enum Kind
        {
            Fade,     // fundido liso a tinta oscura
            Brush,    // pincelada ancha que barre la pantalla
            Paper,    // fundido a papel crema
            Ink,      // la pintura se extiende desde el centro
            Dissolve  // disolución de tinta, a manchas
        }

        const int SortingOrder = 900;
        static ScreenTransition instance;

        Image image;
        Material mat;
        Kind shown = Kind.Fade;
        float amount; // 0 = descubierto, 1 = cubierto

        public static bool IsCovered => instance != null && instance.amount > 0.001f;

        /// <summary>Color con el que cubre cada tipo si no se indica otro.</summary>
        public static Color DefaultColor(Kind kind)
        {
            var t = UITheme.Current;
            switch (kind)
            {
                case Kind.Paper: return t.cream;
                case Kind.Ink: return Color.Lerp(t.ink, t.cerulean, .35f);
                case Kind.Fade: return new Color(t.ink.r * .45f, t.ink.g * .45f, t.ink.b * .45f, 1f);
                default: return t.ink;
            }
        }

        static int lastCover = -1;

        /// <summary>Cubre con la textura pintada de una variante al azar (distinta de la anterior); Fade y Paper son lisos.</summary>
        public static IEnumerator Cover(Kind kind, float seconds = 0.7f)
        {
            var t = UITheme.Current;
            int n = t.transitionCovers != null ? t.transitionCovers.Length : 0;
            int skin = -1;
            if (n > 0 && kind != Kind.Fade && kind != Kind.Paper)
            {
                do skin = Random.Range(0, n); while (n > 1 && skin == lastCover);
                lastCover = skin;
            }
            return Cover(kind, seconds, skin);
        }

        /// <summary>Cubre con un color liso (p. ej. el papel de la pantalla de carga) usando el movimiento del tipo dado.</summary>
        public static IEnumerator Cover(Kind kind, Color color, float seconds)
        {
            var s = Get();
            s.Prepare(kind, color, null);
            yield return s.Animate(s.amount, 1f, seconds);
        }

        /// <summary>skin: índice de la textura pintada (variante del prompt, 0 = Classic); -1 = color liso.</summary>
        public static IEnumerator Cover(Kind kind, float seconds, int skin)
        {
            var t = UITheme.Current;
            Sprite paint = skin >= 0 && t.transitionCovers != null && skin < t.transitionCovers.Length ? t.transitionCovers[skin] : null;
            var s = Get();
            s.Prepare(kind, paint != null ? Color.white : DefaultColor(kind), paint);
            yield return s.Animate(s.amount, 1f, seconds);
        }

        public static IEnumerator Uncover(float seconds = 0.8f)
        {
            if (instance == null) yield break;
            yield return instance.Animate(instance.amount, 0f, seconds);
        }

        /// <summary>Descubre al instante (p. ej. al volver al menú desde una escena que se destruye).</summary>
        public static void Clear()
        {
            if (instance != null) instance.Apply(0f);
        }

        static ScreenTransition Get()
        {
            if (instance != null) return instance;
            var go = new GameObject("ScreenTransition");
            DontDestroyOnLoad(go);
            instance = go.AddComponent<ScreenTransition>();
            instance.Build();
            return instance;
        }

        void Build()
        {
            var canvas = UIFactory.Canvas("TransitionCanvas", SortingOrder);
            canvas.transform.SetParent(transform, false);
            var r = UIFactory.Rect("Cover", canvas.transform);
            UIFactory.Stretch(r);
            image = r.gameObject.AddComponent<Image>();
            image.sprite = UIFactory.DotSprite();
            image.type = Image.Type.Simple;
            image.raycastTarget = false;
            Apply(0f);
        }

        void Prepare(Kind kind, Color color, Sprite paint)
        {
            // Con Reduced motion todo es un fundido (y si falta el shader también).
            var effective = Core.GameSettings.ReducedMotion ? Kind.Fade : kind;
            var shader = UIAnimPresets.RevealShader;
            bool painted = effective == Kind.Brush || effective == Kind.Ink || effective == Kind.Dissolve;
            if (painted && shader == null) { effective = Kind.Fade; painted = false; }
            shown = effective;
            image.color = color;
            // Textura pintada de la variante, o un sprite lleno (el del círculo tiene bordes transparentes).
            image.sprite = paint != null ? paint : FullSprite();
            if (painted)
            {
                if (mat == null) mat = new Material(shader) { hideFlags = HideFlags.DontSave };
                foreach (var k in new[] { "_MODE_BRUSH", "_MODE_INK", "_MODE_DISSOLVE" }) mat.DisableKeyword(k);
                mat.EnableKeyword(effective == Kind.Brush ? "_MODE_BRUSH" : effective == Kind.Ink ? "_MODE_INK" : "_MODE_DISSOLVE");
                mat.SetFloat("_Soft", effective == Kind.Brush ? .18f : effective == Kind.Ink ? .2f : .12f);
                mat.SetFloat("_Seed", Random.Range(0f, 50f));
                image.material = mat;
            }
            else image.material = null;
        }

        static Sprite full;
        static Sprite FullSprite()
        {
            if (full != null) return full;
            var tex = new Texture2D(4, 4, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp };
            var px = new Color32[16];
            for (int i = 0; i < px.Length; i++) px[i] = new Color32(255, 255, 255, 255);
            tex.SetPixels32(px); tex.Apply();
            full = Sprite.Create(tex, new Rect(0, 0, 4, 4), new Vector2(.5f, .5f), 100f);
            return full;
        }

        IEnumerator Animate(float from, float to, float seconds)
        {
            if (Core.GameSettings.ReducedMotion) seconds = Mathf.Min(seconds, 0.2f);
            image.raycastTarget = to > from || amount > 0.001f; // mientras cubre, bloquea clics
            for (float e = 0; e < seconds; e += Time.unscaledDeltaTime)
            {
                Apply(Mathf.Lerp(from, to, Mathf.SmoothStep(0f, 1f, e / seconds)));
                yield return null;
            }
            Apply(to);
            image.raycastTarget = to > 0.001f;
        }

        void Apply(float a)
        {
            amount = a;
            if (image == null) return;
            image.enabled = a > 0.001f;
            if (shown == Kind.Fade || shown == Kind.Paper || image.material == image.defaultMaterial)
            {
                var c = image.color; c.a = a; image.color = c;
            }
            else
            {
                var c = image.color; c.a = 1f; image.color = c;
                mat.SetFloat("_Reveal", a);
            }
        }
    }
}
