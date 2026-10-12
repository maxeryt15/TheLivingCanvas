using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Seasons
{
    /// <summary>Transición de día: pantalla negra con "Spring 4" (y "Year 2" a partir del segundo año) que se desvanece.</summary>
    public class DayFadeUI : MonoBehaviour
    {
        [SerializeField] SeasonClock clock;
        [SerializeField] CanvasGroup group;
        [SerializeField] Text label;
        [Tooltip("Segundos en negro antes de empezar a aclarar.")]
        [SerializeField] float holdSeconds = 0.4f;
        [SerializeField] float fadeSeconds = 1.5f;

        float startTime = float.NegativeInfinity;

        void Awake() => group.alpha = 0f;

        void OnEnable() => clock.DayChanged += OnDayChanged;

        void OnDisable() => clock.DayChanged -= OnDayChanged;

        void OnDayChanged(int day)
        {
            label.text = clock.Year > 1 ? $"{clock.Current} {day}\n<size=28>Year {clock.Year}</size>" : $"{clock.Current} {day}";
            startTime = Time.unscaledTime;
            group.alpha = 1f;
        }

        void Update()
        {
            if (group.alpha <= 0f) return;
            group.alpha = 1f - Mathf.Clamp01((Time.unscaledTime - startTime - holdSeconds) / fadeSeconds);
        }
    }
}
