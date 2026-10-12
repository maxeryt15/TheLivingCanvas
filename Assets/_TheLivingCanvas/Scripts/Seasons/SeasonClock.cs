using System;
using UnityEngine;

namespace TheLivingCanvas.Seasons
{
    /// <summary>Reloj de estaciones: avanza por tiempo de juego (Spring → Summer → Autumn → Winter → Spring...).</summary>
    public class SeasonClock : MonoBehaviour
    {
        [SerializeField] float secondsPerSeason = 480f; // placeholder: 8 min por estación
        [SerializeField] Season startSeason = Season.Spring;

        public Season Current { get; private set; }
        public float SecondsLeft { get; private set; }
        public event Action<Season> SeasonChanged;

        void Awake()
        {
            Current = startSeason;
            SecondsLeft = secondsPerSeason;
        }

        void Update()
        {
            SecondsLeft -= Time.deltaTime;
            if (SecondsLeft <= 0f) NextSeason();
        }

        /// <summary>Salta a la siguiente estación y reinicia el contador.</summary>
        [ContextMenu("Next Season")]
        public void NextSeason()
        {
            Current = (Season)(((int)Current + 1) % 4);
            SecondsLeft = secondsPerSeason;
            SeasonChanged?.Invoke(Current);
        }
    }
}
