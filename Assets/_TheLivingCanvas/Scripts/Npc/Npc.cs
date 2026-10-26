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
    /// <summary>Personaje con el que se puede hablar: se gira hacia el jugador y abre el diálogo con su saludo y gestiona su encargo actual.</summary>
    public class Npc : MonoBehaviour, IInteractable, ISaveable
    {
        [SerializeField] NpcDefinition definition;
        [SerializeField] DialogueUI dialogueUI;
        [SerializeField] CommissionUI commissionUI;
        [Tooltip("Opcional: si está, el personaje sin encargos ofrece comprar pinturas (marchante).")]
        [SerializeField] ArtDealerUI dealerUI;
        [SerializeField] Wallet wallet;
        [SerializeField] ArtistLevel artistLevel;
        [SerializeField] PigmentStock stock;
        [SerializeField] PaintBrushController brush;
        [SerializeField] SeasonClock seasons;
        [Tooltip("Cuerpo del personaje (hijo de la raíz): respira sin tocar el giro hacia el jugador, que mueve la raíz.")]
        [SerializeField] Transform visual;

        // Índice del encargo actual y si ya lo ha pedido.
        int commissionIndex;
        bool requested;

        const float BreathAmplitude = 0.005f; // ±0,5 % de altura: ~1 % de oscilación total
        const float BreathPeriodSeconds = 3.5f;

        float breathPhase;

        void Start() => breathPhase = Random.value * Mathf.PI * 2f; // que no respiren a la vez

        void Update()
        {
            float breath = Mathf.Sin(Time.time * Mathf.PI * 2f / BreathPeriodSeconds + breathPhase);
            visual.localScale = new Vector3(1f, 1f + BreathAmplitude * breath, 1f);
        }

        CommissionDefinition Current => commissionIndex < definition.Commissions.Length ? definition.Commissions[commissionIndex] : null;

        public string Prompt => $"Talk to {definition.DisplayName}";
        public bool CanInteract => !dialogueUI.IsOpen;

        bool talking;
        /// <summary>Hablando con el jugador ahora mismo (la rutina de movimiento se detiene).</summary>
        public bool InConversation
        {
            get
            {
                if (talking && !dialogueUI.IsOpen) talking = false; // el diálogo es global: soltar al cerrarse
                return talking;
            }
        }

        public void Interact(PlayerInteractor interactor)
        {
            talking = true;
            // Solo gira en el eje vertical para no inclinarse hacia la cámara.
            var toPlayer = interactor.transform.position - transform.position;
            toPlayer.y = 0f;
            if (toPlayer.sqrMagnitude > 0.0001f)
                transform.rotation = Quaternion.LookRotation(toPlayer);

            var commission = Current;
            if (commission == null)
            {
                var greeting = WithSeasonLine(definition.GreetingLines);
                if (dealerUI != null)
                    dialogueUI.Open(definition.DisplayName, greeting, "Sell paintings", dealerUI.Open);
                else
                    dialogueUI.Open(definition.DisplayName, greeting);
                return;
            }

            // La primera vez saluda y pide el encargo en un solo diálogo.
            var lines = requested ? commission.RequestLines : definition.GreetingLines.Concat(commission.RequestLines).ToArray();
            requested = true;
            dialogueUI.Open(definition.DisplayName, WithSeasonLine(lines), "Give painting", () => commissionUI.Open(commission, Deliver));
        }

        /// <summary>Antepone la frase de la estación actual (si el personaje tiene una).</summary>
        string[] WithSeasonLine(string[] lines)
        {
            var seasonLines = definition.SeasonLines;
            int index = (int)seasons.Current;
            if (seasonLines == null || index >= seasonLines.Length || string.IsNullOrEmpty(seasonLines[index])) return lines;
            return lines.Prepend(seasonLines[index]).ToArray();
        }

        // Se guarda por el nombre del asset del personaje (hay varios).
        public void WriteSave(SaveData data) =>
            data.npcs.Add(new NpcSave { id = definition.name, commissionIndex = commissionIndex, requested = requested });

        public void ReadSave(SaveData data, SaveRegistry registry)
        {
            var saved = data.npcs.Find(n => n.id == definition.name);
            if (saved == null) return;
            commissionIndex = Mathf.Clamp(saved.commissionIndex, 0, definition.Commissions.Length);
            requested = saved.requested;
        }

        /// <summary>Pintura entregada: paga la recompensa, pasa al siguiente encargo y da las gracias.</summary>
        void Deliver(PaintingItem painting)
        {
            var commission = Current;
            var thanks = commission.ThanksLines.Append(CommissionRewards.Pay(commission, wallet, artistLevel, stock, brush)).ToArray();
            commissionIndex++;
            requested = false;
            dialogueUI.Open(definition.DisplayName, thanks);
        }
    }
}
