using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Seasons
{
    /// <summary>Estación actual y tiempo restante en el HUD: "Spring  ·  7:42".</summary>
    public class SeasonCounterUI : MonoBehaviour
    {
        [SerializeField] SeasonClock clock;
        [SerializeField] Text label;

        void Update()
        {
            int total = Mathf.CeilToInt(clock.SecondsLeft);
            label.text = $"{clock.Current}  ·  {total / 60}:{total % 60:00}";
        }
    }
}
