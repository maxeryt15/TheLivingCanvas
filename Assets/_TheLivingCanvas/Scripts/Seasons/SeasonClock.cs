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
        public event Action<bool> FestivalChanged;

        /// <summary>Festival en la plaza durante la segunda mitad de cada estación.</summary>
        public bool IsFestival => SecondsLeft <= secondsPerSeason * 0.5f;

        bool festival;

        void Awake()
        {
            Current = startSeason;
            SecondsLeft = secondsPerSeason;
        }

        void Update()
        {
            SecondsLeft -= Time.deltaTime;
            if (SecondsLeft <= 0f) NextSeason();
            else RefreshFestival();
        }

        /// <summary>Salta al inicio del festival de la estación actual (para probar).</summary>
        [ContextMenu("Start Festival")]
        void StartFestival() => SecondsLeft = secondsPerSeason * 0.5f;

        void RefreshFestival()
        {
            if (festival == IsFestival) return;
            festival = IsFestival;
            FestivalChanged?.Invoke(festival);
        }

        /// <summary>Salta a la siguiente estación y reinicia el contador.</summary>
        [ContextMenu("Next Season")]
        public void NextSeason()
        {
            Current = (Season)(((int)Current + 1) % 4);
            SecondsLeft = secondsPerSeason;
            SeasonChanged?.Invoke(Current);
            RefreshFestival();
        }
    }
}
