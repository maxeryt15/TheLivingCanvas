using System.IO;
using TheLivingCanvas.Core;
using TheLivingCanvas.Save;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// Pantalla de inicio. Construye su interfaz con UIFactory al arrancar (la escena solo lleva cámara,
    /// EventSystem y este componente): Continue / New Game / Settings / Quit, con confirmación y ajustes.
    /// </summary>
    public class MainMenu : MonoBehaviour
    {
        GameObject mainGroup, settingsPanel, confirmPanel;
        Button continueButton, newGameButton, confirmNo;
        SettingsPanel settings;
        RectTransform backdrop;

        void Awake()
        {
            Time.timeScale = 1f;
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
            GameSettings.ApplySaved();
            Build();
        }

        void Start() => Select(continueButton.gameObject.activeSelf ? continueButton : newGameButton);

        static void Select(Selectable s)
        {
            if (EventSystem.current != null) EventSystem.current.SetSelectedGameObject(s.gameObject);
        }

        void Build()
        {
            var t = UITheme.Current;
            var canvas = UIFactory.Canvas("MenuCanvas");
            canvas.transform.SetParent(transform, false);

            BuildBackdrop(canvas.transform);

            mainGroup = UIFactory.Rect("Main", canvas.transform).gameObject;
            UIFactory.Stretch((RectTransform)mainGroup.transform);

            var title = UIFactory.Label("Title", mainGroup.transform, "The Living Canvas", UIFactory.TextStyle.Title, TextAlignmentOptions.Left);
            UIFactory.ContrastOnPaint(title, 0.35f);
            title.outlineColor = t.OutlineDark;
            UIFactory.Place(title.rectTransform, new Vector2(0, .5f), new Vector2(0, .5f), new Vector2(160, 200), new Vector2(1100, 130));

            bool hasSave = File.Exists(SaveManager.SavePath);
            continueButton = MenuButton("Continue", 70, () => SceneLoader.Load(SceneLoader.GameScene));
            continueButton.gameObject.SetActive(hasSave);
            newGameButton = MenuButton("New Game", hasSave ? -20 : 70, OnNewGame);
            var settingsButton = MenuButton("Settings", hasSave ? -110 : -20, OpenSettings);
            var quitButton = MenuButton("Quit", hasSave ? -200 : -110, Quit);
#if UNITY_WEBGL
            quitButton.gameObject.SetActive(false);
#endif
            settings = SettingsPanel.Create(canvas.transform, CloseSettings);
            settingsPanel = settings.Root;
            BuildConfirm(canvas.transform);
        }

        // Fondo: papel, el paisaje pintado de la pantalla de carga (cubre toda la pantalla, con deriva lenta) y un velo oscuro a la izquierda.
        void BuildBackdrop(Transform parent)
        {
            var t = UITheme.Current;
            var cfg = LoadingScreenSettings.Current;
            var v = cfg.variants != null && cfg.variants.Length > 0 ? cfg.variants[0] : null;

            var bg = UIFactory.Rect("Background", parent);
            UIFactory.Stretch(bg);
            var paper = bg.gameObject.AddComponent<Image>();
            paper.sprite = v != null ? v.paper : t.menuBackground;
            paper.color = v != null ? v.paperTint : t.cerulean * 0.45f;
            paper.raycastTarget = false;

            if (v != null && v.painted != null)
            {
                var art = UIFactory.Rect("Painting", bg);
                UIFactory.Stretch(art);
                var fit = art.gameObject.AddComponent<AspectRatioFitter>();
                fit.aspectMode = AspectRatioFitter.AspectMode.EnvelopeParent;
                fit.aspectRatio = (float)v.painted.rect.width / v.painted.rect.height;
                var img = art.gameObject.AddComponent<Image>();
                img.sprite = v.painted;
                img.raycastTarget = false;
                backdrop = art;
            }

            // Velo oscuro en el lado del texto (degradado horizontal a partir del sprite suave)
            var shade = UIFactory.Rect("Shade", bg);
            shade.anchorMin = new Vector2(0, 0); shade.anchorMax = new Vector2(0, 1);
            shade.pivot = new Vector2(0, .5f);
            shade.anchoredPosition = Vector2.zero;
            shade.sizeDelta = new Vector2(1250, 0);
            var shadeImg = shade.gameObject.AddComponent<Image>();
            shadeImg.sprite = HorizontalFade();
            shadeImg.color = t.Shade(.85f);
            shadeImg.raycastTarget = false;
        }

        /// <summary>Degradado de opaco (izquierda) a transparente (derecha), blanco: se tiñe con Image.color.</summary>
        static Sprite HorizontalFade()
        {
            const int w = 64;
            var tex = new Texture2D(w, 2, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };
            for (int x = 0; x < w; x++)
            {
                float a = Mathf.SmoothStep(1f, 0f, x / (w - 1f));
                for (int y = 0; y < 2; y++) tex.SetPixel(x, y, new Color(1, 1, 1, a));
            }
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, w, 2), new Vector2(.5f, .5f));
        }

        void Update()
        {
            if (backdrop != null && !GameSettings.ReducedMotion)
            {
                float k = 1.04f + 0.02f * Mathf.Sin(Time.unscaledTime * 0.1f);
                backdrop.localScale = new Vector3(k, k, 1f);
                backdrop.anchoredPosition = new Vector2(Mathf.Sin(Time.unscaledTime * 0.07f) * 18f, Mathf.Cos(Time.unscaledTime * 0.05f) * 10f);
            }
            if (Keyboard.current == null && Gamepad.current == null) return;
            bool back = (Keyboard.current != null && Keyboard.current.escapeKey.wasPressedThisFrame)
                        || (Gamepad.current != null && Gamepad.current.buttonEast.wasPressedThisFrame);
            if (!back) return;
            if (settingsPanel.activeSelf) CloseSettings();
            else if (confirmPanel.activeSelf) CloseConfirm();
        }

        // Botón sin caja: solo texto; al pasar el ratón o seleccionarlo, un trazo pintado se desvanece detrás.
        Button MenuButton(string label, float y, UnityEngine.Events.UnityAction onClick)
        {
            var t = UITheme.Current;
            var r = UIFactory.Rect(label + "Button", mainGroup.transform);
            UIFactory.Place(r, new Vector2(0, .5f), new Vector2(0, .5f), new Vector2(160, y), new Vector2(520, 76));
            var stroke = r.gameObject.AddComponent<Image>();
            stroke.sprite = t.promptStroke;
            stroke.type = Image.Type.Simple;
            stroke.color = t.promptStroke != null ? Color.white : t.cerulean;
            var b = r.gameObject.AddComponent<Button>();
            b.targetGraphic = stroke;
            b.transition = Selectable.Transition.ColorTint;
            b.colors = new ColorBlock
            {
                normalColor = new Color(1, 1, 1, 0), highlightedColor = new Color(1, 1, 1, .9f), selectedColor = new Color(1, 1, 1, .9f),
                pressedColor = new Color(.8f, .8f, .8f, 1f), disabledColor = new Color(1, 1, 1, 0), colorMultiplier = 1f, fadeDuration = .18f
            };
            var l = UIFactory.Label("Label", r, label, UIFactory.TextStyle.Heading, TextAlignmentOptions.Left);
            UIFactory.ContrastOnPaint(l, 0.4f);
            l.outlineColor = t.OutlineDark;
            UIFactory.Stretch(l.rectTransform);
            l.rectTransform.offsetMin = new Vector2(44, 0);
            b.onClick.AddListener(onClick);
            return b;
        }

        // ---------- Acciones ----------

        void OnNewGame()
        {
            if (File.Exists(SaveManager.SavePath)) OpenConfirm();
            else SceneLoader.Load(SceneLoader.GameScene);
        }

        void StartFresh()
        {
            try { if (File.Exists(SaveManager.SavePath)) File.Delete(SaveManager.SavePath); }
            catch (System.Exception e) { Debug.LogException(e); }
            PaintingStore.DeleteAll();
            SceneLoader.Load(SceneLoader.GameScene);
        }

        static void Quit()
        {
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }

        // ---------- Confirmación de New Game ----------

        void BuildConfirm(Transform parent)
        {
            var p = UIFactory.Panel("ConfirmPanel", parent, new Vector2(760, 340));
            UIFactory.Place(p.rectTransform, new Vector2(.5f, .5f), new Vector2(.5f, .5f), Vector2.zero, new Vector2(760, 340));
            confirmPanel = p.gameObject;
            var l = UIFactory.Label("Text", p.transform, "Start a new game?\nYour saved game and paintings will be deleted.", UIFactory.TextStyle.Body);
            UIFactory.Place(l.rectTransform, new Vector2(.5f, 1), new Vector2(.5f, 1), new Vector2(0, -50), new Vector2(680, 120));
            var yes = UIFactory.Button("YesButton", p.transform, "Delete and start", new Vector2(320, 68));
            UIFactory.Place((RectTransform)yes.transform, new Vector2(.5f, 0), new Vector2(.5f, 0), new Vector2(-180, 50), new Vector2(320, 68));
            yes.onClick.AddListener(StartFresh);
            confirmNo = UIFactory.Button("NoButton", p.transform, "Cancel", new Vector2(260, 68));
            UIFactory.Place((RectTransform)confirmNo.transform, new Vector2(.5f, 0), new Vector2(.5f, 0), new Vector2(190, 50), new Vector2(260, 68));
            confirmNo.onClick.AddListener(CloseConfirm);
            confirmPanel.SetActive(false);
        }

        void OpenConfirm() { mainGroup.SetActive(false); confirmPanel.SetActive(true); Select(confirmNo); }
        void CloseConfirm() { confirmPanel.SetActive(false); mainGroup.SetActive(true); Select(newGameButton); }

        // ---------- Ajustes ----------

        void OpenSettings() { mainGroup.SetActive(false); settingsPanel.SetActive(true); Select(settings.First); }
        void CloseSettings() { PlayerPrefs.Save(); settingsPanel.SetActive(false); mainGroup.SetActive(true); Select(newGameButton); }
    }
}
