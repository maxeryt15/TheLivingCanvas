using UnityEngine;
using UnityEngine.InputSystem;

namespace TheLivingCanvas.Interaction
{
    /// <summary>
    /// Elige el interactuable más cercano delante del jugador y lo activa con la acción Interact.
    /// </summary>
    public class PlayerInteractor : MonoBehaviour
    {
        [SerializeField] InputActionReference interactAction;
        [Tooltip("Altura desde los pies desde la que se busca (aprox. el pecho).")]
        [SerializeField] float probeHeight = 1f;
        [SerializeField] float reach = 1.5f;
        [Tooltip("Ángulo máximo respecto al frente del jugador.")]
        [SerializeField] float maxAngle = 75f;

        readonly Collider[] hits = new Collider[16];

        /// <summary>Interactuable seleccionado ahora mismo, o null.</summary>
        public IInteractable Current { get; private set; }

        public InputActionReference InteractAction => interactAction;

        void OnEnable()
        {
            interactAction.action.Enable();
            interactAction.action.performed += OnInteract;
        }

        void OnDisable()
        {
            interactAction.action.performed -= OnInteract;
            Current = null;
        }

        void Update() => Current = FindBest();

        void OnInteract(InputAction.CallbackContext _) => Current?.Interact(this);

        IInteractable FindBest()
        {
            Vector3 origin = transform.position + Vector3.up * probeHeight;
            int count = Physics.OverlapSphereNonAlloc(origin, reach, hits, ~0, QueryTriggerInteraction.Collide);

            IInteractable best = null;
            float bestScore = float.MaxValue;
            for (int i = 0; i < count; i++)
            {
                var candidate = hits[i].GetComponentInParent<IInteractable>();
                if (candidate == null || !candidate.CanInteract) continue;

                Vector3 toTarget = hits[i].bounds.center - origin;
                Vector3 flat = Vector3.ProjectOnPlane(toTarget, Vector3.up);
                float angle = flat.sqrMagnitude > 0.0001f ? Vector3.Angle(transform.forward, flat) : 0f;
                if (angle > maxAngle) continue;

                // Prioriza lo cercano y, a igual distancia, lo que está más de frente.
                float score = toTarget.magnitude + angle / maxAngle;
                if (score < bestScore)
                {
                    bestScore = score;
                    best = candidate;
                }
            }
            return best;
        }

        void OnDrawGizmosSelected()
        {
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(transform.position + Vector3.up * probeHeight, reach);
        }
    }
}
