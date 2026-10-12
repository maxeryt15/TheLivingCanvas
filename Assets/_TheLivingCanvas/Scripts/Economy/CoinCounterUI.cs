using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Economy
{
    /// <summary>Contador de monedas arriba a la derecha, con un "+30" / "-5" breve al cambiar.</summary>
    public class CoinCounterUI : MonoBehaviour
    {
        [SerializeField] Wallet wallet;
        [SerializeField] Text label;
        [SerializeField] Text deltaLabel;
        [SerializeField] float deltaSeconds = 2f;
        [SerializeField] Color gainColor = new(0.55f, 0.85f, 0.4f);
        [SerializeField] Color spendColor = new(0.95f, 0.55f, 0.45f);

        const float PunchSeconds = 0.25f;
        const float PunchScale = 1.25f;

        float deltaHideTime;
        float punchStartTime = float.NegativeInfinity;

        void OnEnable()
        {
            wallet.Changed += OnChanged;
            label.text = Format(wallet.Coins);
            deltaLabel.gameObject.SetActive(false);
        }

        void OnDisable() => wallet.Changed -= OnChanged;

        void Update()
        {
            if (deltaLabel.gameObject.activeSelf && Time.unscaledTime >= deltaHideTime)
                deltaLabel.gameObject.SetActive(false);
            float punch = (Time.unscaledTime - punchStartTime) / PunchSeconds;
            // Sube a 1.25 en la primera mitad y vuelve a 1 en la segunda.
            label.rectTransform.localScale = Vector3.one * (punch < 1f ? Mathf.Lerp(1f, PunchScale, 1f - Mathf.Abs(2f * punch - 1f)) : 1f);
        }

        void OnChanged(int total, int delta)
        {
            label.text = Format(total);
            if (delta == 0) return; // carga de partida: sin "+0"
            deltaLabel.text = delta > 0 ? $"+{delta}" : delta.ToString();
            deltaLabel.color = delta > 0 ? gainColor : spendColor;
            deltaLabel.gameObject.SetActive(true);
            deltaHideTime = Time.unscaledTime + deltaSeconds;
            if (delta > 0) punchStartTime = Time.unscaledTime;
        }

        static string Format(int coins) => $"{coins} coins";
    }
}
