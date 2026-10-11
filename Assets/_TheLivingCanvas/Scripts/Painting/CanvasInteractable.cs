using System.Collections.Generic;
using System.Linq;
using TheLivingCanvas.Data;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using UnityEngine;

namespace TheLivingCanvas.Painting
{
    /// <summary>
    /// Un caballete. Vacío: interactuar elige el tipo de lienzo (si hay más de uno) y qué cultivo pintar
    /// (si se sabe más de uno), pone un lienzo en blanco del inventario y entra en el modo pintura.
    /// En blanco o a medias: interactuar sigue pintando.
    /// Terminado: interactuar recoge la pintura al inventario y el caballete queda vacío.
    /// </summary>
    public class CanvasInteractable : MonoBehaviour, IInteractable
    {
        [Tooltip("Punto desde el que la cámara mira el lienzo de frente al pintar.")]
        [SerializeField] Transform viewPoint;
        [SerializeField] PaintSurface surface;
        [SerializeField] CanvasGuide guide;

        PaintModeController paintMode;
        CropPickerUI picker;
        PlayerInventory inventory;
        MeshRenderer canvasRenderer;
        PaintingResult finishedResult;
        bool hasCanvas;

        public Transform ViewPoint => viewPoint;
        public PaintSurface Surface => surface;
        public CanvasGuide Guide => guide;
        /// <summary>Cultivo del lienzo puesto (null con el caballete vacío).</summary>
        public CropDefinition Crop { get; private set; }
        /// <summary>Tipo del lienzo puesto (null con el caballete vacío).</summary>
        public CanvasType CanvasType { get; private set; }
        /// <summary>Resolución de los lienzos que se pongan a partir de ahora (la mejora de tienda la sube; el lienzo ya puesto no cambia).</summary>
        public Vector2Int CanvasResolution { get; set; } = new(PaintSurface.ReferenceWidth, PaintSurface.ReferenceHeight);
        public bool IsFinished => finishedResult != null;
        public string Prompt =>
            IsFinished ? "Take painting"
            : hasCanvas ? $"Paint {Crop.DisplayName.ToLowerInvariant()}"
            : inventory != null && inventory.Items.OfType<BlankCanvasItem>().Any() ? "Paint (uses 1 blank canvas)"
            : "No blank canvas - buy one at the shop";
        public bool CanInteract => true;

        void Awake()
        {
            paintMode = FindAnyObjectByType<PaintModeController>();
            picker = FindAnyObjectByType<CropPickerUI>();
            inventory = FindAnyObjectByType<PlayerInventory>();
            canvasRenderer = surface.GetComponent<MeshRenderer>();
        }

        void Start() => SetHasCanvas(false);

        public void Interact(PlayerInteractor interactor)
        {
            if (IsFinished) TakePainting(interactor);
            else if (hasCanvas) paintMode.Enter(this);
            else
            {
                // Primero el tipo de lienzo y luego el cultivo; cada paso se salta si solo hay una opción.
                var owned = OwnedCanvasTypes(interactor.GetComponent<PlayerInventory>());
                if (owned.Count == 1) ChooseCrop(interactor, owned[0]);
                else if (owned.Count > 1) picker.Open(this, owned);
            }
        }

        /// <summary>Con el tipo de lienzo ya elegido: elige el cultivo (si se sabe más de uno) y empieza a pintar.</summary>
        public void ChooseCrop(PlayerInteractor interactor, CanvasType canvasType)
        {
            var known = interactor.GetComponent<Sketchbook>().KnownCrops;
            if (known.Count == 1) StartPainting(interactor, canvasType, known[0]);
            else if (known.Count > 1) picker.Open(this, canvasType, known);
        }

        /// <summary>Pone un lienzo en blanco de <paramref name="canvasType"/> para <paramref name="crop"/> y entra en el modo pintura.</summary>
        public void StartPainting(PlayerInteractor interactor, CanvasType canvasType, CropDefinition crop)
        {
            if (hasCanvas || !interactor.GetComponent<PlayerInventory>().TryConsume(BlankCanvasItem.KeyFor(canvasType))) return;
            CanvasType = canvasType;
            Crop = crop;
            surface.SetResolution(CanvasResolution.x, CanvasResolution.y); // antes que la guía, que se construye al tamaño de la superficie
            guide.SetTemplate(crop.Template);
            surface.ResetToBlank();
            SetHasCanvas(true);
            // El boceto tenue se ve también desde el mundo, antes de empezar a pintar.
            ShowSketch();
            paintMode.Enter(this);
        }

        /// <summary>La pintura pasó la evaluación: queda lista para recogerla.</summary>
        public void MarkFinished(PaintingResult result)
        {
            finishedResult = result;
            guide.Show(showOutline: false, showHints: false); // sin boceto: se ve la pintura tal cual
        }

        void TakePainting(PlayerInteractor interactor)
        {
            var inventory = interactor.GetComponent<PlayerInventory>();
            inventory.Add(new PaintingItem(Crop, CanvasType, finishedResult, surface.CreateSnapshot()));

            // El caballete queda vacío hasta que se ponga otro lienzo.
            finishedResult = null;
            Crop = null;
            CanvasType = null;
            SetHasCanvas(false);
        }

        /// <summary>Tipos de lienzo en blanco de los que el jugador tiene al menos uno.</summary>
        static List<CanvasType> OwnedCanvasTypes(PlayerInventory inventory) =>
            inventory.Items.OfType<BlankCanvasItem>().Select(item => item.Type).ToList();

        void SetHasCanvas(bool value)
        {
            hasCanvas = value;
            canvasRenderer.enabled = value;
        }

        void ShowSketch() => guide.Show(showOutline: true, showHints: false);
    }
}
