using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace TheLivingCanvas.Interaction
{
    /// <summary>
    /// Muestra "[E] Acción" mientras haya un interactuable seleccionado.
    /// UI provisional: el diseño final llegará con la dirección de arte.
    /// </summary>
    public class InteractionPromptUI : MonoBehaviour
    {
        [SerializeField] PlayerInteractor interactor;
        [SerializeField] GameObject panel;
        [SerializeField] Text label;

        void Update()
        {
            var current = interactor.isActiveAndEnabled ? interactor.Current : null;
            panel.SetActive(current != null);
            if (current == null) return;

            // Muestra la tecla del esquema teclado/ratón (ej. "E"). El mando llegará con la UI final.
            string key = interactor.InteractAction.action.GetBindingDisplayString(group: "Keyboard&Mouse");
            label.text = $"[{key}]  {current.Prompt}";
        }
    }
}
