using System;
using System.Collections.Generic;
using TheLivingCanvas.Data;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Mientras se pinta: proyecta el puntero sobre el lienzo activo, dibuja un aro del tamaño
    /// del pincel y pinta con el botón izquierdo / punta del lápiz. Guarda el estado de las
    /// herramientas (pigmento, tamaño, borrador).
    /// </summary>
    public class PaintBrushController : MonoBehaviour
    {
        [SerializeField] PaintModeController paintMode;
        [SerializeField] InputActionReference pointAction;
        [SerializeField] InputActionReference strokeAction;
        [Tooltip("Rueda del ratón y teclas [ ] para cambiar el tamaño.")]
        [SerializeField] InputActionReference brushSizeAction;
        [SerializeField] InputActionReference undoAction;
        [SerializeField] InputActionReference redoAction;
        [Tooltip("Imagen de UI (en un Canvas Screen Space - Overlay) que marca el tamaño del pincel.")]
        [SerializeField] Image cursorRing;

        [SerializeField] List<PigmentDefinition> palette = new();
        [Tooltip("Pinceles que tiene el jugador; el primero es el seleccionado al empezar.")]
        [SerializeField] List<BrushDefinition> brushes = new();
        [Tooltip("Radio del pincel en píxeles de la pintura.")]
        [SerializeField] float brushRadius = 10f;
        [SerializeField] float minBrushRadius = 3f;
        [SerializeField] float maxBrushRadius = 40f;
        [Tooltip("Opacidad de cada trazo del pincel Glaze (veladura).")]
        [SerializeField, Range(0.1f, 0.9f)] float glazeOpacity = 0.5f;
        [Tooltip("Factor por paso de rueda / tecla.")]
        [SerializeField] float sizeStepFactor = 1.15f;

        PaintSurface strokeSurface;
        Texture2D ringTexture;
        Canvas uiCanvas;
        CanvasInteractable guidedCanvas;

        /// <summary>Se dispara cuando cambia el pigmento, el tamaño o el borrador (para refrescar la UI).</summary>
        public event Action ToolsChanged;
        /// <summary>Se dispara con cada pigmento nuevo en la paleta (ej. comprado en la tienda).</summary>
        public event Action<PigmentDefinition> PigmentAdded;

        public IReadOnlyList<PigmentDefinition> Palette => palette;
        public IReadOnlyList<BrushDefinition> Brushes => brushes;
        public BrushDefinition SelectedBrush { get; private set; }
        /// <summary>Se dispara con cada pincel nuevo (ej. comprado en la tienda).</summary>
        public event Action<BrushDefinition> BrushAdded;
        public PigmentDefinition SelectedPigment { get; private set; }
        public bool EraserActive { get; private set; }
        /// <summary>Contorno tenue de la plantilla.</summary>
        public bool ShowGuide { get; private set; } = true;
        /// <summary>Pista del color sugerido dentro de cada zona.</summary>
        public bool ShowColorHints { get; private set; }
        public float BrushRadius => brushRadius;
        public float MinBrushRadius => minBrushRadius;
        /// <summary>Crece con la resolución del lienzo activo para conservar el mismo tamaño físico máximo.</summary>
        public float MaxBrushRadius =>
            ActiveSurface == null ? maxBrushRadius : maxBrushRadius * ActiveSurface.Width / PaintSurface.ReferenceWidth;

        PaintSurface ActiveSurface => paintMode.IsPainting ? paintMode.ActiveCanvas.Surface : null;
        public bool CanUndo => ActiveSurface != null && ActiveSurface.CanUndo;
        public bool CanRedo => ActiveSurface != null && ActiveSurface.CanRedo;

        void Awake()
        {
            uiCanvas = cursorRing.canvas;
            cursorRing.color = Color.white; // los colores van en la textura
            cursorRing.gameObject.SetActive(false);
            if (palette.Count > 0)
                SelectedPigment = palette[0];
            if (brushes.Count > 0)
                SelectedBrush = brushes[0];
        }

        void OnDestroy() => DestroyRing();

        void OnEnable()
        {
            pointAction.action.Enable();
            strokeAction.action.Enable();
            brushSizeAction.action.Enable();
            brushSizeAction.action.performed += OnBrushSizeInput;
            undoAction.action.Enable();
            undoAction.action.performed += OnUndoInput;
            redoAction.action.Enable();
            redoAction.action.performed += OnRedoInput;
        }

        void OnDisable()
        {
            brushSizeAction.action.performed -= OnBrushSizeInput;
            undoAction.action.performed -= OnUndoInput;
            redoAction.action.performed -= OnRedoInput;
        }

        public void Undo()
        {
            strokeSurface = null; // un trazo en curso no debe seguir sobre el estado restaurado
            ActiveSurface?.Undo();
        }

        public void Redo()
        {
            strokeSurface = null;
            ActiveSurface?.Redo();
        }

        public void ClearCanvas()
        {
            strokeSurface = null;
            ActiveSurface?.Clear();
        }

        void OnUndoInput(InputAction.CallbackContext _) => Undo();

        void OnRedoInput(InputAction.CallbackContext _) => Redo();

        public bool HasPigment(PigmentDefinition pigment) => palette.Contains(pigment);

        /// <summary>Añade un pigmento a la paleta (false si ya estaba).</summary>
        public bool AddPigment(PigmentDefinition pigment)
        {
            if (pigment == null || palette.Contains(pigment)) return false;
            palette.Add(pigment);
            PigmentAdded?.Invoke(pigment);
            return true;
        }

        public bool HasBrush(BrushDefinition brush) => brushes.Contains(brush);

        /// <summary>Añade un pincel (false si ya lo tenía).</summary>
        public bool AddBrush(BrushDefinition brush)
        {
            if (brush == null || brushes.Contains(brush)) return false;
            brushes.Add(brush);
            BrushAdded?.Invoke(brush);
            return true;
        }

        /// <summary>Cambia de pincel; el borrador sigue como estaba (con Fill, borra la zona entera).</summary>
        public void SelectBrush(BrushDefinition brush)
        {
            SelectedBrush = brush;
            ToolsChanged?.Invoke();
        }

        public void SelectPigment(PigmentDefinition pigment)
        {
            SelectedPigment = pigment;
            EraserActive = false;
            ToolsChanged?.Invoke();
        }

        public void SetEraser(bool active)
        {
            EraserActive = active;
            ToolsChanged?.Invoke();
        }

        public void SetShowGuide(bool show)
        {
            ShowGuide = show;
            ApplyGuide();
            ToolsChanged?.Invoke();
        }

        public void SetShowColorHints(bool show)
        {
            ShowColorHints = show;
            ApplyGuide();
            ToolsChanged?.Invoke();
        }

        void ApplyGuide()
        {
            if (guidedCanvas != null)
                guidedCanvas.Guide.Show(ShowGuide, ShowColorHints);
        }

        public void SetBrushRadius(float radius)
        {
            float clamped = Mathf.Clamp(radius, minBrushRadius, MaxBrushRadius);
            if (Mathf.Approximately(clamped, brushRadius)) return;
            brushRadius = clamped;
            ToolsChanged?.Invoke();
        }

        void OnBrushSizeInput(InputAction.CallbackContext context)
        {
            if (!paintMode.IsPainting) return;
            float value = context.ReadValue<float>();
            if (value == 0f) return; // soltar la tecla
            SetBrushRadius(value > 0f ? brushRadius * sizeStepFactor : brushRadius / sizeStepFactor);
        }

        void Update()
        {
            // Al empezar cada sesión de pintura, aplicar al lienzo las opciones de guía actuales.
            if (paintMode.ActiveCanvas != guidedCanvas)
            {
                guidedCanvas = paintMode.ActiveCanvas;
                ApplyGuide();
            }

            var surface = paintMode.IsPainting ? paintMode.ActiveCanvas.Surface : null;
            if (surface == null || Camera.main == null)
            {
                strokeSurface = null;
                cursorRing.gameObject.SetActive(false);
                return;
            }

            // Sobre la paleta (UI) no se pinta.
            bool overUi = EventSystem.current != null && EventSystem.current.IsPointerOverGameObject();
            Ray ray = Camera.main.ScreenPointToRay(pointAction.action.ReadValue<Vector2>());
            bool overCanvas = surface.Raycast(ray, out Vector2 uv, out RaycastHit hit) && !overUi;
            UpdateCursor(overCanvas, hit, surface);

            if (overCanvas && strokeAction.action.IsPressed())
            {
                bool fill = SelectedBrush != null && SelectedBrush.Kind == BrushKind.Fill;
                if (strokeSurface != surface)
                {
                    Color color = EraserActive || SelectedPigment == null ? surface.BaseColor : SelectedPigment.Color;
                    if (fill)
                    {
                        var template = paintMode.ActiveCanvas.Crop.Template;
                        surface.FillZone(uv, PaintEvaluator.ZoneMap(template, surface.Width, surface.Height), color);
                    }
                    else
                    {
                        bool glaze = SelectedBrush != null && SelectedBrush.Kind == BrushKind.Glaze;
                        surface.BeginStroke(uv, brushRadius, color, glaze ? glazeOpacity : 1f);
                    }
                    strokeSurface = surface;
                }
                else if (!fill)
                {
                    surface.ContinueStroke(uv); // Fill actúa una vez por clic: mantener pulsado no rellena más
                }
            }
            else
            {
                // Salir del lienzo corta el trazo; al volver empieza uno nuevo.
                strokeSurface = null;
            }
        }

        void UpdateCursor(bool overCanvas, RaycastHit hit, PaintSurface surface)
        {
            cursorRing.gameObject.SetActive(overCanvas);
            Cursor.visible = !overCanvas; // el aro sustituye al cursor del sistema sobre el lienzo
            if (!overCanvas) return;

            // Proyecta el radio del pincel (en el plano del lienzo) a píxeles de pantalla.
            var cam = Camera.main;
            float worldRadius = brushRadius * surface.PixelWorldSize;
            Vector3 center = cam.WorldToScreenPoint(hit.point);
            Vector3 edge = cam.WorldToScreenPoint(hit.point + surface.transform.right * worldRadius);
            float screenRadius = Vector2.Distance(center, edge);

            // La textura se genera al tamaño exacto en pantalla para que el grosor del aro sea fijo en píxeles.
            int size = Mathf.Max(8, Mathf.CeilToInt(screenRadius * 2f) + 4);
            if (ringTexture == null || ringTexture.width != size)
                RebuildRing(size);

            var rect = cursorRing.rectTransform;
            rect.position = new Vector3(center.x, center.y, 0f); // Canvas Overlay: posición en píxeles de pantalla
            rect.sizeDelta = Vector2.one * (size / uiCanvas.scaleFactor);
        }

        /// <summary>Aro oscuro de ~1.5 px con un borde interior claro, para verse sobre lienzo y pintura.</summary>
        void RebuildRing(int size)
        {
            DestroyRing();
            ringTexture = new Texture2D(size, size, TextureFormat.RGBA32, false)
            {
                name = "BrushRing",
                wrapMode = TextureWrapMode.Clamp
            };

            var dark = new Color(0.18f, 0.12f, 0.08f);
            var light = new Color(1f, 0.97f, 0.9f);
            float half = size * 0.5f;
            float outer = half - 2f;          // centro de la línea oscura
            float inner = outer - 1.75f;      // centro de la línea clara
            var pixels = new Color[size * size];
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float d = new Vector2(x + 0.5f - half, y + 0.5f - half).magnitude;
                    float darkA = Mathf.Clamp01(1.25f - Mathf.Abs(d - outer));
                    float lightA = Mathf.Clamp01(0.9f - Mathf.Abs(d - inner)) * 0.8f;
                    var c = darkA >= lightA ? dark : light;
                    c.a = Mathf.Max(darkA, lightA);
                    pixels[y * size + x] = c;
                }
            }
            ringTexture.SetPixels(pixels);
            ringTexture.Apply(false);
            cursorRing.sprite = Sprite.Create(ringTexture, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f));
        }

        void DestroyRing()
        {
            if (cursorRing != null && cursorRing.sprite != null) Destroy(cursorRing.sprite);
            if (ringTexture != null) Destroy(ringTexture);
        }
    }
}
