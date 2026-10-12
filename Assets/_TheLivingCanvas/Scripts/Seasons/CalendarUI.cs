using System.Collections.Generic;
using System.Linq;
using TheLivingCanvas.Core;
using TheLivingCanvas.Growth;
using TheLivingCanvas.Painting;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace TheLivingCanvas.Seasons
{
    /// <summary>
    /// Calendario (C / cruceta arriba o la pared del estudio): cuadrícula de 7 columnas con los días de una estación,
    /// que se puede hojear con los botones; marca hoy, atenúa los días pasados y tiñe festival y mercado.
    /// </summary>
    public class CalendarUI : ModalPanel
    {
        [SerializeField] SeasonClock clock;
        [SerializeField] InputActionReference toggleAction;
        [SerializeField] PaintModeController paintMode;
        [SerializeField] PaintingPlacer placer;
        [SerializeField] Text titleLabel;
        [SerializeField] Text footerLabel;
        [SerializeField] Button prevButton;
        [SerializeField] Button nextButton;
        [SerializeField] RectTransform cellContainer;
        [Tooltip("Celda desactivada que se clona por día (Image + Outline, Text 'Number' y Text 'Events').")]
        [SerializeField] GameObject cellTemplate;

        // Paleta placeholder (marrones y crema del resto de la UI).
        static readonly Color NormalColor = new Color(0.93f, 0.88f, 0.78f);
        static readonly Color FestivalColor = new Color(0.94f, 0.66f, 0.42f);
        static readonly Color MarketColor = new Color(0.82f, 0.78f, 0.50f);
        static readonly Color PastBlend = new Color(0.30f, 0.20f, 0.13f);
        static readonly Color TodayOutline = new Color(1f, 0.82f, 0.2f);

        struct Cell
        {
            public Image image;
            public Outline outline;
            public Text number;
            public Text events;
        }

        readonly List<Cell> cells = new();
        Season shown;

        protected override void Awake()
        {
            base.Awake();
            cellTemplate.SetActive(false);
            for (int day = 1; day <= clock.DaysPerSeason; day++)
            {
                var go = Instantiate(cellTemplate, cellContainer);
                go.SetActive(true);
                go.name = $"Day_{day}";
                cells.Add(new Cell
                {
                    image = go.GetComponent<Image>(),
                    outline = go.GetComponent<Outline>(),
                    number = go.transform.Find("Number").GetComponent<Text>(),
                    events = go.transform.Find("Events").GetComponent<Text>()
                });
            }
            prevButton.onClick.AddListener(() => Browse(-1));
            nextButton.onClick.AddListener(() => Browse(1));
        }

        protected override void OnEnable()
        {
            base.OnEnable();
            toggleAction.action.Enable();
            toggleAction.action.performed += OnToggle;
            clock.DayChanged += OnDayChanged;
        }

        protected override void OnDisable()
        {
            base.OnDisable();
            toggleAction.action.performed -= OnToggle;
            clock.DayChanged -= OnDayChanged;
        }

        void OnToggle(InputAction.CallbackContext _)
        {
            if (IsOpen) Close();
            else if (!paintMode.IsPainting && !placer.IsPlacing) Open(); // TryOpen ya descarta otro panel con el cursor
        }

        /// <summary>Abre el calendario en la estación actual.</summary>
        public void Open()
        {
            if (!TryOpen()) return;
            shown = clock.Current;
            Refresh();
        }

        void OnDayChanged(int day)
        {
            if (IsOpen) Refresh();
        }

        void Browse(int step)
        {
            shown = (Season)(((int)shown + step + 4) % 4);
            Refresh();
        }

        void Refresh()
        {
            // Se hojea hacia delante: una estación anterior a la actual es la del año que viene.
            int year = (int)shown < (int)clock.Current ? clock.Year + 1 : clock.Year;
            titleLabel.text = $"{shown}  ·  Year {year}";
            bool isCurrent = shown == clock.Current;

            for (int i = 0; i < cells.Count; i++)
            {
                int day = i + 1;
                var cell = cells[i];
                bool today = isCurrent && day == clock.Day;
                bool past = isCurrent && day < clock.Day;

                var color = clock.IsFestivalDayNumber(day) ? FestivalColor : clock.IsMarketDayNumber(day) ? MarketColor : NormalColor;
                cell.image.color = past ? Color.Lerp(color, PastBlend, 0.45f) : color;
                cell.outline.enabled = today;
                cell.outline.effectColor = TodayOutline;
                cell.number.text = day.ToString();
                cell.number.color = past ? new Color(0.25f, 0.17f, 0.1f, 0.55f) : new Color(0.25f, 0.17f, 0.1f);
                cell.events.text = string.Join("\n", CalendarEvents.For(clock, shown, day).Take(2));
            }
            footerLabel.text = NextEventText();
        }

        /// <summary>
        /// Busca hacia delante (cruzando estaciones) el primer día con un evento que no sea el mercado (este se ve
        /// cada semana en la cuadrícula); si hoy hay mercado lo dice antes.
        /// </summary>
        string NextEventText()
        {
            string prefix = clock.IsMarketDay ? $"Today: {CalendarEvents.MarketLabel}   " : string.Empty;
            return prefix + NextBigEventText();
        }

        string NextBigEventText()
        {
            var season = clock.Current;
            int day = clock.Day;
            int limit = clock.DaysPerSeason * 4;
            for (int offset = 1; offset <= limit; offset++)
            {
                if (++day > clock.DaysPerSeason)
                {
                    day = 1;
                    season = (Season)(((int)season + 1) % 4);
                }
                var label = CalendarEvents.For(clock, season, day).FirstOrDefault(e => e != CalendarEvents.MarketLabel);
                if (label != null) return $"Next: {label} in {offset} {(offset == 1 ? "day" : "days")}";
            }
            return string.Empty;
        }
    }
}
