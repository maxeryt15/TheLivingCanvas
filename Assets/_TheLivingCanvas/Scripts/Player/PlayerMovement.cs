using TheLivingCanvas.Save;
using UnityEngine;
using UnityEngine.InputSystem;

namespace TheLivingCanvas.Player
{
    /// <summary>
    /// Movimiento en tercera persona relativo a la cámara: caminar, correr, girar hacia
    /// la dirección de movimiento y gravedad.
    /// </summary>
    [RequireComponent(typeof(CharacterController))]
    public class PlayerMovement : MonoBehaviour, ISaveable
    {
        [SerializeField] InputActionReference moveAction;
        [SerializeField] InputActionReference sprintAction;
        [Tooltip("Cámara de referencia para la dirección. Si está vacío se usa Camera.main.")]
        [SerializeField] Transform cameraTransform;

        [SerializeField] float walkSpeed = 3f;
        [SerializeField] float sprintSpeed = 5.5f;
        [Tooltip("Grados por segundo.")]
        [SerializeField] float turnSpeed = 720f;
        [SerializeField] float gravity = -20f;

        CharacterController controller;
        float verticalVelocity;

        void Awake()
        {
            controller = GetComponent<CharacterController>();
            if (cameraTransform == null && Camera.main != null)
                cameraTransform = Camera.main.transform;
        }

        void OnEnable()
        {
            moveAction.action.Enable();
            sprintAction.action.Enable();
        }

        void Update()
        {
            Vector2 input = moveAction.action.ReadValue<Vector2>();
            Vector3 move = Vector3.zero;

            if (input.sqrMagnitude > 0.01f)
            {
                Vector3 forward = Vector3.ProjectOnPlane(cameraTransform.forward, Vector3.up).normalized;
                Vector3 right = Vector3.Cross(Vector3.up, forward);
                move = Vector3.ClampMagnitude(forward * input.y + right * input.x, 1f);

                Quaternion targetRotation = Quaternion.LookRotation(move);
                transform.rotation = Quaternion.RotateTowards(transform.rotation, targetRotation, turnSpeed * Time.deltaTime);
            }

            if (controller.isGrounded && verticalVelocity < 0f)
                verticalVelocity = -2f; // mantiene al jugador pegado al suelo
            verticalVelocity += gravity * Time.deltaTime;

            float speed = sprintAction.action.IsPressed() ? sprintSpeed : walkSpeed;
            controller.Move((move * speed + Vector3.up * verticalVelocity) * Time.deltaTime);
        }

        public void WriteSave(SaveData data)
        {
            data.playerPosition = transform.position;
            data.playerYaw = transform.eulerAngles.y;
        }

        public void ReadSave(SaveData data, SaveRegistry registry)
        {
            controller.enabled = false; // si no, el CharacterController revierte el teletransporte
            transform.SetPositionAndRotation(data.playerPosition, Quaternion.Euler(0f, data.playerYaw, 0f));
            controller.enabled = true;
            verticalVelocity = 0f;
        }
    }
}
