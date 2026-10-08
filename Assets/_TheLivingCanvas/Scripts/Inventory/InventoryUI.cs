using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace TheLivingCanvas.Inventory
{
    /// <summary>
    /// Panel placeholder del inventario (I / Tab / Y): una casilla por objeto con miniatura, nombre y detalle.
    /// Además avisa brevemente al recoger algo.
    /// </summary>
    public class InventoryUI : MonoBehaviour
    {
        [SerializeField] PlayerInventory inventory;
        [SerializeField] InputActionReference toggleAction;
        [SerializeField] GameObject panel;
        [SerializeField] RectTransform slotContainer;
        [Tooltip("Casilla desactivada que se clona por cada objeto (RawImage 'Icon' + Text 'Name').")]
        [SerializeField] GameObject slotTemplate;
        [SerializeField] GameObject emptyLabel;
        [SerializeField] GameObject toast;
        [SerializeField] Text toastLabel;
        [SerializeField] float toastSeconds = 3f;

        float toastHideTime;

        void Awake()
        {
            slotTemplate.SetActive(false);
            panel.SetActive(false);
            toast.SetActive(false);
        }

        void OnEnable()
        {
            toggleAction.action.Enable();
            toggleAction.action.performed += OnToggle;
            inventory.ItemAdded += OnItemAdded;
        }

        void OnDisable()
        {
            toggleAction.action.performed -= OnToggle;
            inventory.ItemAdded -= OnItemAdded;
        }

        void Update()
        {
            if (toast.activeSelf && Time.unscaledTime >= toastHideTime)
                toast.SetActive(false);
        }

        void OnToggle(InputAction.CallbackContext _)
        {
            panel.SetActive(!panel.activeSelf);
            if (panel.activeSelf) Rebuild();
        }

        void OnItemAdded(InventoryItem item)
        {
            toastLabel.text = $"+1 {item.DisplayName} ({item.Detail})";
            toast.SetActive(true);
            toastHideTime = Time.unscaledTime + toastSeconds;
            if (panel.activeSelf) Rebuild();
        }

        void Rebuild()
        {
            foreach (Transform child in slotContainer)
                if (child.gameObject != slotTemplate)
                    Destroy(child.gameObject);

            emptyLabel.SetActive(inventory.Items.Count == 0);
            foreach (var item in inventory.Items)
            {
                var slot = Instantiate(slotTemplate, slotContainer);
                slot.SetActive(true);
                slot.transform.Find("Icon").GetComponent<RawImage>().texture = item.Icon;
                slot.transform.Find("Name").GetComponent<Text>().text = $"{item.DisplayName}\n{item.Detail}";
            }
        }
    }
}
