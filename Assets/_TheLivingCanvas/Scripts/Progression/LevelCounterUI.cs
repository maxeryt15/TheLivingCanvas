using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Progression
{
    /// <summary>Nivel de artista bajo el contador de monedas: texto "Lv 2  ·  80/150 XP" y barra de avance.</summary>
    public class LevelCounterUI : MonoBehaviour
    {
        [SerializeField] ArtistLevel level;
        [SerializeField] Text label;
        [SerializeField] Image fill;

        void OnEnable()
        {
            level.Changed += Refresh;
            Refresh();
        }

        void OnDisable() => level.Changed -= Refresh;

        void Refresh()
        {
            label.text = level.IsMaxLevel
                ? $"Lv {level.Level} (max)"
                : $"Lv {level.Level}  ·  {level.Xp}/{level.NextLevelXp} XP";
            fill.fillAmount = level.Progress;
        }
    }
}
