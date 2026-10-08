using UnityEngine;
using UnityEngine.InputSystem;

namespace TheLivingCanvas.Core
{
    /// <summary>
    /// Bloquea el cursor para mirar con el ratón. Escape lo libera; clic izquierdo lo vuelve a bloquear.
    /// </summary>
    public class CursorLock : MonoBehaviour
    {
        void Start() => SetLocked(true);

        void Update()
        {
            if (Keyboard.current != null && Keyboard.current.escapeKey.wasPressedThisFrame)
                SetLocked(false);
            else if (Mouse.current != null && Mouse.current.leftButton.wasPressedThisFrame && Cursor.lockState != CursorLockMode.Locked)
                SetLocked(true);
        }

        static void SetLocked(bool locked)
        {
            Cursor.lockState = locked ? CursorLockMode.Locked : CursorLockMode.None;
            Cursor.visible = !locked;
        }
    }
}
