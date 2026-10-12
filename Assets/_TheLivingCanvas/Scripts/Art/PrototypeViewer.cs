using UnityEngine;
using UnityEngine.InputSystem;

namespace TheLivingCanvas.Art
{
    /// <summary>
    /// Visor del prototipo artístico: cámara libre y tecla F para alternar normal / Descoloración.
    /// RMB + ratón = mirar, WASD = mover, Q/E = bajar/subir, Shift = rápido. No es parte del juego.
    /// </summary>
    public class PrototypeViewer : MonoBehaviour
    {
        public PainterlyDescolor descolor;
        public float moveSpeed = 1.6f;
        public float lookSpeed = 0.12f;

        float _yaw, _pitch;

        void Start()
        {
            var e = transform.eulerAngles;
            _yaw = e.y;
            _pitch = e.x > 180f ? e.x - 360f : e.x;
        }

        void Update()
        {
            var kb = Keyboard.current;
            var mouse = Mouse.current;
            if (kb == null) return;

            if (kb.fKey.wasPressedThisFrame && descolor != null) descolor.Toggle();

            if (mouse != null && mouse.rightButton.isPressed)
            {
                var d = mouse.delta.ReadValue();
                _yaw += d.x * lookSpeed;
                _pitch = Mathf.Clamp(_pitch - d.y * lookSpeed, -80f, 80f);
                transform.rotation = Quaternion.Euler(_pitch, _yaw, 0f);
            }

            var dir = Vector3.zero;
            if (kb.wKey.isPressed) dir += Vector3.forward;
            if (kb.sKey.isPressed) dir += Vector3.back;
            if (kb.dKey.isPressed) dir += Vector3.right;
            if (kb.aKey.isPressed) dir += Vector3.left;
            if (kb.eKey.isPressed) dir += Vector3.up;
            if (kb.qKey.isPressed) dir += Vector3.down;
            var speed = moveSpeed * (kb.leftShiftKey.isPressed ? 3f : 1f);
            transform.position += transform.rotation * dir * (speed * Time.deltaTime);
        }

        void OnGUI()
        {
            GUI.Label(new Rect(12, 8, 600, 24), "F: toggle Descoloration   |   RMB + mouse: look   |   WASD / Q E: move");
        }
    }
}
