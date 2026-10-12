using TheLivingCanvas.Seasons;
using UnityEngine;

namespace TheLivingCanvas.Economy
{
    /// <summary>Algo que se vende en la tienda: nombre, descripción, precio y qué recibe el comprador.</summary>
    public abstract class ShopOffer : ScriptableObject
    {
        [SerializeField] string displayName;
        [SerializeField, TextArea] string description;
        [SerializeField] int price = 5;
        [SerializeField] Texture2D icon;
        [Tooltip("Nivel de artista mínimo para comprarla.")]
        [SerializeField] int requiredLevel = 1;
        [Tooltip("Si está marcado, solo se vende durante la estación indicada.")]
        [SerializeField] bool seasonal;
        [SerializeField] Season season;

        public string DisplayName => displayName;
        public string Description => description;
        public int Price => price;
        public int RequiredLevel => requiredLevel;
        public virtual Texture Icon => icon;

        /// <summary>true si en los días de mercado cuesta la mitad (pigmentos y recargas).</summary>
        public virtual bool HalfPriceOnMarketDay => false;

        /// <summary>false si la oferta es de una estación y no es la actual.</summary>
        public bool IsSoldIn(Season current) => !seasonal || current == season;

        /// <summary>false si ya no se puede comprar (ej. una mejora que ya se tiene).</summary>
        public virtual bool IsAvailable(GameObject buyer) => true;

        /// <summary>Entrega la compra al jugador (el pago ya se hizo).</summary>
        public abstract void Deliver(GameObject buyer);

#if UNITY_EDITOR
        public void EditorSetupOffer(string newDisplayName, string newDescription, int newPrice, Texture2D newIcon)
        {
            displayName = newDisplayName;
            description = newDescription;
            price = newPrice;
            icon = newIcon;
        }

        public void EditorSetRequiredLevel(int level) => requiredLevel = level;

        /// <summary>null = se vende todo el año.</summary>
        public void EditorSetSeason(Season? onlyIn)
        {
            seasonal = onlyIn.HasValue;
            if (onlyIn.HasValue) season = onlyIn.Value;
        }
#endif
    }
}
