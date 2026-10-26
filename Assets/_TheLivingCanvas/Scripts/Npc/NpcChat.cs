using TheLivingCanvas.Interaction;
using UnityEngine;

namespace TheLivingCanvas.Npcs
{
    /// <summary>
    /// Charla de relleno de los visitantes del museo: al pulsar E cerca, se gira hacia el jugador, se queda quieto y dice sus líneas.
    /// Provisional: el texto real se escribe al final.
    /// </summary>
    [RequireComponent(typeof(NpcRoutine))]
    public class NpcChat : MonoBehaviour, IInteractable
    {
        [SerializeField] DialogueUI dialogueUI;
        [SerializeField] NpcRoutine routine;
        [SerializeField] string displayName = "Visitor";
        [SerializeField] string[] lines = { "This is a nice view." };

        [Tooltip("Si el jugador se aleja más de esto (m), el diálogo se cierra solo.")]
        [SerializeField] float closeDistance = 4f;

        bool talking;
        Transform player;

        public string Prompt => $"Talk to {displayName}";
        public bool CanInteract => !dialogueUI.IsOpen;

        void Awake()
        {
            if (routine == null) routine = GetComponent<NpcRoutine>();
        }

        public void Interact(PlayerInteractor interactor)
        {
            var toPlayer = interactor.transform.position - transform.position;
            toPlayer.y = 0f;
            if (toPlayer.sqrMagnitude > 0.0001f) transform.rotation = Quaternion.LookRotation(toPlayer);
            talking = true;
            player = interactor.transform;
            routine.Hold = true;
            dialogueUI.Open(displayName, lines);
        }

        void Update()
        {
            if (!talking) return;
            if (dialogueUI.IsOpen && player != null && (player.position - transform.position).sqrMagnitude > closeDistance * closeDistance)
                dialogueUI.Close();
            if (!dialogueUI.IsOpen) { talking = false; routine.Hold = false; }
        }
    }
}
