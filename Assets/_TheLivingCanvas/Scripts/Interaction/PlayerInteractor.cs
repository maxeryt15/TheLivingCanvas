using UnityEngine;
using UnityEngine.InputSystem;

namespace TheLivingCanvas.Interaction
{
    /// <summary>
    /// Elige el interactuable al que apunta la mirada (centro de la pantalla, en primera persona)
    /// y lo activa con la acción Interact.
    /// </summary>
    public class PlayerInteractor : MonoBehaviour
    {
        const float MaxInsideAngle = 35f;

        [SerializeField] InputActionReference interactAction;
        [Tooltip("Origen y dirección de la mirada. Si está vacío se usa Camera.main.")]
        [SerializeField] Transform view;
        [Tooltip("Distancia máxima desde los ojos.")]
        [SerializeField] float reach = 2.8f;
        [Tooltip("Grosor del rayo de la mirada: perdona apuntar un poco al lado de objetos pequeños.")]
        [SerializeField] float aimRadius = 0.12f;

        readonly RaycastHit[] hits = new RaycastHit[16];

        /// <summary>Interactuable seleccionado ahora mismo, o null.</summary>
        public IInteractable Current { get; private set; }

        public InputActionReference InteractAction => interactAction;

        void Awake()
        {
            if (view == null && Camera.main != null)
                view = Camera.main.transform;
        }

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

        void Update() => Current = FindAimed();

        void OnInteract(InputAction.CallbackContext _) => Current?.Interact(this);

        IInteractable FindAimed()
        {
            int count = Physics.SphereCastNonAlloc(view.position, aimRadius, view.forward, hits, reach, ~0, QueryTriggerInteraction.Collide);

            // Se recorren los impactos de cerca a lejos: los interactuables disponibles son candidatos y lo primero
            // que no lo es (una pared, un interactuable desactivado) tapa lo que hay detrás.
            // Entre los candidatos gana el de mayor prioridad; a igualdad, el más cercano.
            System.Array.Sort(hits, 0, count, DistanceComparer);
            IInteractable best = null;
            var bestPriority = int.MinValue;
            for (int i = 0; i < count; i++)
            {
                if (hits[i].collider.transform.IsChildOf(transform)) continue;
                // Distancia 0 = los ojos ya están dentro del collider (ej. el volumen de un marco al pegarse a él):
                // solo cuenta si se mira hacia él.
                if (hits[i].distance <= 0f && Vector3.Angle(view.forward, hits[i].collider.bounds.center - view.position) > MaxInsideAngle)
                    continue;

                var candidate = hits[i].collider.GetComponentInParent<IInteractable>();
                if (candidate == null || !candidate.CanInteract) break;
                int priority = PriorityOf(candidate);
                if (priority > bestPriority) { best = candidate; bestPriority = priority; }
            }
            return best;
        }

        static readonly System.Collections.Generic.IComparer<RaycastHit> DistanceComparer =
            System.Collections.Generic.Comparer<RaycastHit>.Create((a, b) => a.distance.CompareTo(b.distance));

        public static int PriorityOf(IInteractable i) =>
            (int)(i is IInteractionPriority p ? p.Priority : InteractionPriority.Examine);

        void OnDrawGizmosSelected()
        {
            if (view == null) return;
            Gizmos.color = Color.yellow;
            Gizmos.DrawLine(view.position, view.position + view.forward * reach);
        }
    }
}
