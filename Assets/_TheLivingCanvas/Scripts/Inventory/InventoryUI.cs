using TheLivingCanvas.Core;
using TheLivingCanvas.Growth;
using TheLivingCanvas.Painting;
using TheLivingCanvas.Player;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace TheLivingCanvas.Inventory
{
    /// <summary>
    /// Panel placeholder del inventario (I / Tab / Y): una casilla por objeto con miniatura, nombre y detalle.
    /// Con el panel abierto el cursor queda libre; clicar una pintura empieza a colocarla en el suelo.
    /// Además avisa brevemente al recoger algo.
    /// </summary>
    public class InventoryUI : MonoBehaviour
    {
        [SerializeField] PlayerInventory inventory;
        [SerializeField] InputActionReference toggleAction;
        [SerializeField] PaintingPlacer placer;
        [SerializeField] PaintModeController paintMode;
        [SerializeField] CursorLock cursorLock;
        [SerializeField] CameraModeController cameraMode;
        [SerializeField] GameObject panel;
        [SerializeField] RectTransform slotContainer;
        [Tooltip("Casilla desactivada (Button) que se clona por cada objeto (RawImage 'Icon' + Text 'Name').")]
        [SerializeField] Button slotTemplate;
        [SerializeField] GameObject emptyLabel;
        [SerializeField] GameObject toast;
        [SerializeField] Text toastLabel;
        [SerializeField] float toastSeconds = 3f;

        float toastHideTime;

        bool IsOpen => panel.activeSelf;

        void Awake()
        {
            slotTemplate.gameObject.SetActive(false);
            panel.SetActive(false);
            toast.SetActive(false);
        }

        void OnEnable()
        {
            toggleAction.action.Enable();
            toggleAction.action.performed += OnToggle;
            inventory.ItemAdded += OnItemAdded;
            inventory.Changed += OnChanged;
        }

        void OnDisable()
        {
            toggleAction.action.performed -= OnToggle;
            inventory.ItemAdded -= OnItemAdded;
            inventory.Changed -= OnChanged;
        }

        void Update()
        {
            if (toast.activeSelf && Time.unscaledTime >= toastHideTime)
                toast.SetActive(false);
        }

        void OnToggle(InputAction.CallbackContext _)
        {
            if (IsOpen) Close();
            else if (!paintMode.IsPainting && !placer.IsPlacing) Open();
        }

        void Open()
        {
            panel.SetActive(true);
            cursorLock.PointerMode = true;
            cameraMode.SetLookInputEnabled(false);
            Rebuild();
        }

        void Close()
        {
            panel.SetActive(false);
            cursorLock.PointerMode = false;
            cameraMode.SetLookInputEnabled(true);
        }

        void OnItemAdded(InventoryItem item)
        {
            toastLabel.text = $"+1 {item.DisplayName} ({item.Detail})";
            toast.SetActive(true);
            toastHideTime = Time.unscaledTime + toastSeconds;
        }

        void OnChanged()
        {
            if (IsOpen) Rebuild();
        }

        void OnSlotClicked(InventoryItem item)
        {
            if (item is not PaintingItem painting) return;
            Close();
            placer.Begin(painting);
        }

        void Rebuild()
        {
            foreach (Transform child in slotContainer)
                if (child != slotTemplate.transform)
                    Destroy(child.gameObject);

            emptyLabel.SetActive(inventory.Items.Count == 0);
            foreach (var item in inventory.Items)
            {
                var slot = Instantiate(slotTemplate, slotContainer);
                slot.gameObject.SetActive(true);
                slot.transform.Find("Icon").GetComponent<RawImage>().texture = item.Icon;
                slot.transform.Find("Name").GetComponent<Text>().text = $"{item.DisplayName}\n{item.Detail}";
                slot.onClick.AddListener(() => OnSlotClicked(item));
            }
        }
    }
}
