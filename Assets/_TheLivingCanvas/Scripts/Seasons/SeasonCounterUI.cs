using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Seasons
{
    /// <summary>Estación, día y hora en el HUD: "Spring 4  ·  9:40 am" (+ "Festival!" o "Market day" cuando toca).</summary>
    public class SeasonCounterUI : MonoBehaviour
    {
        [SerializeField] SeasonClock clock;
        [SerializeField] Text label;

        void Update()
        {
            var extra = clock.IsFestival ? "  ·  Festival!" : clock.IsMarketDay ? "  ·  Market day" : "";
            label.text = $"{clock.Current} {clock.Day}  ·  {clock.TimeText}{extra}";
        }
    }
}
