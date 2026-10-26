using UnityEngine;
using UnityEngine.InputSystem;

// Dev only: camara libre para la escena NpcLineup.
// WASD mover, Q/E bajar/subir, Shift rapido, clic derecho mantenido para mirar, rueda cambia la velocidad.
public class NpcLineupFlyCam : MonoBehaviour
{
    public float speed = 3f;
    public float lookSens = 0.15f;
    float yaw, pitch;

    void Start()
    {
        var e = transform.eulerAngles;
        yaw = e.y; pitch = e.x > 180f ? e.x - 360f : e.x;
    }

    void Update()
    {
        var kb = Keyboard.current; var ms = Mouse.current;
        if (kb == null || ms == null) return;

        if (ms.rightButton.isPressed)
        {
            var d = ms.delta.ReadValue() * lookSens;
            yaw += d.x; pitch = Mathf.Clamp(pitch - d.y, -89f, 89f);
            transform.rotation = Quaternion.Euler(pitch, yaw, 0f);
            Cursor.lockState = CursorLockMode.Locked;
        }
        else Cursor.lockState = CursorLockMode.None;

        float scroll = ms.scroll.ReadValue().y;
        if (scroll != 0f) speed = Mathf.Clamp(speed * (scroll > 0 ? 1.2f : 1f / 1.2f), 0.2f, 30f);

        var dir = Vector3.zero;
        if (kb.wKey.isPressed) dir += transform.forward;
        if (kb.sKey.isPressed) dir -= transform.forward;
        if (kb.dKey.isPressed) dir += transform.right;
        if (kb.aKey.isPressed) dir -= transform.right;
        if (kb.eKey.isPressed) dir += Vector3.up;
        if (kb.qKey.isPressed) dir -= Vector3.up;
        float mul = kb.leftShiftKey.isPressed ? 3f : 1f;
        transform.position += dir.normalized * speed * mul * Time.deltaTime;
    }
}
