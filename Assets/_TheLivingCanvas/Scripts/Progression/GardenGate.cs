using System.Collections;
using TheLivingCanvas.Interaction;
using UnityEngine;

namespace TheLivingCanvas.Progression
{
    /// <summary>
    /// Puerta del jardín: bloquea el hueco entre el estudio y el jardín hasta que el jugador
    /// alcanza el nivel pedido; entonces la hoja se abre y el collider deja de bloquear.
    /// </summary>
    public class GardenGate : MonoBehaviour, IInteractable
    {
        [SerializeField] ArtistLevel artistLevel;
        [SerializeField] int requiredLevel = 4;
        [Tooltip("Collider sólido que cierra el hueco mientras la puerta está cerrada.")]
        [SerializeField] Collider blocker;
        [Tooltip("Pivote en la bisagra: se gira para abrir la hoja.")]
        [SerializeField] Transform hinge;
        [SerializeField] float openAngle = 90f;
        [SerializeField] float openSeconds = 0.6f;

        bool open;

        // Mientras está cerrada se puede interactuar solo para que el jugador vea el aviso.
        public string Prompt => $"Garden — opens at level {requiredLevel}";
        public bool CanInteract => !open;

        void OnEnable() => artistLevel.LeveledUp += OnLeveledUp;
        void OnDisable() => artistLevel.LeveledUp -= OnLeveledUp;

        void Start()
        {
            // Por si el nivel ya alcanza (p. ej. al cargar partida): se abre sin animación.
            if (artistLevel.Level >= requiredLevel) Open(animate: false);
        }

        public void Interact(PlayerInteractor interactor) { }

        void OnLeveledUp(int level)
        {
            if (level >= requiredLevel) Open(animate: true);
        }

        void Open(bool animate)
        {
            if (open) return;
            open = true;
            blocker.enabled = false;
            var target = Quaternion.Euler(0f, openAngle, 0f);
            if (animate) StartCoroutine(Swing(target));
            else hinge.localRotation = target;
        }

        IEnumerator Swing(Quaternion target)
        {
            var start = hinge.localRotation;
            for (float t = 0f; t < openSeconds; t += Time.deltaTime)
            {
                hinge.localRotation = Quaternion.Slerp(start, target, t / openSeconds);
                yield return null;
            }
            hinge.localRotation = target;
        }
    }
}
