using System.Collections.Generic;

namespace TheLivingCanvas.Seasons
{
    /// <summary>Eventos del calendario (solo código): etiquetas cortas en inglés para un día de una estación.</summary>
    public static class CalendarEvents
    {
        public const string MarketLabel = "Pigment Market";

        public static IEnumerable<string> For(SeasonClock clock, Season season, int day)
        {
            if (day == 1) yield return $"First day of {season}";
            if (day == clock.DaysPerSeason) yield return $"Last day of {season}";
            if (clock.IsFestivalDayNumber(day)) yield return $"{season} Festival";
            if (clock.IsMarketDayNumber(day)) yield return MarketLabel;
        }
    }
}
