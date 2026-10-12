using System.Linq;
using TheLivingCanvas.Data;
using TheLivingCanvas.Economy;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Painting;
using TheLivingCanvas.Progression;
using TheLivingCanvas.Save;
using TheLivingCanvas.Seasons;
using UnityEngine;

namespace TheLivingCanvas.Npcs
{
    /// <summary>
    /// Puesto del juez del festival en la plaza: el concurso de la estación se gana una vez y deja un trofeo en la galería.
    /// El objeto raíz siempre está activo; el puesto y los banderines solo se ven mientras dura el festival.
    /// </summary>
    public class FestivalStand : MonoBehaviour, IInteractable, ISaveable
    {
        [SerializeField] SeasonClock clock;
        [Tooltip("Un concurso por estación, en el orden del enum Season.")]
        [SerializeField] CommissionDefinition[] contests;
        [Tooltip("Un trofeo por estación en la galería, en el orden del enum Season; ocultos hasta ganar.")]
        [SerializeField] GameObject[] trophies;
        [Tooltip("Puesto, banderines y collider: solo activos durante el festival.")]
        [SerializeField] GameObject[] festivalVisuals;
        [SerializeField] DialogueUI dialogueUI;
        [SerializeField] CommissionUI commissionUI;
        [SerializeField] Wallet wallet;
        [SerializeField] ArtistLevel artistLevel;
        [SerializeField] PigmentStock stock;
        [SerializeField] PaintBrushController brush;

        const string Speaker = "Festival judge";

        // Estaciones cuyo concurso ya se ganó.
        readonly bool[] won = new bool[4];

        public string Prompt => "Talk to the festival judge";
        public bool CanInteract => clock.IsFestival && !dialogueUI.IsOpen;

        void OnEnable() => clock.FestivalChanged += SetFestival;

        void OnDisable() => clock.FestivalChanged -= SetFestival;

        void Start()
        {
            SetFestival(clock.IsFestival);
            for (int i = 0; i < trophies.Length; i++)
                trophies[i].SetActive(won[i]);
        }

        void SetFestival(bool active)
        {
            foreach (var visual in festivalVisuals)
                visual.SetActive(active);
        }

        public void Interact(PlayerInteractor interactor)
        {
            int season = (int)clock.Current;
            if (won[season])
            {
                dialogueUI.Open(Speaker, new[] { "You already won this season's ribbon. Come back next festival!" });
                return;
            }
            var contest = contests[season];
            dialogueUI.Open(Speaker, contest.RequestLines, "Enter painting", () => commissionUI.Open(contest, Deliver));
        }

        public void WriteSave(SaveData data) => data.festivalWon = won.ToList();

        public void ReadSave(SaveData data, SaveRegistry registry)
        {
            for (int i = 0; i < won.Length; i++)
            {
                won[i] = i < data.festivalWon.Count && data.festivalWon[i];
                trophies[i].SetActive(won[i]);
            }
        }

        /// <summary>Pintura inscrita: paga el premio, marca la estación como ganada y enseña su trofeo.</summary>
        void Deliver(PaintingItem painting)
        {
            int season = (int)clock.Current;
            var contest = contests[season];
            var thanks = contest.ThanksLines.Append(CommissionRewards.Pay(contest, wallet, artistLevel, stock, brush)).ToArray();
            won[season] = true;
            trophies[season].SetActive(true);
            dialogueUI.Open(Speaker, thanks);
        }
    }
}
