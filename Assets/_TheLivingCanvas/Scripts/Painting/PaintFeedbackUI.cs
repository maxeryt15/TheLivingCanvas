using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Painting
{
    /// <summary>Mensaje temporal abajo al centro (ánimo si falta pintura, enhorabuena si pasa).</summary>
    public class PaintFeedbackUI : MonoBehaviour
    {
        [SerializeField] GameObject panel;
        [SerializeField] Image background;
        [SerializeField] Text label;
        [SerializeField] float visibleSeconds = 5f;
        [SerializeField] Color hintColor = new(0.16f, 0.11f, 0.08f, 0.9f);
        [SerializeField] Color successColor = new(0.22f, 0.36f, 0.16f, 0.92f);

        float hideTime;

        void Awake() => panel.SetActive(false);

        public void Show(string message, bool success)
        {
            label.text = message;
            background.color = success ? successColor : hintColor;
            panel.SetActive(true);
            hideTime = Time.unscaledTime + visibleSeconds;
        }

        void Update()
        {
            if (panel.activeSelf && Time.unscaledTime >= hideTime)
                panel.SetActive(false);
        }
    }
}
