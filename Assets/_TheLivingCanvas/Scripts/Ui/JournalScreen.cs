using System.Collections;
using System.Collections.Generic;
using TheLivingCanvas.Core;
using TheLivingCanvas.Economy;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Painting;
using TheLivingCanvas.Player;
using TheLivingCanvas.Progression;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace TheLivingCanvas.Ui
{
    /// <summary>
    /// Cuaderno del jugador (I / Tab / Y): pestaña Satchel (objetos, pigmentos, monedas y nivel) y pestaña Notes
    /// (notas que añade el juego con <see cref="AddNote"/>). Solo lectura. Libera el cursor mientras está abierto;
    /// Esc / B / la misma tecla lo cierran. Se construye por código al arrancar.
    /// </summary>
    public class JournalScreen : MonoBehaviour
    {
        const float FadeSeconds = 0.18f;
        const int MaxRows = 8, MaxNotes = 6;
        const float RowHeight = 64f;
        static readonly Vector2 PanelSize = new Vector2(1500, 860);

        struct Note { public string Title, Text; }
        static readonly List<Note> notes = new List<Note>();

        /// <summary>Fotograma en que se cerró: la pausa no debe usar el mismo Esc.</summary>
        public static int ClosedFrame { get; private set; } = -1;
        public static JournalScreen Instance { get; private set; }
        public bool IsOpen { get; private set; }

        /// <summary>Añade una nota a la pestaña Notes (no se guarda en la partida todavía).</summary>
        public static void AddNote(string title, string text)
        {
            notes.Add(new Note { Title = title, Text = text });
            Notifications.Show("New journal note: " + title);
            if (Instance != null && Instance.IsOpen) Instance.Refresh();
        }

        CursorLock cursorLock;
        CameraModeController cameraMode;
        PlayerInteractor interactor;
        PaintModeController paintMode;
        PlayerInventory inventory;
        PigmentStock pigments;
        Wallet wallet;
        ArtistLevel level;

        CanvasGroup group;
        GameObject satchelPage, notesPage;
        RectTransform itemList, pigmentList, notesList;
        TextMeshProUGUI coinsLabel, levelLabel, emptyLabel, notesEmpty, moreLabel;
        Image xpFill;
        Button satchelTab, notesTab;
        Coroutine fade;
        int openedFrame = -1;
        bool busyLastFrame;

        void Awake()
        {
            Instance = this;
            Build();
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        void Start()
        {
            cursorLock = FindAnyObjectByType<CursorLock>();
            cameraMode = FindAnyObjectByType<CameraModeController>();
            interactor = FindAnyObjectByType<PlayerInteractor>();
            paintMode = FindAnyObjectByType<PaintModeController>();
            inventory = FindAnyObjectByType<PlayerInventory>();
            pigments = FindAnyObjectByType<PigmentStock>();
            wallet = FindAnyObjectByType<Wallet>();
            level = FindAnyObjectByType<ArtistLevel>();
        }

        void Update()
        {
            if (cursorLock == null || interactor == null) return;
            bool toggle = TogglePressed();
            if (IsOpen)
            {
                bool close = toggle || (Keyboard.current != null && Keyboard.current.escapeKey.wasPressedThisFrame)
                             || (Gamepad.current != null && Gamepad.current.buttonEast.wasPressedThisFrame);
                if (close && Time.frameCount != openedFrame) Close();
                return;
            }
            bool busy = cursorLock.PointerMode || (paintMode != null && paintMode.IsPainting)
                        || (DialogueBox.Instance != null && DialogueBox.Instance.IsOpen)
                        || SceneLoader.IsLoading || ScreenTransition.IsCovered;
            if (!busy && !busyLastFrame && toggle) Open();
            busyLastFrame = busy;
        }

        static bool TogglePressed() =>
            (Keyboard.current != null && (Keyboard.current.iKey.wasPressedThisFrame || Keyboard.current.tabKey.wasPressedThisFrame))
            || (Gamepad.current != null && Gamepad.current.buttonNorth.wasPressedThisFrame);

        // ---------- Abrir / cerrar ----------

        void Open()
        {
            PauseScreen.EnsureEventSystem();
            IsOpen = true;
            openedFrame = Time.frameCount;
            interactor.enabled = false;
            cursorLock.PointerMode = true;
            if (cameraMode != null) cameraMode.SetLookInputEnabled(false);
            group.gameObject.SetActive(true);
            ShowTab(true);
            Refresh(); // con el canvas ya activo: TMP no aplica contornos en jerarquías apagadas
            group.blocksRaycasts = true;
            StartFade(1f);
            UIEvents.Play(UISound.PageTurn);
        }

        void Close()
        {
            if (!IsOpen) return;
            IsOpen = false;
            ClosedFrame = Time.frameCount;
            interactor.enabled = true;
            cursorLock.PointerMode = false;
            if (cameraMode != null) cameraMode.SetLookInputEnabled(true);
            group.blocksRaycasts = false;
            StartFade(0f);
            UIEvents.Play(UISound.CloseMenu);
        }

        void StartFade(float target)
        {
            if (fade != null) StopCoroutine(fade);
            fade = StartCoroutine(FadeRoutine(target));
        }

        IEnumerator FadeRoutine(float target)
        {
            float seconds = GameSettings.ReducedMotion ? 0.06f : FadeSeconds;
            while (!Mathf.Approximately(group.alpha, target))
            {
                group.alpha = Mathf.MoveTowards(group.alpha, target, Time.unscaledDeltaTime / seconds);
                yield return null;
            }
            if (target <= 0f) group.gameObject.SetActive(false);
            fade = null;
        }

        void ShowTab(bool satchel)
        {
            satchelPage.SetActive(satchel);
            notesPage.SetActive(!satchel);
            Dim(satchelTab, satchel);
            Dim(notesTab, !satchel);
        }

        static void Dim(Button b, bool active)
        {
            if (b.targetGraphic != null) b.targetGraphic.canvasRenderer.SetAlpha(active ? 1f : 0.55f);
        }

        // ---------- Contenido ----------

        void Refresh()
        {
            // TMP no aplica contornos dentro de jerarquías apagadas: se activan las dos páginas mientras se rellenan.
            bool satchelWas = satchelPage.activeSelf, notesWas = notesPage.activeSelf;
            satchelPage.SetActive(true);
            notesPage.SetActive(true);
            Fill();
            satchelPage.SetActive(satchelWas);
            notesPage.SetActive(notesWas);
        }

        void Fill()
        {
            Clear(itemList);
            Clear(pigmentList);
            Clear(notesList);
            var t = UITheme.Current;

            int count = inventory != null ? inventory.Items.Count : 0;
            emptyLabel.gameObject.SetActive(count == 0);
            for (int i = 0; i < Mathf.Min(count, MaxRows); i++) ItemRow(inventory.Items[i], i);
            moreLabel.gameObject.SetActive(count > MaxRows);
            moreLabel.text = $"+{count - MaxRows} more";

            coinsLabel.text = wallet != null ? $"Coins   {wallet.Coins}" : "Coins   0";
            if (level != null)
            {
                levelLabel.text = level.IsMaxLevel ? $"Artist level {level.Level}  (max)" : $"Artist level {level.Level}   {level.Xp} / {level.NextLevelXp} xp";
                SetXpFill(level.IsMaxLevel ? 1f : Mathf.Clamp01((float)level.Xp / Mathf.Max(1, level.NextLevelXp)));
            }
            else { levelLabel.text = "Artist level 1"; SetXpFill(0f); }

            int p = 0;
            if (pigments != null)
                foreach (var pair in pigments.All)
                {
                    var chip = UIFactory.Rect("Pigment", pigmentList);
                    UIFactory.Place(chip, new Vector2(0, 1), new Vector2(0, 1), new Vector2((p % 2) * 200f, -(p / 2) * 52f), new Vector2(190, 46));
                    var sw = UIFactory.Rect("Swatch", chip);
                    UIFactory.Place(sw, new Vector2(0, .5f), new Vector2(0, .5f), Vector2.zero, new Vector2(34, 34));
                    var img = sw.gameObject.AddComponent<Image>();
                    img.sprite = UIFactory.DotSprite(); img.color = pair.Key.Color; img.raycastTarget = false;
                    var l = UIFactory.Label("Amount", chip, pair.Value.ToString(), UIFactory.TextStyle.Body, TextAlignmentOptions.Left);
                    UIFactory.ContrastOnPaint(l, 0.3f);
                    UIFactory.Stretch(l.rectTransform);
                    l.rectTransform.offsetMin = new Vector2(46, 0);
                    p++;
                }

            notesEmpty.gameObject.SetActive(notes.Count == 0);
            for (int i = 0; i < Mathf.Min(notes.Count, MaxNotes); i++)
            {
                var n = notes[notes.Count - 1 - i]; // la más reciente arriba
                var l = UIFactory.Label("Note", notesList, $"<color=#E8C25A>{n.Title}</color>\n{n.Text}", UIFactory.TextStyle.Body, TextAlignmentOptions.TopLeft);
                UIFactory.ContrastOnPaint(l, 0.3f);
                UIFactory.Place(l.rectTransform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, -i * 110f), new Vector2(1280, 104));
            }
        }

        void SetXpFill(float amount) => xpFill.rectTransform.anchorMax = new Vector2(amount, 1f); // sin sprite, "Filled" no recorta

        void ItemRow(InventoryItem item, int index)
        {
            var row = UIFactory.Rect("Item", itemList);
            UIFactory.Place(row, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, -index * RowHeight), new Vector2(800, RowHeight - 6));
            if (item.Icon != null)
            {
                var icon = UIFactory.Rect("Icon", row);
                UIFactory.Place(icon, new Vector2(0, .5f), new Vector2(0, .5f), Vector2.zero, new Vector2(54, 54));
                var raw = icon.gameObject.AddComponent<RawImage>();
                raw.texture = item.Icon; raw.raycastTarget = false;
            }
            var name = UIFactory.Label("Name", row, item.DisplayName, UIFactory.TextStyle.Body, TextAlignmentOptions.Left);
            UIFactory.ContrastOnPaint(name, 0.3f);
            UIFactory.Place(name.rectTransform, new Vector2(0, .5f), new Vector2(0, .5f), new Vector2(70, 0), new Vector2(400, 56));
            string detail = item.Detail;
            if (item.Quantity > 1 && string.IsNullOrEmpty(detail)) detail = $"x{item.Quantity}"; // el detalle de algunos objetos ya trae la cantidad
            var d = UIFactory.Label("Detail", row, detail, UIFactory.TextStyle.Small, TextAlignmentOptions.Right);
            d.color = UITheme.A(UITheme.Current.cream, .85f);
            UIFactory.ContrastOnPaint(d, 0.3f);
            UIFactory.Place(d.rectTransform, new Vector2(1, .5f), new Vector2(1, .5f), Vector2.zero, new Vector2(320, 56));
        }

        static void Clear(Transform parent)
        {
            for (int i = parent.childCount - 1; i >= 0; i--) Destroy(parent.GetChild(i).gameObject);
        }

        // ---------- Construcción ----------

        void Build()
        {
            var t = UITheme.Current;
            var canvas = UIFactory.Canvas("JournalCanvas", 400);
            canvas.transform.SetParent(transform, false);
            group = canvas.gameObject.AddComponent<CanvasGroup>();
            group.alpha = 0f;

            var dim = UIFactory.Rect("Dim", canvas.transform);
            UIFactory.Stretch(dim);
            var dimImg = dim.gameObject.AddComponent<Image>();
            dimImg.color = t.Dim(.55f);

            var panel = UIFactory.Panel("Journal", canvas.transform, PanelSize);
            UIFactory.Place(panel.rectTransform, new Vector2(.5f, .5f), new Vector2(.5f, .5f), Vector2.zero, PanelSize);
            var shade = UIFactory.Rect("Shade", panel.transform);
            UIFactory.Stretch(shade);
            shade.offsetMin = new Vector2(50, 50); shade.offsetMax = new Vector2(-50, -50);
            var shadeImg = shade.gameObject.AddComponent<Image>();
            shadeImg.color = t.Shade(.6f);
            shadeImg.raycastTarget = false;

            var title = UIFactory.Label("Title", panel.transform, "Journal", UIFactory.TextStyle.Heading);
            UIFactory.ContrastOnPaint(title, 0.3f);
            UIFactory.Place(title.rectTransform, new Vector2(.5f, 1), new Vector2(.5f, 1), new Vector2(0, -60), new Vector2(700, 70));

            satchelTab = Tab(panel.transform, "Satchel", 0, () => ShowTab(true));
            notesTab = Tab(panel.transform, "Notes", 1, () => ShowTab(false));

            satchelPage = Page(panel.transform, "SatchelPage");
            notesPage = Page(panel.transform, "NotesPage");

            // Satchel: objetos a la izquierda, resumen a la derecha
            Header(satchelPage.transform, "ITEMS", 110, 0);
            itemList = Area(satchelPage.transform, "Items", new Vector2(110, -230), new Vector2(820, MaxRows * RowHeight));
            emptyLabel = UIFactory.Label("Empty", satchelPage.transform, "Your satchel is empty.", UIFactory.TextStyle.Body, TextAlignmentOptions.Left);
            UIFactory.ContrastOnPaint(emptyLabel, 0.3f);
            UIFactory.Place(emptyLabel.rectTransform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(110, -230), new Vector2(600, 50));
            moreLabel = UIFactory.Label("More", satchelPage.transform, "", UIFactory.TextStyle.Small, TextAlignmentOptions.Left);
            UIFactory.ContrastOnPaint(moreLabel, 0.3f);
            UIFactory.Place(moreLabel.rectTransform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(110, -230 - MaxRows * RowHeight - 6), new Vector2(400, 40));

            Header(satchelPage.transform, "ARTIST", 1000, 0);
            coinsLabel = UIFactory.Label("Coins", satchelPage.transform, "", UIFactory.TextStyle.Body, TextAlignmentOptions.Left);
            UIFactory.ContrastOnPaint(coinsLabel, 0.3f);
            UIFactory.Place(coinsLabel.rectTransform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(1000, -230), new Vector2(400, 50));
            levelLabel = UIFactory.Label("Level", satchelPage.transform, "", UIFactory.TextStyle.Body, TextAlignmentOptions.Left);
            UIFactory.ContrastOnPaint(levelLabel, 0.3f);
            UIFactory.Place(levelLabel.rectTransform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(1000, -285), new Vector2(400, 50));
            var barBack = UIFactory.Rect("XpBack", satchelPage.transform);
            UIFactory.Place(barBack, new Vector2(0, 1), new Vector2(0, 1), new Vector2(1000, -345), new Vector2(380, 16));
            var bb = barBack.gameObject.AddComponent<Image>();
            bb.color = UITheme.A(t.ink, .8f); bb.raycastTarget = false;
            var fillRect = UIFactory.Rect("XpFill", barBack);
            UIFactory.Stretch(fillRect);
            xpFill = fillRect.gameObject.AddComponent<Image>();
            xpFill.color = t.warmYellow; xpFill.raycastTarget = false;

            Header(satchelPage.transform, "PIGMENTS", 1000, -170);
            pigmentList = Area(satchelPage.transform, "Pigments", new Vector2(1000, -450), new Vector2(400, 300));

            // Notes
            Header(notesPage.transform, "NOTES", 110, 0);
            notesList = Area(notesPage.transform, "NotesList", new Vector2(110, -250), new Vector2(1280, MaxNotes * 110f));
            notesEmpty = UIFactory.Label("Empty", notesPage.transform, "No notes yet.", UIFactory.TextStyle.Body, TextAlignmentOptions.Left);
            UIFactory.ContrastOnPaint(notesEmpty, 0.3f);
            UIFactory.Place(notesEmpty.rectTransform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(110, -230), new Vector2(600, 50));

            var close = UIFactory.Button("CloseButton", panel.transform, "Close", new Vector2(280, 64));
            UIFactory.Place((RectTransform)close.transform, new Vector2(.5f, 0), new Vector2(.5f, 0), new Vector2(0, 56), new Vector2(280, 64));
            close.onClick.AddListener(Close);

            ShowTab(true);
            canvas.gameObject.SetActive(false);
            group.gameObject.SetActive(false);
        }

        static Button Tab(Transform parent, string label, int index, UnityEngine.Events.UnityAction onClick)
        {
            var b = UIFactory.Button(label + "Tab", parent, label, new Vector2(220, 56));
            UIFactory.Place((RectTransform)b.transform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(110 + index * 235, -130), new Vector2(220, 56));
            b.onClick.AddListener(onClick);
            return b;
        }

        static GameObject Page(Transform parent, string name)
        {
            var r = UIFactory.Rect(name, parent);
            UIFactory.Stretch(r);
            return r.gameObject;
        }

        static RectTransform Area(Transform parent, string name, Vector2 pos, Vector2 size)
        {
            var r = UIFactory.Rect(name, parent);
            UIFactory.Place(r, new Vector2(0, 1), new Vector2(0, 1), pos, size);
            return r;
        }

        static void Header(Transform parent, string text, float x, float yOffset)
        {
            var t = UITheme.Current;
            var l = UIFactory.Label(text + "Header", parent, text, UIFactory.TextStyle.Small, TextAlignmentOptions.Left);
            l.characterSpacing = 8f;
            l.color = UITheme.A(t.warmYellow, .9f);
            UIFactory.ContrastOnPaint(l, 0.3f);
            UIFactory.Place(l.rectTransform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(x, -(yOffset == 0 ? 205 : 205 - yOffset)), new Vector2(500, 30));
        }
    }
}
