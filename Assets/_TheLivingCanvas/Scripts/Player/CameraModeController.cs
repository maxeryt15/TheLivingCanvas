using Unity.Cinemachine;
using UnityEngine;
using UnityEngine.InputSystem;

namespace TheLivingCanvas.Player
{
    public enum CameraMode
    {
        ThirdPerson,
        FirstPerson
    }

    /// <summary>
    /// Cámara contextual: tercera persona por defecto y primera persona para acciones
    /// puntuales (pintar, inspeccionar pinturas). Cambia la prioridad entre dos
    /// CinemachineCamera y deja quieto al jugador mientras está en primera persona.
    /// </summary>
    public class CameraModeController : MonoBehaviour
    {
        const int ActivePriority = 10;
        const int InactivePriority = 0;

        [SerializeField] CinemachineCamera thirdPersonCamera;
        [SerializeField] CinemachineCamera firstPersonCamera;
        [SerializeField] PlayerMovement playerMovement;
        [Tooltip("Se oculta en primera persona para que el cuerpo no tape la vista.")]
        [SerializeField] GameObject playerVisuals;
        [Tooltip("Temporal (Fase 1B): alterna la vista para probar. Lo reemplazarán las interacciones.")]
        [SerializeField] InputActionReference debugToggleAction;

        CinemachineInputAxisController thirdPersonInput;
        CinemachineInputAxisController firstPersonInput;
        CinemachinePanTilt firstPersonPanTilt;

        public CameraMode Mode { get; private set; }

        void Awake()
        {
            thirdPersonInput = thirdPersonCamera.GetComponent<CinemachineInputAxisController>();
            firstPersonInput = firstPersonCamera.GetComponent<CinemachineInputAxisController>();
            firstPersonPanTilt = firstPersonCamera.GetComponent<CinemachinePanTilt>();
        }

        void OnEnable()
        {
            if (debugToggleAction == null) return;
            debugToggleAction.action.Enable();
            debugToggleAction.action.performed += OnDebugToggle;
        }

        void OnDisable()
        {
            if (debugToggleAction == null) return;
            debugToggleAction.action.performed -= OnDebugToggle;
        }

        void Start() => SetMode(CameraMode.ThirdPerson);

        void OnDebugToggle(InputAction.CallbackContext _) =>
            SetMode(Mode == CameraMode.ThirdPerson ? CameraMode.FirstPerson : CameraMode.ThirdPerson);

        public void SetMode(CameraMode mode)
        {
            Mode = mode;
            bool firstPerson = mode == CameraMode.FirstPerson;

            if (firstPerson)
            {
                // Empieza mirando hacia donde mira el jugador.
                firstPersonPanTilt.PanAxis.Value = playerMovement.transform.eulerAngles.y;
                firstPersonPanTilt.TiltAxis.Value = 0f;
            }

            firstPersonCamera.Priority = firstPerson ? ActivePriority : InactivePriority;
            thirdPersonCamera.Priority = firstPerson ? InactivePriority : ActivePriority;

            // Solo la cámara activa lee el ratón/stick.
            firstPersonInput.enabled = firstPerson;
            thirdPersonInput.enabled = !firstPerson;

            playerMovement.enabled = !firstPerson;
            playerVisuals.SetActive(!firstPerson);
        }
    }
}
