using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace TheLivingCanvas.Interaction
{
    /// <summary>
    /// Muestra la mira en el centro de la pantalla y "[E] Acción" mientras haya un interactuable seleccionado.
    /// UI provisional: el diseño final llegará con la dirección de arte.
    /// </summary>
    public class InteractionPromptUI : MonoBehaviour
    {
        [SerializeField] PlayerInteractor interactor;
        [SerializeField] GameObject panel;
        [SerializeField] Text label;
        [Tooltip("Punto en el centro; se oculta cuando no se puede interactuar (pintando, con un panel abierto...).")]
        [SerializeField] Image reticle;
        [SerializeField] Color reticleIdle = new(1f, 0.97f, 0.9f, 0.55f);
        [SerializeField] Color reticleActive = new(1f, 0.85f, 0.45f, 1f);
        [Tooltip("Escala de la mira al apuntar a algo interactuable.")]
        [SerializeField] float activeScale = 1.6f;

        void Update()
        {
            bool aiming = interactor.isActiveAndEnabled;
            var current = aiming ? interactor.Current : null;
            panel.SetActive(current != null);

            // Con el cursor libre (inventario abierto, Esc) la mira no sirve.
            reticle.enabled = aiming && Cursor.lockState == CursorLockMode.Locked;
            reticle.color = current != null ? reticleActive : reticleIdle;
            reticle.rectTransform.localScale = Vector3.one * (current != null ? activeScale : 1f);
            if (current == null) return;

            // Muestra la tecla del esquema teclado/ratón (ej. "E"). El mando llegará con la UI final.
            string key = interactor.InteractAction.action.GetBindingDisplayString(group: "Keyboard&Mouse");
            label.text = $"[{key}]  {current.Prompt}";
        }
    }
}
