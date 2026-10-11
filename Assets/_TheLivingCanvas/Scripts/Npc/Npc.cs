using System.Collections.Generic;
using System.Linq;
using TheLivingCanvas.Data;
using TheLivingCanvas.Economy;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Painting;
using TheLivingCanvas.Progression;
using UnityEngine;

namespace TheLivingCanvas.Npcs
{
    /// <summary>Personaje con el que se puede hablar: se gira hacia el jugador y abre el diálogo con su saludo y gestiona su encargo actual.</summary>
    public class Npc : MonoBehaviour, IInteractable
    {
        [SerializeField] NpcDefinition definition;
        [SerializeField] DialogueUI dialogueUI;
        [SerializeField] CommissionUI commissionUI;
        [SerializeField] Wallet wallet;
        [SerializeField] ArtistLevel artistLevel;
        [SerializeField] PigmentStock stock;
        [SerializeField] PaintBrushController brush;

        // Sin guardado todavía (fase 18): índice del encargo actual y si ya lo ha pedido.
        int commissionIndex;
        bool requested;

        CommissionDefinition Current => commissionIndex < definition.Commissions.Length ? definition.Commissions[commissionIndex] : null;

        public string Prompt => $"Talk to {definition.DisplayName}";
        public bool CanInteract => !dialogueUI.IsOpen;

        public void Interact(PlayerInteractor interactor)
        {
            // Solo gira en el eje vertical para no inclinarse hacia la cámara.
            var toPlayer = interactor.transform.position - transform.position;
            toPlayer.y = 0f;
            if (toPlayer.sqrMagnitude > 0.0001f)
                transform.rotation = Quaternion.LookRotation(toPlayer);

            var commission = Current;
            if (commission == null)
            {
                dialogueUI.Open(definition.DisplayName, definition.GreetingLines);
                return;
            }

            // La primera vez saluda y pide el encargo en un solo diálogo.
            var lines = requested ? commission.RequestLines : definition.GreetingLines.Concat(commission.RequestLines).ToArray();
            requested = true;
            dialogueUI.Open(definition.DisplayName, lines, "Give painting", () => commissionUI.Open(commission, Deliver));
        }

        /// <summary>Pintura entregada: paga la recompensa, pasa al siguiente encargo y da las gracias.</summary>
        void Deliver(PaintingItem painting)
        {
            var commission = Current;
            var thanks = commission.ThanksLines.Append(PayReward(commission)).ToArray();
            commissionIndex++;
            requested = false;
            dialogueUI.Open(definition.DisplayName, thanks);
        }

        /// <summary>Entrega monedas, XP y pigmento del encargo; devuelve la línea que resume lo recibido.</summary>
        string PayReward(CommissionDefinition commission)
        {
            var parts = new List<string>();
            if (commission.RewardCoins > 0)
            {
                wallet.Add(commission.RewardCoins);
                parts.Add($"+{commission.RewardCoins} coins");
            }
            if (commission.RewardXp > 0)
            {
                parts.Add($"+{commission.RewardXp} XP");
                if (artistLevel.AddXp(commission.RewardXp)) parts.Add("Level up!");
            }
            var pigment = commission.RewardPigment;
            if (pigment != null)
            {
                bool unlocked = brush.AddPigment(pigment); // false si ya estaba en la paleta
                stock.Add(pigment, commission.RewardPigmentAmount);
                parts.Add($"+{commission.RewardPigmentAmount} {pigment.DisplayName}" + (unlocked ? " (new color for your palette!)" : ""));
            }
            return "Reward: " + string.Join(" · ", parts);
        }
    }
}
