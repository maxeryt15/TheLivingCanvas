using System.Collections.Generic;
using TheLivingCanvas.Core;
using TheLivingCanvas.Progression;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Economy
{
    /// <summary>
    /// Panel placeholder de la tienda: una fila por oferta que se puede comprar ahora (lo ya comprado y las
    /// recargas de colores que aún no se tienen no salen), con su precio y un botón Buy.
    /// Las ofertas de un nivel de artista superior se listan, pero bloqueadas.
    /// </summary>
    public class ShopUI : ModalPanel
    {
        [SerializeField] ShopOffer[] offers;
        [SerializeField] Wallet wallet;
        [SerializeField] ArtistLevel artistLevel;
        [SerializeField] RectTransform rowContainer;
        [Tooltip("Fila desactivada que se clona por oferta (RawImage 'Icon', Text 'Name', Button 'Buy' con Text).")]
        [SerializeField] GameObject rowTemplate;
        [SerializeField] Text messageLabel;

        readonly List<(ShopOffer offer, Button buy)> rows = new();
        GameObject buyer;

        protected override void Awake()
        {
            base.Awake();
            rowTemplate.SetActive(false);
        }

        protected override void OnEnable()
        {
            base.OnEnable();
            wallet.Changed += OnWalletChanged;
            artistLevel.LeveledUp += OnLeveledUp;
        }

        protected override void OnDisable()
        {
            base.OnDisable();
            wallet.Changed -= OnWalletChanged;
            artistLevel.LeveledUp -= OnLeveledUp;
        }

        public void Open(GameObject player)
        {
            if (!TryOpen()) return;
            buyer = player;
            messageLabel.text = string.Empty;
            Rebuild();
        }

        void OnWalletChanged(int total, int delta)
        {
            if (IsOpen) RefreshButtons();
        }

        void OnLeveledUp(int level)
        {
            if (IsOpen) RefreshButtons();
        }

        public void Buy(ShopOffer offer)
        {
            if (!offer.IsAvailable(buyer) || offer.RequiredLevel > artistLevel.Level) return;
            if (!wallet.TrySpend(offer.Price))
            {
                messageLabel.text = $"Not enough coins for {offer.DisplayName.ToLowerInvariant()}.";
                return;
            }
            offer.Deliver(buyer);
            messageLabel.text = $"Bought {offer.DisplayName.ToLowerInvariant()}!";
            Rebuild(); // lo comprado puede desaparecer y aparecer otras ofertas (ej. la recarga de ese color)
        }

        void Rebuild()
        {
            foreach (var (_, buy) in rows)
                Destroy(buy.transform.parent.gameObject);
            rows.Clear();

            foreach (var offer in offers)
            {
                if (!offer.IsAvailable(buyer)) continue;
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
                bool unlocked = offer.RequiredLevel <= artistLevel.Level;
                buy.interactable = unlocked && wallet.CanAfford(offer.Price);
                buy.GetComponentInChildren<Text>().text = unlocked ? $"Buy  {offer.Price}" : $"Level {offer.RequiredLevel}";
            }
        }
    }
}
