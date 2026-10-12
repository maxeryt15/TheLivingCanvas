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

            // Lo primero que toca la mirada (sin contar al propio jugador) decide: una pared delante tapa lo de detrás.
            RaycastHit? nearest = null;
            for (int i = 0; i < count; i++)
            {
                if (hits[i].collider.transform.IsChildOf(transform)) continue;
                // Distancia 0 = los ojos ya están dentro del collider (ej. el volumen de un marco al pegarse a él):
                // solo cuenta si se mira hacia él.
                if (hits[i].distance <= 0f && Vector3.Angle(view.forward, hits[i].collider.bounds.center - view.position) > MaxInsideAngle)
                    continue;
                if (nearest == null || hits[i].distance < nearest.Value.distance)
                    nearest = hits[i];
            }
            if (nearest == null) return null;

            var candidate = nearest.Value.collider.GetComponentInParent<IInteractable>();
            return candidate != null && candidate.CanInteract ? candidate : null;
        }

        void OnDrawGizmosSelected()
        {
            if (view == null) return;
            Gizmos.color = Color.yellow;
            Gizmos.DrawLine(view.position, view.position + view.forward * reach);
        }
    }
}
