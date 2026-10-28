using System.IO;
using TheLivingCanvas.Ui;
using TMPro;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace TheLivingCanvas.EditorTools
{
    /// <summary>F0 de la UI nueva: importa TMP, crea el UITheme con sprites placeholder y la escena UI_Sandbox.</summary>
    public static class UIBuilder
    {
        const string UiDir = "Assets/_TheLivingCanvas/UI";
        const string PlaceholderDir = UiDir + "/Placeholders";
        const string ThemePath = "Assets/_TheLivingCanvas/Resources/UITheme.asset";
        const string SandboxPath = "Assets/_TheLivingCanvas/Scenes/UI_Sandbox.unity";
        const string MainMenuPath = "Assets/_TheLivingCanvas/Scenes/MainMenu.unity";
        const string TmpPackage = "Packages/com.unity.ugui/Package Resources/TMP Essential Resources.unitypackage";

        [MenuItem("TheLivingCanvas/UI/1 Import TMP Essentials")]
        static void ImportTmp()
        {
            if (Directory.Exists("Assets/TextMesh Pro")) { Debug.Log("TMP Essentials ya importado."); return; }
            AssetDatabase.ImportPackage(TmpPackage, false);
        }

        [MenuItem("TheLivingCanvas/UI/2 Create Theme (placeholders)")]
        static void CreateTheme()
        {
            Directory.CreateDirectory(PlaceholderDir);
            Directory.CreateDirectory(Path.GetDirectoryName(ThemePath));
            var theme = AssetDatabase.LoadAssetAtPath<UITheme>(ThemePath);
            if (theme == null)
            {
                theme = ScriptableObject.CreateInstance<UITheme>();
                AssetDatabase.CreateAsset(theme, ThemePath);
            }
            // Panel/barras/botones placeholder: rectángulo redondeado crema-tinta con borde; se sustituye por arte pintado.
            theme.panel = Make("panel", new Color32(0x2B, 0x22, 0x1B, 235), new Color32(0xE0, 0xCD, 0xB0, 90), 12, 2);
            theme.buttonNormal = Make("button_normal", new Color32(0x52, 0x6A, 0x83, 255), new Color32(0x86, 0x9B, 0xB2, 255), 9, 2);
            theme.buttonHover = Make("button_hover", new Color32(0x6A, 0x86, 0xA3, 255), new Color32(0xD4, 0xA7, 0x2C, 255), 9, 2);
            theme.buttonPressed = Make("button_pressed", new Color32(0x3E, 0x52, 0x66, 255), new Color32(0xD4, 0xA7, 0x2C, 255), 9, 2);
            theme.buttonDisabled = Make("button_disabled", new Color32(0x4A, 0x4A, 0x4A, 160), new Color32(0x80, 0x80, 0x80, 160), 9, 2);
            theme.barBack = Make("bar_back", new Color32(0x2B, 0x22, 0x1B, 200), new Color32(0xE0, 0xCD, 0xB0, 70), 6, 1);
            theme.barFill = Make("bar_fill", new Color32(0xD4, 0xA7, 0x2C, 255), new Color32(0xD4, 0xA7, 0x2C, 255), 6, 0);
            theme.tooltip = Make("tooltip", new Color32(0x2B, 0x22, 0x1B, 245), new Color32(0xD4, 0xA7, 0x2C, 110), 7, 1);
            theme.card = Make("card", new Color32(0xEC, 0xDF, 0xC6, 255), new Color32(0xA8, 0x8F, 0x68, 200), 8, 2);
            theme.slot = Make("slot", new Color32(0x3A, 0x2F, 0x26, 230), new Color32(0xE0, 0xCD, 0xB0, 80), 6, 1);

            var def = TMP_Settings.defaultFontAsset;
            if (def != null) { if (theme.bodyFont == null) theme.bodyFont = def; if (theme.titleFont == null) theme.titleFont = def; }
            else Debug.LogWarning("TMP Essentials no importado: ejecuta 'TheLivingCanvas/UI/1 Import TMP Essentials' y repite este paso.");

            EditorUtility.SetDirty(theme);
            AssetDatabase.SaveAssets();
            Selection.activeObject = theme;
        }

        [MenuItem("TheLivingCanvas/UI/3 Build UI Sandbox Scene")]
        static void BuildSandbox()
        {
            if (AssetDatabase.LoadAssetAtPath<UITheme>(ThemePath) == null) CreateTheme();
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var cam = new GameObject("Camera", typeof(Camera));
            var c = cam.GetComponent<Camera>();
            c.clearFlags = CameraClearFlags.SolidColor;
            c.backgroundColor = new Color32(0x1E, 0x2A, 0x38, 255);
            cam.tag = "MainCamera";

            var es = new GameObject("EventSystem", typeof(EventSystem), typeof(InputSystemUIInputModule));
            es.GetComponent<InputSystemUIInputModule>().AssignDefaultActions();

            var canvas = UIFactory.Canvas("Canvas");
            // Solo el sandbox: las capturas en modo Edit no incluyen canvas Overlay.
            canvas.renderMode = RenderMode.ScreenSpaceCamera;
            canvas.worldCamera = c;
            canvas.planeDistance = 1f;
            var th = UITheme.Current;
            var top = new Vector2(.5f, 1);
            var mid = new Vector2(.5f, .5f);

            // --- Izquierda: tipografia y paleta ---
            var pType = UIFactory.Panel("TypePanel", canvas.transform, new Vector2(560, 860));
            UIFactory.Place(pType.rectTransform, mid, mid, new Vector2(-620, 0), new Vector2(560, 860));
            var h = UIFactory.Label("Hdr", pType.transform, "Typography", UIFactory.TextStyle.Heading);
            UIFactory.Place(h.rectTransform, top, top, new Vector2(0, -30), new Vector2(500, 70));
            var t1 = UIFactory.Label("Title", pType.transform, "The Living Canvas", UIFactory.TextStyle.Title);
            t1.fontSize = 64; t1.color = th.warmYellow;
            UIFactory.Place(t1.rectTransform, top, top, new Vector2(0, -110), new Vector2(520, 90));
            var t2 = UIFactory.Label("Heading", pType.transform, "Heading - Gallery of the Garden", UIFactory.TextStyle.Heading);
            t2.fontSize = 36;
            UIFactory.Place(t2.rectTransform, top, top, new Vector2(0, -210), new Vector2(520, 60));
            var t3 = UIFactory.Label("Body", pType.transform, "Body - Every brushstroke remembers who painted it. Lora keeps long lines easy to read.", UIFactory.TextStyle.Body);
            t3.fontSize = 26;
            UIFactory.Place(t3.rectTransform, top, top, new Vector2(0, -290), new Vector2(500, 130));
            var t4 = UIFactory.Label("Small", pType.transform, "Small - [E] Interact   0123456789", UIFactory.TextStyle.Small);
            UIFactory.Place(t4.rectTransform, top, top, new Vector2(0, -430), new Vector2(500, 40));

            var names = new[] { "cerulean", "warmYellow", "olive", "terracotta", "greyBlue", "cream", "ink" };
            var cols = new[] { th.cerulean, th.warmYellow, th.olive, th.terracotta, th.greyBlue, th.cream, th.ink };
            for (int i = 0; i < cols.Length; i++)
            {
                var sw = UIFactory.Rect("Swatch_" + names[i], pType.transform);
                sw.gameObject.AddComponent<Image>().color = cols[i];
                UIFactory.Place(sw, top, top, new Vector2(-210 + i * 70, -520), new Vector2(60, 60));
                var l = UIFactory.Label("N_" + names[i], pType.transform, names[i], UIFactory.TextStyle.Small);
                l.fontSize = 11;
                UIFactory.Place(l.rectTransform, top, top, new Vector2(-210 + i * 70, -590), new Vector2(68, 30));
            }
            var onPaper = UIFactory.Rect("PaperSample", pType.transform);
            onPaper.gameObject.AddComponent<Image>().color = th.cream;
            UIFactory.Place(onPaper, top, top, new Vector2(0, -690), new Vector2(480, 80));
            var pl = UIFactory.Label("OnPaper", onPaper, "Ink on paper", UIFactory.TextStyle.Body);
            pl.color = th.ink; UIFactory.Stretch(pl.rectTransform);

            // --- Centro: controles y estados ---
            var panel = UIFactory.Panel("SamplePanel", canvas.transform, new Vector2(620, 860));
            UIFactory.Place(panel.rectTransform, mid, mid, Vector2.zero, new Vector2(620, 860));
            var ch = UIFactory.Label("Hdr", panel.transform, "Controls", UIFactory.TextStyle.Heading);
            UIFactory.Place(ch.rectTransform, top, top, new Vector2(0, -30), new Vector2(560, 70));
            float y = -120;
            string[] labels = { "Continue", "New Game", "Disabled" };
            for (int i = 0; i < labels.Length; i++)
            {
                var b = UIFactory.Button(labels[i] + "Button", panel.transform, labels[i], new Vector2(420, 72));
                UIFactory.Place((RectTransform)b.transform, top, top, new Vector2(0, y), new Vector2(420, 72));
                if (i == 2) b.interactable = false;
                y -= 90;
            }
            // Muestras de los sprites de estado (en Edit no se puede forzar hover/pressed).
            var states = new[] { th.buttonNormal, th.buttonHover, th.buttonPressed, th.buttonDisabled };
            var stateNames = new[] { "normal", "hover", "pressed", "disabled" };
            for (int i = 0; i < 4; i++)
            {
                var r = UIFactory.Rect("State_" + stateNames[i], panel.transform);
                var im = r.gameObject.AddComponent<Image>();
                im.sprite = states[i]; im.type = states[i] != null ? Image.Type.Sliced : Image.Type.Simple;
                if (states[i] == null) im.color = th.greyBlue;
                UIFactory.Place(r, top, top, new Vector2(-225 + i * 150, y - 10), new Vector2(130, 50));
                var l = UIFactory.Label("L_" + stateNames[i], r, stateNames[i], UIFactory.TextStyle.Small);
                l.fontSize = 16; UIFactory.Stretch(l.rectTransform); UIFactory.ContrastOnPaint(l);
            }
            y -= 90;
            var slider = UIFactory.Slider("VolumeSlider", panel.transform, new Vector2(420, 24), 0, 1, .7f);
            UIFactory.Place((RectTransform)slider.transform, top, top, new Vector2(0, y), new Vector2(420, 24));
            var slider2 = UIFactory.Slider("LowSlider", panel.transform, new Vector2(420, 24), 0, 1, .18f);
            UIFactory.Place((RectTransform)slider2.transform, top, top, new Vector2(0, y - 62), new Vector2(420, 24));
            y -= 125;
            var toggle = UIFactory.Toggle("FullscreenToggle", panel.transform, "Fullscreen", true);
            UIFactory.Place((RectTransform)toggle.transform, top, top, new Vector2(0, y), new Vector2(420, 48));
            y -= 70;
            var toggle2 = UIFactory.Toggle("SubtitlesToggle", panel.transform, "Subtitles", false);
            UIFactory.Place((RectTransform)toggle2.transform, top, top, new Vector2(0, y), new Vector2(420, 48));
            y -= 80;
            var back = UIFactory.Rect("BarBack", panel.transform);
            var bi = back.gameObject.AddComponent<Image>();
            bi.sprite = th.barBack; bi.type = th.barBack != null ? Image.Type.Sliced : Image.Type.Simple;
            if (th.barBack == null) bi.color = new Color(th.ink.r, th.ink.g, th.ink.b, .8f);
            UIFactory.Place(back, top, top, new Vector2(0, y), new Vector2(420, 26));
            var fill = UIFactory.Rect("BarFill", back);
            var fi = fill.gameObject.AddComponent<Image>();
            fi.sprite = th.barFill; fi.type = th.barFill != null ? Image.Type.Sliced : Image.Type.Simple;
            if (th.barFill == null) fi.color = th.olive;
            fill.anchorMin = Vector2.zero; fill.anchorMax = new Vector2(.62f, 1); fill.offsetMin = fill.offsetMax = Vector2.zero;

            // --- Derecha: piezas de HUD ---
            var pHud = UIFactory.Panel("HudPanel", canvas.transform, new Vector2(560, 860));
            UIFactory.Place(pHud.rectTransform, mid, mid, new Vector2(620, 0), new Vector2(560, 860));
            var hh = UIFactory.Label("Hdr", pHud.transform, "HUD pieces", UIFactory.TextStyle.Heading);
            UIFactory.Place(hh.rectTransform, top, top, new Vector2(0, -30), new Vector2(500, 70));
            int skins = Mathf.Min(th.SkinCount, 4);
            for (int i = 0; i < skins; i++)
            {
                Sprite blot, stroke; th.SkinSprites(i, out blot, out stroke);
                var row = UIFactory.Rect("Prompt_" + i, pHud.transform);
                UIFactory.Place(row, top, top, new Vector2(0, -130 - i * 100), new Vector2(480, 80));
                var sr = UIFactory.Rect("Stroke", row); UIFactory.Stretch(sr);
                var si = sr.gameObject.AddComponent<Image>(); si.sprite = stroke; si.color = stroke != null ? Color.white : new Color(th.ink.r, th.ink.g, th.ink.b, .6f);
                var kr = UIFactory.Rect("Key", row);
                UIFactory.Place(kr, new Vector2(0, .5f), new Vector2(0, .5f), new Vector2(40, 0), new Vector2(60, 60));
                var ki = kr.gameObject.AddComponent<Image>(); ki.sprite = blot; ki.color = blot != null ? Color.white : th.terracotta;
                var kl = UIFactory.Label("KeyL", kr, "E", UIFactory.TextStyle.Body); UIFactory.Stretch(kl.rectTransform); UIFactory.ContrastOnPaint(kl);
                var al = UIFactory.Label("Action", row, "Open the door", UIFactory.TextStyle.Body, TMPro.TextAlignmentOptions.Left);
                UIFactory.Place(al.rectTransform, new Vector2(0, .5f), new Vector2(0, .5f), new Vector2(240, 0), new Vector2(340, 60));
                UIFactory.ContrastOnPaint(al);
            }
            string[] kinds = { "Info - The gallery is quiet", "Reward - +30 coins", "Saved" };
            Color[] kc = { th.cerulean, th.warmYellow, th.olive };
            for (int i = 0; i < kinds.Length; i++)
            {
                var card = UIFactory.Rect("Note_" + i, pHud.transform);
                UIFactory.Place(card, top, top, new Vector2(0, -560 - i * 80), new Vector2(480, 64));
                card.gameObject.AddComponent<Image>().color = new Color(th.ink.r, th.ink.g, th.ink.b, .88f);
                var bar = UIFactory.Rect("Accent", card);
                bar.anchorMin = Vector2.zero; bar.anchorMax = new Vector2(0, 1); bar.sizeDelta = new Vector2(8, 0); bar.anchoredPosition = new Vector2(4, 0);
                bar.gameObject.AddComponent<Image>().color = kc[i];
                var cl = UIFactory.Label("T", card, kinds[i], UIFactory.TextStyle.Small, TMPro.TextAlignmentOptions.Left);
                cl.rectTransform.anchorMin = Vector2.zero; cl.rectTransform.anchorMax = Vector2.one;
                cl.rectTransform.offsetMin = new Vector2(24, 0); cl.rectTransform.offsetMax = new Vector2(-8, 0);
            }

            Directory.CreateDirectory(Path.GetDirectoryName(SandboxPath));
            EditorSceneManager.SaveScene(scene, SandboxPath);
        }

        [MenuItem("TheLivingCanvas/UI/4 Build MainMenu Scene + Build Settings")]
        static void BuildMainMenu()
        {
            if (AssetDatabase.LoadAssetAtPath<UITheme>(ThemePath) == null) CreateTheme();
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var cam = new GameObject("Camera", typeof(Camera), typeof(AudioListener));
            var c = cam.GetComponent<Camera>();
            c.clearFlags = CameraClearFlags.SolidColor;
            c.backgroundColor = new Color32(0x1E, 0x2A, 0x38, 255);
            cam.tag = "MainCamera";

            var es = new GameObject("EventSystem", typeof(EventSystem), typeof(InputSystemUIInputModule));
            es.GetComponent<InputSystemUIInputModule>().AssignDefaultActions();
            new GameObject("MainMenu", typeof(TheLivingCanvas.Ui.MainMenu));

            Directory.CreateDirectory(Path.GetDirectoryName(MainMenuPath));
            EditorSceneManager.SaveScene(scene, MainMenuPath);

            const string museum = "Assets/_TheLivingCanvas/Scenes/Museum.unity";
            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene(MainMenuPath, true),
                new EditorBuildSettingsScene(museum, true),
            };
            Debug.Log("MainMenu creada; Build Settings: 0 MainMenu, 1 Museum.");
        }

        const string PresetsPath = "Assets/_TheLivingCanvas/Resources/UIAnimPresets.asset";
        const string DemoPath = "Assets/_TheLivingCanvas/Scenes/UI_PaintedDemo.unity";
        const string RevealShaderPath = "Assets/_TheLivingCanvas/Art/Shaders/TLC_UIPaintReveal.shader";

        [MenuItem("TheLivingCanvas/UI/5 Create Anim Presets + Painted Demo")]
        static void BuildPaintedDemo()
        {
            Directory.CreateDirectory(Path.GetDirectoryName(PresetsPath));
            var presets = AssetDatabase.LoadAssetAtPath<UIAnimPresets>(PresetsPath);
            if (presets == null)
            {
                presets = ScriptableObject.CreateInstance<UIAnimPresets>();
                AssetDatabase.CreateAsset(presets, PresetsPath);
            }
            presets.paintRevealShader = AssetDatabase.LoadAssetAtPath<Shader>(RevealShaderPath);
            EditorUtility.SetDirty(presets);
            AssetDatabase.SaveAssets();

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var cam = new GameObject("Camera", typeof(Camera));
            var c = cam.GetComponent<Camera>();
            c.clearFlags = CameraClearFlags.SolidColor;
            c.backgroundColor = new Color32(0x3A, 0x32, 0x2A, 255);
            cam.tag = "MainCamera";

            var canvas = UIFactory.Canvas("Canvas");
            canvas.renderMode = RenderMode.ScreenSpaceCamera; // solo la demo: capturable en modo Edit
            canvas.worldCamera = c;
            canvas.planeDistance = 1f;
            var t = UITheme.Current;

            Sprite[] sprites = { BrushStrokes.Stroke(1), BrushStrokes.Blot(2), BrushStrokes.Ring(3), BrushStrokes.Stroke(4, 256, 48), BrushStrokes.Stroke(5, 256, 48), BrushStrokes.Stroke(6, 256, 48) };
            UIAnimKind[] kinds = { UIAnimKind.BrushReveal, UIAnimKind.InkReveal, UIAnimKind.Dissolve, UIAnimKind.SoftSlide, UIAnimKind.SoftScale, UIAnimKind.PageTurn };
            Color[] colors = { t.warmYellow, t.terracotta, t.cerulean, t.olive, t.cream, t.greyBlue };
            for (int i = 0; i < kinds.Length; i++)
            {
                int col = i % 3, row = i / 3;
                var cell = UIFactory.Rect(kinds[i].ToString(), canvas.transform);
                UIFactory.Place(cell, new Vector2(.5f, .5f), new Vector2(.5f, .5f), new Vector2((col - 1) * 520, 160 - row * 330), new Vector2(440, 220));
                var img = UIFactory.Rect("Sprite", cell).gameObject.AddComponent<Image>();
                UIFactory.Place(img.rectTransform, new Vector2(.5f, .5f), new Vector2(.5f, .5f), new Vector2(0, 20), i == 1 ? new Vector2(150, 150) : i == 2 ? new Vector2(190, 190) : new Vector2(400, 80));
                img.sprite = sprites[i]; img.color = colors[i]; img.raycastTarget = false;
                var lab = UIFactory.Label("Name", cell, kinds[i].ToString(), UIFactory.TextStyle.Small);
                UIFactory.Place(lab.rectTransform, new Vector2(.5f, 0), new Vector2(.5f, 0), new Vector2(0, 0), new Vector2(400, 36));
                var anim = cell.gameObject.AddComponent<UIAnimator>();
                var so = new SerializedObject(anim);
                so.FindProperty("showPreset").enumValueIndex = (int)kinds[i];
                so.FindProperty("hidePreset").enumValueIndex = (int)UIAnimKind.FadeOut;
                so.FindProperty("deactivateOnHide").boolValue = false;
                so.FindProperty("seed").floatValue = i * 3.7f;
                so.ApplyModifiedPropertiesWithoutUndo();
                var loop = cell.gameObject.AddComponent<UIAnimDemoLoop>();
                var lso = new SerializedObject(loop);
                lso.FindProperty("offset").floatValue = i * 0.4f;
                lso.ApplyModifiedPropertiesWithoutUndo();
            }
            Directory.CreateDirectory(Path.GetDirectoryName(DemoPath));
            EditorSceneManager.SaveScene(scene, DemoPath);
        }

        static Sprite Make(string name, Color32 fill, Color32 border, int radius, int borderPx)
        {
            // 128 px, bordes suavizados y algo irregulares (no un rectangulo perfecto); 9-slice con borde = esquina.
            const int size = 128;
            int r = radius * 2;
            float bw = Mathf.Max(borderPx, 0) * 1.0f;
            var px = new Color32[size * size];
            float sx = (name.GetHashCode() & 0xFF) * .37f, sy = ((name.GetHashCode() >> 8) & 0xFF) * .21f;
            for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    float dx = Mathf.Max(r - x - .5f, x + .5f - (size - r), 0);
                    float dy = Mathf.Max(r - y - .5f, y + .5f - (size - r), 0);
                    float inside = r - Mathf.Sqrt(dx * dx + dy * dy);
                    // Irregularidad suave del contorno (hecha a mano), solo en el borde.
                    inside += (Mathf.PerlinNoise(x * .09f + 3.1f, y * .09f + 7.7f) - .5f) * 1.6f;
                    float cover = Mathf.Clamp01(inside + .5f); // alfa antialias del contorno exterior
                    float inBorder = bw > 0 ? Mathf.Clamp01(bw + .5f - inside) : 0f; // 1 en el anillo del borde
                    // Cerdas de pincel: vetas horizontales de brillo (direccion y escala propositivas, no ruido uniforme).
                    float streak = (Mathf.PerlinNoise(x * .035f + sx, y * .5f + sy) - .5f) * .16f
                                 + (Mathf.PerlinNoise(x * .13f + sy, y * 1.1f + sx) - .5f) * .06f;
                    Color f = fill, bc = border;
                    f.r = Mathf.Clamp01(f.r * (1f + streak)); f.g = Mathf.Clamp01(f.g * (1f + streak)); f.b = Mathf.Clamp01(f.b * (1f + streak));
                    Color c = Color.Lerp(f, bc, inBorder * bc.a);
                    c.a = Mathf.Lerp(f.a, Mathf.Max(f.a, bc.a), inBorder) * cover;
                    px[y * size + x] = c;
                }
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
            tex.SetPixels32(px);
            tex.Apply();
            string path = $"{PlaceholderDir}/{name}.png";
            File.WriteAllBytes(path, tex.EncodeToPNG());
            Object.DestroyImmediate(tex);
            AssetDatabase.ImportAsset(path);
            var imp = (TextureImporter)AssetImporter.GetAtPath(path);
            imp.textureType = TextureImporterType.Sprite;
            imp.spriteImportMode = SpriteImportMode.Single;
            int bd = r + 2;
            imp.spriteBorder = new Vector4(bd, bd, bd, bd);
            imp.spritePixelsPerUnit = 100;
            imp.filterMode = FilterMode.Bilinear;
            imp.mipmapEnabled = false;
            imp.alphaIsTransparency = true;
            imp.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Sprite>(path);
        }
    }
}
