using UnityEngine;
using UnityEngine.InputSystem;

namespace TheLivingCanvas.Core
{
    /// <summary>
    /// Bloquea el cursor para mirar con el ratón. Si el cursor queda libre (ej. al pulsar Alt+Tab), un clic izquierdo lo vuelve a bloquear.
    /// En PointerMode (ej. pintando) el cursor queda libre y visible.
    /// </summary>
    public class CursorLock : MonoBehaviour
    {
        bool pointerMode;
        int pointerModeChangedFrame = -1;

        public bool PointerMode
        {
            get => pointerMode;
            set
            {
                pointerMode = value;
                pointerModeChangedFrame = Time.frameCount;
                SetLocked(!value);
            }
        }

        void Start() => SetLocked(true);

        void Update()
        {
            // El clic que cierra un panel (o sale del modo pintura) no debe bloquear el cursor en ese mismo frame.
            if (pointerMode || Time.frameCount == pointerModeChangedFrame) return;

            if (Mouse.current != null && Mouse.current.leftButton.wasPressedThisFrame && Cursor.lockState != CursorLockMode.Locked)
                SetLocked(true);
        }

        static void SetLocked(bool locked)
        {
            Cursor.lockState = locked ? CursorLockMode.Locked : CursorLockMode.None;
            Cursor.visible = !locked;
        }
    }
}
