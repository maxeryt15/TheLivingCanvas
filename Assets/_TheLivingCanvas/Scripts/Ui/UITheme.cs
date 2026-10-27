using TMPro;
using UnityEngine;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// Tema único de la interfaz: paleta, fuentes, sprites 9-slice y tiempos. Vive en Resources/UITheme.asset.
    /// Los sprites son placeholders hasta que el usuario entregue los pintados; basta con reasignarlos aquí.
    /// </summary>
    [CreateAssetMenu(menuName = "TheLivingCanvas/UI Theme", fileName = "UITheme")]
    public class UITheme : ScriptableObject
    {
        [Header("Palette (ART_DIRECTION)")]
        public Color cerulean = new Color32(0x52, 0x6A, 0x83, 255);
        public Color warmYellow = new Color32(0xD4, 0xA7, 0x2C, 255);
        public Color olive = new Color32(0x65, 0x78, 0x5A, 255);
        public Color terracotta = new Color32(0xA8, 0x5F, 0x47, 255);
        public Color greyBlue = new Color32(0x74, 0x79, 0x83, 255);
        public Color cream = new Color32(0xE0, 0xCD, 0xB0, 255);
        public Color ink = new Color32(0x2B, 0x22, 0x1B, 255);

        [Header("Fonts")]
        public TMP_FontAsset titleFont;
        public TMP_FontAsset bodyFont;

        [Header("Sprites (9-slice)")]
        public Sprite panel;
        public Sprite buttonNormal;
        public Sprite buttonHover;
        public Sprite buttonPressed;
        public Sprite buttonDisabled;
        public Sprite barBack;
        public Sprite barFill;
        public Sprite divider;
        public Sprite reticle;
        [Tooltip("Mancha pintada tras la tecla del prompt (si falta, se usa una procedural lisa).")]
        public Sprite keyBlot;
        [Tooltip("Trazo pintado de fondo del prompt de interacción.")]
        public Sprite promptStroke;
        public Sprite menuBackground;

        [System.Serializable]
        public class PromptSkin { public string name; public Sprite blot, stroke; }

        [Tooltip("Variantes del prompt inspiradas en cuadros de Van Gogh. El índice activo está en PlayerPrefs 'ui.promptSkin' (-2 = ciclar, -1 = Classic = keyBlot/promptStroke).")]
        public PromptSkin[] promptSkins;
        [Tooltip("Texturas pintadas de pantalla completa para las transiciones; mismo índice que las variantes (0 = Classic).")]
        public Sprite[] transitionCovers;
        public const string PromptSkinKey = "ui.promptSkin";

        /// <summary>Valor guardado: -2 = ciclar todas (por defecto), -1 = solo Classic, 0.. = variante fija.</summary>
        public int SavedSkin => PlayerPrefs.GetInt(PromptSkinKey, -2);
        public bool CycleSkins => SavedSkin == -2 && SkinCount > 1;
        /// <summary>Classic (índice 0) + variantes.</summary>
        public int SkinCount => 1 + (promptSkins != null ? promptSkins.Length : 0);

        /// <summary>Sprites de la variante i (0 = Classic, 1.. = promptSkins[i-1]).</summary>
        public void SkinSprites(int i, out Sprite blot, out Sprite stroke)
        {
            if (i > 0 && promptSkins != null && i <= promptSkins.Length && promptSkins[i - 1].blot != null)
            { blot = promptSkins[i - 1].blot; stroke = promptSkins[i - 1].stroke; }
            else { blot = keyBlot; stroke = promptStroke; }
        }

        [Header("Type sizes (reference 1920x1080)")]
        public float titleSize = 96f;
        public float headingSize = 48f;
        public float bodySize = 30f;
        public float smallSize = 22f;

        [Header("Timing (seconds, unscaled)")]
        public float panelOpen = 0.15f;
        public float panelClose = 0.12f;
        public float buttonFade = 0.08f;

        static UITheme current;

        public static UITheme Current
        {
            get
            {
                if (current == null) current = Resources.Load<UITheme>("UITheme");
                if (current == null) current = CreateInstance<UITheme>();
                return current;
            }
        }

        public Color PanelTint => new Color(ink.r, ink.g, ink.b, 0.88f);
        public TMP_FontAsset Title => titleFont != null ? titleFont : bodyFont;
    }
}
