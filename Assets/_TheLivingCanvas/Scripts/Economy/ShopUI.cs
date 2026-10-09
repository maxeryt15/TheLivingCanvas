using System.Collections.Generic;
using TheLivingCanvas.Core;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Player;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace TheLivingCanvas.Economy
{
    /// <summary>
    /// Panel placeholder de la tienda: una fila por oferta con su precio y un botón Buy.
    /// Se cierra con el botón Close, Exit (Esc / B) o Interact (E / A).
    /// </summary>
    public class ShopUI : MonoBehaviour
    {
        [SerializeField] ShopOffer[] offers;
        [SerializeField] Wallet wallet;
        [SerializeField] PlayerInteractor interactor;
        [SerializeField] CursorLock cursorLock;
        [SerializeField] CameraModeController cameraMode;
        [SerializeField] InputActionReference exitAction;
        [SerializeField] GameObject panel;
        [SerializeField] RectTransform rowContainer;
        [Tooltip("Fila desactivada que se clona por oferta (RawImage 'Icon', Text 'Name', Button 'Buy' con Text).")]
        [SerializeField] GameObject rowTemplate;
        [SerializeField] Button closeButton;
        [SerializeField] Text messageLabel;

        readonly List<(ShopOffer offer, Button buy)> rows = new();
        GameObject buyer;
        int openedFrame = -1;

        public bool IsOpen => panel.activeSelf;

        void Awake()
        {
            rowTemplate.SetActive(false);
            panel.SetActive(false);
            closeButton.onClick.AddListener(Close);
        }

        void OnEnable()
        {
            exitAction.action.performed += OnCloseRequested;
            interactor.InteractAction.action.performed += OnCloseRequested;
            wallet.Changed += OnWalletChanged;
        }

        void OnDisable()
        {
            exitAction.action.performed -= OnCloseRequested;
            interactor.InteractAction.action.performed -= OnCloseRequested;
            wallet.Changed -= OnWalletChanged;
        }

        public void Open(GameObject player)
        {
            // Otro panel (inventario, modo pintura) ya tiene el cursor.
            if (IsOpen || cursorLock.PointerMode) return;
            buyer = player;
            openedFrame = Time.frameCount;
            panel.SetActive(true);
            messageLabel.text = string.Empty;
            interactor.enabled = false; // E cierra en lugar de interactuar
            cursorLock.PointerMode = true;
            cameraMode.SetLookInputEnabled(false);
            exitAction.action.Enable();
            Rebuild();
        }

        public void Close()
        {
            if (!IsOpen) return;
            panel.SetActive(false);
            exitAction.action.Disable();
            interactor.enabled = true;
            cursorLock.PointerMode = false;
            cameraMode.SetLookInputEnabled(true);
        }

        void OnCloseRequested(InputAction.CallbackContext _)
        {
            // La misma pulsación de E que abre no debe cerrar.
            if (Time.frameCount != openedFrame) Close();
        }

        void OnWalletChanged(int total, int delta)
        {
            if (IsOpen) RefreshButtons();
        }

        public void Buy(ShopOffer offer)
        {
            if (!offer.IsAvailable(buyer)) return;
            if (!wallet.TrySpend(offer.Price))
            {
                messageLabel.text = $"Not enough coins for {offer.DisplayName.ToLowerInvariant()}.";
                return;
            }
            offer.Deliver(buyer);
            messageLabel.text = $"Bought {offer.DisplayName.ToLowerInvariant()}!";
            RefreshButtons();
        }

        void Rebuild()
        {
            foreach (var (_, buy) in rows)
                Destroy(buy.transform.parent.gameObject);
            rows.Clear();

            foreach (var offer in offers)
            {
                var row = Instantiate(rowTemplate, rowContainer);
                row.SetActive(true);
                row.transform.Find("Icon").GetComponent<RawImage>().texture = offer.Icon;
                row.transform.Find("Name").GetComponent<Text>().text = $"{offer.DisplayName}\n<size=18>{offer.Description}</size>";
                var buy = row.transform.Find("Buy").GetComponent<Button>();
                buy.onClick.AddListener(() => Buy(offer));
                rows.Add((offer, buy));
            }
            RefreshButtons();
        }

        void RefreshButtons()
        {
            foreach (var (offer, buy) in rows)
            {
                bool available = offer.IsAvailable(buyer);
                buy.interactable = available && wallet.CanAfford(offer.Price);
                buy.GetComponentInChildren<Text>().text = available ? $"Buy  {offer.Price}" : "Owned";
            }
        }
    }
}
