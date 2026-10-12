using System.Linq;
using TheLivingCanvas.Data;
using TheLivingCanvas.Economy;
using TheLivingCanvas.Interaction;
using TheLivingCanvas.Inventory;
using TheLivingCanvas.Painting;
using TheLivingCanvas.Progression;
using TheLivingCanvas.Save;
using UnityEngine;

namespace TheLivingCanvas.Npcs
{
    /// <summary>Tablón de encargos del pueblo: ofrece los encargos de los vecinos uno a uno, en orden.</summary>
    public class CommissionBoard : MonoBehaviour, IInteractable, ISaveable
    {
        [SerializeField] CommissionDefinition[] commissions;
        [SerializeField] DialogueUI dialogueUI;
        [SerializeField] CommissionUI commissionUI;
        [SerializeField] Wallet wallet;
        [SerializeField] ArtistLevel artistLevel;
        [SerializeField] PigmentStock stock;
        [SerializeField] PaintBrushController brush;
        [Tooltip("Notas de papel visibles: se quitan a medida que se cumplen los encargos.")]
        [SerializeField] GameObject[] notes;

        const string Speaker = "Notice board";

        // Índice del encargo actual.
        int commissionIndex;

        CommissionDefinition Current => commissionIndex < commissions.Length ? commissions[commissionIndex] : null;

        public string Prompt => "Read the notice board";
        public bool CanInteract => !dialogueUI.IsOpen;

        void Awake() => RefreshNotes();

        public void Interact(PlayerInteractor interactor)
        {
            var commission = Current;
            if (commission == null)
            {
                dialogueUI.Open(Speaker, new[] { "The board is empty for now. Check back another day." });
                return;
            }
            dialogueUI.Open(Speaker, commission.RequestLines, "Give painting", () => commissionUI.Open(commission, Deliver));
        }

        /// <summary>Pintura entregada: paga la recompensa, pasa al siguiente encargo y deja la nota de gracias.</summary>
        void Deliver(PaintingItem painting)
        {
            var commission = Current;
            var thanks = commission.ThanksLines.Append(CommissionRewards.Pay(commission, wallet, artistLevel, stock, brush)).ToArray();
            commissionIndex++;
            RefreshNotes();
            dialogueUI.Open(Speaker, thanks);
        }

        public void WriteSave(SaveData data) => data.boardCommissionIndex = commissionIndex;

        public void ReadSave(SaveData data, SaveRegistry registry)
        {
            commissionIndex = Mathf.Clamp(data.boardCommissionIndex, 0, commissions.Length);
            RefreshNotes();
        }

        /// <summary>Deja tantas notas como encargos quedan (máximo las que hay).</summary>
        void RefreshNotes()
        {
            int visible = Mathf.Min(commissions.Length - commissionIndex, notes.Length);
            for (int i = 0; i < notes.Length; i++)
                notes[i].SetActive(i < visible);
        }
    }
}
