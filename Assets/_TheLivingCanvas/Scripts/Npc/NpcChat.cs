using TheLivingCanvas.Interaction;
using TheLivingCanvas.Ui;
using UnityEngine;

namespace TheLivingCanvas.Npcs
{
    /// <summary>
    /// Charla de relleno de los visitantes del museo: al pulsar E cerca, se gira hacia el jugador, se queda quieto y dice sus líneas.
    /// Provisional: el texto real se escribe al final.
    /// </summary>
    [RequireComponent(typeof(NpcRoutine))]
    public class NpcChat : MonoBehaviour, IInteractable, IInteractionPriority
    {
        public InteractionPriority Priority => InteractionPriority.Dialogue;
        [SerializeField] NpcRoutine routine;
        [SerializeField] string displayName = "Visitor";
        [SerializeField] string[] lines = { "This is a nice view." };

        [Tooltip("Si el jugador se aleja más de esto (m), el diálogo se cierra solo.")]
        [SerializeField] float closeDistance = 4f;

        NpcLookAt lookAt;
        bool talking;
        Transform player;

        public string Prompt => $"Talk to {displayName}";
        DialogueBox Box => DialogueBox.Instance;

        public bool CanInteract => Box != null && !Box.IsOpen;

        void Awake()
        {
            if (routine == null) routine = GetComponent<NpcRoutine>();
            lookAt = GetComponent<NpcLookAt>();
        }

        public void Interact(PlayerInteractor interactor)
        {
            var toPlayer = interactor.transform.position - transform.position;
            toPlayer.y = 0f;
            if (toPlayer.sqrMagnitude > 0.0001f) transform.rotation = Quaternion.LookRotation(toPlayer);
            if (Box == null) return;
            talking = true;
            player = interactor.transform;
            routine.Hold = true;
            if (lookAt != null && Camera.main != null) lookAt.LookOverride = Camera.main.transform;
            Box.Open(displayName, lines);
        }

        void Update()
        {
            if (!talking) return;
            if (Box == null || !Box.IsOpen)
            {
                talking = false;
                routine.Hold = false;
                if (lookAt != null) lookAt.LookOverride = null;
                return;
            }
            if (player != null && (player.position - transform.position).sqrMagnitude > closeDistance * closeDistance)
                Box.Close();
        }
    }
}
