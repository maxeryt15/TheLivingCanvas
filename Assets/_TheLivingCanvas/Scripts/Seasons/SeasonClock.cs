using System;
using UnityEngine;

namespace TheLivingCanvas.Seasons
{
    /// <summary>
    /// Reloj y calendario: un día va de las 6:00 am a las 2:30 am del siguiente (1230 min de juego repartidos en
    /// secondsPerDay); 28 días por estación (Spring → Summer → Autumn → Winter → Spring...). Al llegar a las 2:30 se
    /// pasa al día siguiente sin castigo.
    /// </summary>
    public class SeasonClock : MonoBehaviour
    {
        /// <summary>Minutos de juego de un día: de las 6:00 a las 2:30 (20,5 h).</summary>
        public const float MinutesPerDay = 1230f;
        const int DayStartHour = 6;

        [SerializeField] float secondsPerDay = 900f; // placeholder: 15 min reales por día
        [SerializeField] int daysPerSeason = 28;
        [SerializeField] int festivalDay = 24;
        [SerializeField] int marketEvery = 7;
        [SerializeField] Season startSeason = Season.Spring;

        public Season Current { get; private set; }
        /// <summary>Día de la estación, de 1 a DaysPerSeason.</summary>
        public int Day { get; private set; }
        /// <summary>Año, empieza en 1; sube al pasar de Winter a Spring.</summary>
        public int Year { get; private set; }
        /// <summary>Minutos de juego desde las 6:00 (0..1230).</summary>
        public float MinutesOfDay { get; private set; }

        public int DaysPerSeason => daysPerSeason;
        public int FestivalDay => festivalDay;

        public event Action<Season> SeasonChanged;
        public event Action<bool> FestivalChanged;
        /// <summary>Se dispara en cada día nuevo (después de SeasonChanged si también cambia la estación).</summary>
        public event Action<int> DayChanged;

        /// <summary>Festival en la plaza durante un solo día de cada estación.</summary>
        public bool IsFestival => IsFestivalDayNumber(Day);
        public bool IsMarketDay => IsMarketDayNumber(Day);

        public bool IsFestivalDayNumber(int day) => day == festivalDay;
        public bool IsMarketDayNumber(int day) => marketEvery > 0 && day % marketEvery == 0;

        /// <summary>Hora en 12 h, con los minutos de 10 en 10: "9:40 am", "12:00 pm", "1:10 am".</summary>
        public string TimeText
        {
            get
            {
                int total = DayStartHour * 60 + Mathf.FloorToInt(MinutesOfDay);
                int hour24 = (total / 60) % 24;
                int minute = total % 60 / 10 * 10;
                int hour12 = hour24 % 12 == 0 ? 12 : hour24 % 12;
                return $"{hour12}:{minute:00} {(hour24 < 12 ? "am" : "pm")}";
            }
        }

        bool festival;

        void Awake()
        {
            Current = startSeason;
            Day = 1;
            Year = 1;
            MinutesOfDay = 0f;
        }

        void Update()
        {
            MinutesOfDay += Time.deltaTime * MinutesPerDay / secondsPerDay;
            if (MinutesOfDay >= MinutesPerDay) NextDay();
        }

        /// <summary>Pasa al día siguiente a las 6:00 (y a la siguiente estación si era el último día).</summary>
        [ContextMenu("Next Day")]
        public void NextDay()
        {
            MinutesOfDay = 0f;
            Day++;
            if (Day > daysPerSeason)
            {
                Day = 1;
                AdvanceSeason();
            }
            DayChanged?.Invoke(Day);
            RefreshFestival();
        }

        /// <summary>Salta al día 1 de la siguiente estación.</summary>
        [ContextMenu("Next Season")]
        public void NextSeason()
        {
            Day = 1;
            MinutesOfDay = 0f;
            AdvanceSeason();
            DayChanged?.Invoke(Day);
            RefreshFestival();
        }

        /// <summary>Salta al día del festival de la estación actual, a las 6:00 (para probar).</summary>
        [ContextMenu("Start Festival")]
        void StartFestival()
        {
            Day = festivalDay;
            MinutesOfDay = 0f;
            DayChanged?.Invoke(Day);
            RefreshFestival();
        }

        /// <summary>Salta a las 2:00 am para probar el final del día.</summary>
        [ContextMenu("Skip To Night")]
        void SkipToNight() => MinutesOfDay = 1200f;

        void AdvanceSeason()
        {
            Current = (Season)(((int)Current + 1) % 4);
            if (Current == Season.Spring) Year++;
            SeasonChanged?.Invoke(Current);
        }

        void RefreshFestival()
        {
            if (festival == IsFestival) return;
            festival = IsFestival;
            FestivalChanged?.Invoke(festival);
        }
    }
}
