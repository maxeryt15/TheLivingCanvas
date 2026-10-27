using System;
using UnityEngine;

namespace TheLivingCanvas.Ui
{
    public enum UIAnimKind { FadeIn, FadeOut, SoftScale, SoftSlide, BrushReveal, InkReveal, PageTurn, Dissolve }

    /// <summary>Un preset de animación: todo configurable desde el Inspector.</summary>
    [Serializable]
    public class UIAnimPreset
    {
        public UIAnimKind kind;
        [Min(0.01f)] public float duration = 0.35f;
        [Min(0f)] public float delay;
        [Tooltip("Curva suave 0→1; evita rebotes y sobrepasos.")]
        public AnimationCurve curve = AnimationCurve.EaseInOut(0, 0, 1, 1);
        [Tooltip("SoftScale / PageTurn: escala inicial al aparecer.")]
        public float fromScale = 0.96f;
        [Tooltip("SoftSlide: desplazamiento inicial en unidades del canvas.")]
        public Vector2 slide = new Vector2(0, -24);
        [Tooltip("Reveal/Dissolve: suavidad del borde del revelado.")]
        [Range(0.01f, 0.5f)] public float edgeSoftness = 0.15f;
    }

    /// <summary>
    /// Biblioteca central de presets (Resources/UIAnimPresets.asset). Si falta el asset o un preset,
    /// se usan los valores por defecto de <see cref="Default"/>.
    /// </summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/UI Anim Presets", fileName = "UIAnimPresets")]
    public class UIAnimPresets : ScriptableObject
    {
        public UIAnimPreset[] presets = DefaultSet();
        [Tooltip("Shader TLC/UI/PaintReveal; la referencia lo incluye en las builds.")]
        public Shader paintRevealShader;

        static UIAnimPresets current;

        public static UIAnimPresets Current
        {
            get
            {
                if (current == null) current = Resources.Load<UIAnimPresets>("UIAnimPresets");
                return current;
            }
        }

        public static UIAnimPreset Get(UIAnimKind kind)
        {
            var c = Current;
            if (c != null && c.presets != null)
                foreach (var p in c.presets) if (p != null && p.kind == kind) return p;
            return Default(kind);
        }

        public static Shader RevealShader =>
            Current != null && Current.paintRevealShader != null ? Current.paintRevealShader : Shader.Find("TLC/UI/PaintReveal");

        public static UIAnimPreset Default(UIAnimKind kind)
        {
            var p = new UIAnimPreset { kind = kind };
            switch (kind)
            {
                case UIAnimKind.FadeIn: p.duration = 0.4f; break;
                case UIAnimKind.FadeOut: p.duration = 0.3f; break;
                case UIAnimKind.SoftScale: p.duration = 0.35f; p.fromScale = 0.96f; break;
                case UIAnimKind.SoftSlide: p.duration = 0.45f; break;
                case UIAnimKind.BrushReveal: p.duration = 0.7f; p.edgeSoftness = 0.18f; break;
                case UIAnimKind.InkReveal: p.duration = 0.9f; p.edgeSoftness = 0.2f; break;
                case UIAnimKind.PageTurn: p.duration = 0.55f; p.fromScale = 0.04f; break;
                case UIAnimKind.Dissolve: p.duration = 0.8f; p.edgeSoftness = 0.12f; break;
            }
            return p;
        }

        static UIAnimPreset[] DefaultSet()
        {
            var kinds = (UIAnimKind[])Enum.GetValues(typeof(UIAnimKind));
            var set = new UIAnimPreset[kinds.Length];
            for (int i = 0; i < kinds.Length; i++) set[i] = Default(kinds[i]);
            return set;
        }
    }
}
