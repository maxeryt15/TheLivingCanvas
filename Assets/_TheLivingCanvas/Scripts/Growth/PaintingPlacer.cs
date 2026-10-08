using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace TheLivingCanvas.Growth
{
    /// <summary>
    /// Colocar una pintura del inventario en el suelo: una vista previa sigue al jugador,
    /// Interact (E / A) la pone y Exit (Esc / B) cancela. No se puede poner encima de otros objetos.
    /// </summary>
    public class PaintingPlacer : MonoBehaviour
    {
        [SerializeField] PlayerInventory inventory;
        [SerializeField] PlayerInteractor interactor;
        [SerializeField] PaintingPlot plotPrefab;
        [SerializeField] InputActionReference confirmAction;
        [SerializeField] InputActionReference cancelAction;
        [SerializeField] GameObject hint;
        [SerializeField] Text hintLabel;

        [Tooltip("Distancia delante del jugador a la que se coloca (m).")]
        [SerializeField] float distance = 1.6f;
        [SerializeField] LayerMask groundMask = 1;
        [Tooltip("Diferencia máxima de altura entre el suelo elegido y los pies del jugador (m).")]
        [SerializeField] float maxHeightDifference = 0.3f;
        [Tooltip("Medio tamaño del hueco que necesita la parcela (marco del lienzo + margen).")]
        [SerializeField] Vector3 clearanceHalfExtents = new(0.55f, 0.12f, 0.45f);

        readonly Collider[] overlaps = new Collider[16];
        PaintingItem item;
        PaintingPlot preview;
        Collider groundCollider;
        bool validSpot;
        int beganFrame;

        public bool IsPlacing => item != null;

        void OnEnable()
        {
            confirmAction.action.performed += OnConfirm;
            cancelAction.action.performed += OnCancel;
        }

        void OnDisable()
        {
            confirmAction.action.performed -= OnConfirm;
            cancelAction.action.performed -= OnCancel;
        }

        public void Begin(PaintingItem painting)
        {
            if (IsPlacing) return;
            item = painting;
            beganFrame = Time.frameCount;
            preview = Instantiate(plotPrefab);
            preview.name = "PaintingPlot (preview)";
            preview.Show(painting);
            preview.SetPreview(true);

            interactor.enabled = false; // E coloca en lugar de interactuar
            confirmAction.action.Enable();
            cancelAction.action.Enable();
            hint.SetActive(true);
            UpdatePreview();
        }

        void Update()
        {
            if (IsPlacing) UpdatePreview();
        }

        void UpdatePreview()
        {
            Transform player = interactor.transform;
            Vector3 forward = Vector3.ProjectOnPlane(player.forward, Vector3.up).normalized;
            Vector3 probe = player.position + forward * distance + Vector3.up * 2f;

            // Solo vale suelo plano a la altura de los pies (no encima de mesas, lámparas...).
            validSpot = Physics.Raycast(probe, Vector3.down, out RaycastHit hit, 4f, groundMask, QueryTriggerInteraction.Ignore)
                        && hit.normal.y > 0.9f
                        && Mathf.Abs(hit.point.y - player.position.y) < maxHeightDifference;
            groundCollider = validSpot ? hit.collider : null;

            Vector3 position = validSpot ? hit.point : player.position + forward * distance;
            preview.transform.SetPositionAndRotation(position + Vector3.up * 0.01f, Quaternion.LookRotation(forward));
            validSpot &= IsSpotClear();

            hintLabel.text = validSpot
                ? "Place painting:  [E] place   ·   [Esc] cancel"
                : "Can't place it here  ·  [Esc] cancel";
        }

        bool IsSpotClear()
        {
            Transform t = preview.transform;
            int count = Physics.OverlapBoxNonAlloc(t.position + Vector3.up * (clearanceHalfExtents.y + 0.02f),
                clearanceHalfExtents, overlaps, t.rotation, ~0, QueryTriggerInteraction.Ignore);
            for (int i = 0; i < count; i++)
            {
                var c = overlaps[i];
                if (c == groundCollider || c.transform.IsChildOf(interactor.transform)) continue;
                return false; // muebles, caballete, otras parcelas, límites del estudio
            }
            return true;
        }

        void OnConfirm(InputAction.CallbackContext _)
        {
            if (!IsPlacing || Time.frameCount == beganFrame || !validSpot) return;
            preview.name = "PaintingPlot";
            preview.SetPreview(false);
            inventory.Remove(item);
            End();
        }

        void OnCancel(InputAction.CallbackContext _)
        {
            if (!IsPlacing) return;
            Destroy(preview.gameObject);
            End();
        }

        void End()
        {
            item = null;
            preview = null;
            interactor.enabled = true;
            hint.SetActive(false);
        }
    }
}
