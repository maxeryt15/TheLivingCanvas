using System;
using System.Collections.Generic;
using System.Linq;
using TheLivingCanvas.Audio;
using TheLivingCanvas.Data;
using TheLivingCanvas.Save;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace TheLivingCanvas.Painting
{
    /// <summary>Herramientas de pintura que se compran una vez en la tienda.</summary>
    public enum PaintTool
    {
        Eyedropper,
        Symmetry
    }

    /// <summary>
    /// Mientras se pinta: proyecta el puntero sobre el lienzo activo, dibuja un aro del tamaño
    /// del pincel y pinta con el botón izquierdo / punta del lápiz. Guarda el estado de las
    /// herramientas (pigmento, tamaño, borrador).
    /// </summary>
    public class PaintBrushController : MonoBehaviour, ISaveable
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
        [Tooltip("Opacidad de cada trazo de Round y Glaze con el estilo Wash.")]
        [SerializeField, Range(0.1f, 0.9f)] float washOpacity = 0.65f;
        [Tooltip("Factor por paso de rueda / tecla.")]
        [SerializeField] float sizeStepFactor = 1.15f;

        PaintSurface strokeSurface;
        Texture2D ringTexture;
        Canvas uiCanvas;
        CanvasInteractable guidedCanvas;
        bool pickHeld; // el clic que copió el color sigue pulsado: no debe empezar un trazo

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
        /// <summary>Color copiado de la pintura con el cuentagotas; sustituye al del pigmento hasta elegir otro.</summary>
        public Color? PickedColor { get; private set; }
        /// <summary>Cuentagotas armado: el próximo clic sobre pintura copia su color.</summary>
        public bool EyedropperActive { get; private set; }
        public bool SymmetryActive { get; private set; }
        /// <summary>Contorno tenue de la plantilla.</summary>
        public bool ShowGuide { get; private set; } = true;
        /// <summary>Pista del color sugerido dentro de cada zona.</summary>
        public bool ShowColorHints { get; private set; }
        /// <summary>El puntero está sobre el lienzo activo (no sobre la UI): <see cref="HitPoint"/> y <see cref="HitNormal"/> son válidos.</summary>
        public bool HasHit { get; private set; }
        public Vector3 HitPoint { get; private set; }
        public Vector3 HitNormal { get; private set; }
        /// <summary>Hay un trazo en curso.</summary>
        public bool IsStroking => strokeSurface != null;
        public float BrushRadius => brushRadius;
        public float MinBrushRadius => minBrushRadius;
        /// <summary>Crece con la resolución del lienzo activo para conservar el mismo tamaño físico máximo.</summary>
        public float MaxBrushRadius =>
            ActiveSurface == null ? maxBrushRadius : maxBrushRadius * ActiveSurface.Width / PaintSurface.ReferenceWidth;

        /// <summary>Se dispara con cada herramienta nueva (ej. comprada en la tienda).</summary>
        public event Action<PaintTool> ToolAdded;

        readonly HashSet<PaintTool> tools = new();

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

        /// <summary>Termina el trazo en curso (si lo hay): la acuarela sangra al soltar.</summary>
        void EndStroke()
        {
            SfxPlayer.SetBrushing(false);
            if (strokeSurface == null) return;
            strokeSurface.EndStroke();
            strokeSurface = null;
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

        public bool HasTool(PaintTool tool) => tools.Contains(tool);

        /// <summary>Añade una herramienta (false si ya la tenía).</summary>
        public bool AddTool(PaintTool tool)
        {
            if (!tools.Add(tool)) return false;
            ToolAdded?.Invoke(tool);
            return true;
        }

        public void WriteSave(SaveData data)
        {
            data.palette = palette.Select(p => p.Id).ToList();
            data.brushes = brushes.Select(b => b.Id).ToList();
            data.tools = tools.Select(t => t.ToString()).ToList();
        }

        /// <summary>Añade lo que falta (los iniciales se quedan); los eventos Added actualizan la UI de la paleta.</summary>
        public void ReadSave(SaveData data, SaveRegistry registry)
        {
            foreach (var id in data.palette)
                AddPigment(registry.FindPigment(id));
            foreach (var id in data.brushes)
                AddBrush(registry.FindBrush(id));
            foreach (var name in data.tools)
            {
                if (Enum.TryParse(name, out PaintTool tool)) AddTool(tool);
                else Debug.LogWarning($"[Save] Unknown tool '{name}' in save; skipped.");
            }
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
            PickedColor = null;
            EraserActive = false;
            ToolsChanged?.Invoke();
        }

        public void SetEraser(bool active)
        {
            EraserActive = active;
            ToolsChanged?.Invoke();
        }

        public void SetEyedropper(bool active)
        {
            EyedropperActive = active;
            ToolsChanged?.Invoke();
        }

        public void SetSymmetry(bool active)
        {
            SymmetryActive = active;
            ToolsChanged?.Invoke();
        }

        /// <summary>Vuelve al color copiado con el cuentagotas (también quita el borrador).</summary>
        public void SelectPickedColor()
        {
            EraserActive = false;
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
                EndStroke();
                HasHit = false;
                cursorRing.gameObject.SetActive(false);
                return;
            }

            // Sobre la paleta (UI) no se pinta.
            bool overUi = EventSystem.current != null && EventSystem.current.IsPointerOverGameObject();
            Ray ray = Camera.main.ScreenPointToRay(pointAction.action.ReadValue<Vector2>());
            bool overCanvas = surface.Raycast(ray, out Vector2 uv, out RaycastHit hit) && !overUi;
            HasHit = overCanvas;
            HitPoint = hit.point;
            HitNormal = hit.normal;
            UpdateCursor(overCanvas, hit, surface);

            bool pressed = strokeAction.action.IsPressed();
            if (!pressed)
                pickHeld = false;
            if (EyedropperActive && overCanvas && strokeAction.action.WasPressedThisFrame())
                TryPickColor(surface, uv);

            // Con el cuentagotas armado (o recién usado, hasta soltar el botón) no se pinta.
            if (overCanvas && pressed && !EyedropperActive && !pickHeld)
            {
                bool fill = SelectedBrush != null && SelectedBrush.Kind == BrushKind.Fill;
                if (strokeSurface != surface)
                {
                    Color color = StrokeColor(surface);
                    if (fill)
                    {
                        var template = paintMode.ActiveCanvas.Crop.Template;
                        surface.FillZone(uv, PaintEvaluator.ZoneMap(template, surface.Width, surface.Height), color, SymmetryActive);
                    }
                    else
                    {
                        bool glaze = SelectedBrush != null && SelectedBrush.Kind == BrushKind.Glaze;
                        // Wash: Round y Glaze pintan translúcido y sangran al soltar; Swirl los pinta con vetas. El borrador, con ninguno.
                        bool wash = !EraserActive && paintMode.ActiveCanvas.Style != null && paintMode.ActiveCanvas.Style.Kind == StyleKind.Wash;
                        bool swirl = !EraserActive && paintMode.ActiveCanvas.Style != null && paintMode.ActiveCanvas.Style.Kind == StyleKind.Swirl;
                        surface.BeginStroke(uv, brushRadius, color, wash ? washOpacity : glaze ? glazeOpacity : 1f, SymmetryActive, wash, swirl);
                        SfxPlayer.SetBrushing(true);
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
                EndStroke();
            }
        }

        /// <summary>Copia el color bajo el puntero; sobre tela sin pintar no hay nada que copiar y sigue armado.</summary>
        void TryPickColor(PaintSurface surface, Vector2 uv)
        {
            if (!surface.TrySamplePaint(uv, out Color sampled)) return;
            PickedColor = sampled;
            EraserActive = false;
            EyedropperActive = false;
            pickHeld = true;
            ToolsChanged?.Invoke();
        }

        Color StrokeColor(PaintSurface surface)
        {
            if (EraserActive) return surface.BaseColor;
            if (PickedColor.HasValue) return PickedColor.Value;
            return SelectedPigment != null ? SelectedPigment.Color : surface.BaseColor;
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
