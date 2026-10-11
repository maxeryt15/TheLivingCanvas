using System.Linq;
using TheLivingCanvas.Data;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using UnityEngine;

namespace TheLivingCanvas.Npcs
{
    /// <summary>Personaje con el que se puede hablar: se gira hacia el jugador y abre el diálogo con su saludo y gestiona su encargo actual.</summary>
    public class Npc : MonoBehaviour, IInteractable
    {
        [SerializeField] NpcDefinition definition;
        [SerializeField] DialogueUI dialogueUI;
        [SerializeField] CommissionUI commissionUI;

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

        /// <summary>Pintura entregada: pasa al siguiente encargo y da las gracias.</summary>
        void Deliver(PaintingItem painting)
        {
            var thanks = Current.ThanksLines;
            commissionIndex++;
            requested = false;
            dialogueUI.Open(definition.DisplayName, thanks);
        }
    }
}
