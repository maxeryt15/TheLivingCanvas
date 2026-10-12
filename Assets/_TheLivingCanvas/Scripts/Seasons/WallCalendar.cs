using TheLivingCanvas.Interaction;
using UnityEngine;
using UnityEngine.UI;

namespace TheLivingCanvas.Seasons
{
    /// <summary>Calendario de pared del estudio: muestra la fecha y, al interactuar, abre el calendario.</summary>
    public class WallCalendar : MonoBehaviour, IInteractable
    {
        [SerializeField] CalendarUI calendarUI;
        [SerializeField] SeasonClock clock;
        [SerializeField] Text label;

        public string Prompt => "Check calendar";
        public bool CanInteract => !calendarUI.IsOpen;

        void OnEnable()
        {
            clock.DayChanged += OnDayChanged;
            Refresh();
        }

        void OnDisable() => clock.DayChanged -= OnDayChanged;

        void Start() => Refresh(); // por si el reloj aún no había hecho su Awake en OnEnable

        public void Interact(PlayerInteractor interactor) => calendarUI.Open();

        void OnDayChanged(int day) => Refresh();

        void Refresh() => label.text = $"{clock.Current} {clock.Day}";
    }
}
